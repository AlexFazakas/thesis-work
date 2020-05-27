#!/usr/bin/env python3

import subprocess
import pyinotify
import os
import json
import time
import requests
import sys
from collections import UserDict
import base64
import zlib
import pprint


wm = pyinotify.WatchManager()

mask = pyinotify.IN_CREATE
API = ''


class ProblemReport(UserDict):
    def __init__(self, type='Crash', date=None):
        '''Initialize a fresh problem report.

        type can be 'Crash', 'Packaging', 'KernelCrash' or 'KernelOops'.
        date is the desired date/time string; if None (default), the
        current local time is used.
        '''
        if date is None:
            date = time.asctime()
        self.data = {'ProblemType': type, 'Date': date}

        # keeps track of keys which were added since the last ctor or load()
        self.old_keys = set()

    def load(self, file, binary=True, key_filter=None):
        '''Initialize problem report from a file-like object.

        If binary is False, binary data is not loaded; the dictionary key is
        created, but its value will be an empty string. If it is True, it is
        transparently uncompressed and available as dictionary byte array values.
        If binary is 'compressed', the compressed value is retained, and the
        dictionary value will be a CompressedValue object. This is useful if
        the compressed value is still useful (to avoid recompression if the
        file needs to be written back).

        file needs to be opened in binary mode.

        If key_filter is given, only those keys will be loaded.

        Files are in RFC822 format, but with case sensitive keys.
        '''
        self._assert_bin_mode(file)
        self.data.clear()
        key = None
        value = None
        b64_block = False
        bd = None
        if key_filter:
            remaining_keys = set(key_filter)
        else:
            remaining_keys = None
        for line in file:
            if line.startswith(b' '):
                if b64_block and not binary:
                    continue
                assert (key is not None and value is not None)
                if b64_block:
                    block = line
                    if bd:
                        value += block
                    else:
                        if binary == 'compressed':
                            if value.gzipvalue == b'' and not block.startswith(b'\037\213\010'):
                                value.legacy_zlib = True
                            value.gzipvalue += block
                        else:
                            if block.startswith(b'\037\213\010'):
                                bd = zlib.decompressobj(-zlib.MAX_WBITS)
                                value = block
                            else:
                                bd = zlib.decompressobj()
                                value += block
                else:
                    if len(value) > 0:
                        value += b'\n'
                    if line.endswith(b'\n'):
                        value += line[1:-1]
                    else:
                        value += line[1:]
            else:
                if b64_block:
                    if bd:
                        value += bd.flush()
                    b64_block = False
                    bd = None
                if key:
                    assert value is not None
                    if remaining_keys is not None:
                        try:
                            remaining_keys.remove(key)
                            self.data[key] = self._try_unicode(value)
                            if not remaining_keys:
                                key = None
                                break
                        except KeyError:
                            pass
                    else:
                        self.data[key] = self._try_unicode(value)
                (key, value) = line.split(b':', 1)
                key = key.decode('ASCII')
                value = value.strip()
                if value == b'base64':
                    if binary == 'compressed':
                        value = CompressedValue(key.encode())
                        value.gzipvalue = b''
                    else:
                        value = b''
                    b64_block = True

        if key is not None:
            # self.data[key] = self._try_unicode(value)
            self.data[key] = value

        self.old_keys = set(self.data.keys())

    @classmethod
    def _is_binary(klass, string):
        '''Check if the given strings contains binary data.'''

        if type(string) == bytes:
            for c in string:
                if c < 32 and not chr(c).isspace():
                    return True
        return False

    @classmethod
    def _try_unicode(klass, value):
        '''Try to convert bytearray value to unicode'''

        if type(value) == bytes and not klass._is_binary(value):
            try:
                return value.decode('UTF-8')
            except UnicodeDecodeError:
                return value
        return value

    def __setitem__(self, k, v):
        assert hasattr(k, 'isalnum')
        if not k.replace('.', '').replace('-', '').replace('_', '').isalnum():
            raise ValueError("key '%s' contains invalid characters (only numbers, letters, '.', '_', and '-' are allowed)" % k)
        # value must be a string or a CompressedValue or a file reference
        # (tuple (string|file [, bool, [, max_size [, fail_on_empty]]]))
        if not (isinstance(v, CompressedValue) or hasattr(v, 'isalnum') or
                (isinstance(v, tuple) and (
                    len(v) == 1 or (len(v) >= 2 and len(v) <= 4 and v[1] in (True, False))) and
                    (hasattr(v[0], 'isalnum') or hasattr(v[0], 'read')))):
            raise TypeError("value for key %s must be a string, CompressedValue, or a file reference" % k)

        return self.data.__setitem__(k, v)

    @classmethod
    def _assert_bin_mode(klass, file):
        '''Assert that given file object is in binary mode'''

        assert not hasattr(file, 'encoding'), 'file stream must be in binary mode'

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        global API

        print(time.asctime())
        time.sleep(1)
        if not API:
            with open('/etc/report_monitor/target.txt', 'r') as f:
                API = f.read().strip()
        with open(event.pathname, 'a') as f:
            f.write('Package: gconftool-2')
        subprocess.call(['apport-retrace', '-c', event.pathname])
        data = {}
        with open(event.pathname, 'rb') as f:
            report = ProblemReport()
            report.load(f)
            for key in report.data:
                if report.data[key] != '':
                    data[key] = report.data[key]
        result = requests.post(API, data=data)
        print('Status code: {}, body: {}'.format(
            result.status_code,
            result.text))
        print(time.asctime())

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch('/var/crash', mask)
notifier.loop()
