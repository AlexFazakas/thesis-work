#!/usr/bin/env python3

import subprocess
import pyinotify
import os
import json
import time
import requests
from problem_report import ProblemReport


API = 'https://1l98y1vir2.execute-api.eu-central-1.amazonaws.com/add_report'
wm = pyinotify.WatchManager()

mask = pyinotify.IN_CREATE

class EventHandler(pyinotify.ProcessEvent):
    def process_IN_CREATE(self, event):
        print(time.asctime())
        time.sleep(2)
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
        print(result)
        print(time.asctime())

handler = EventHandler()
notifier = pyinotify.Notifier(wm, handler)
wdd = wm.add_watch('/var/crash', mask)
notifier.loop()
