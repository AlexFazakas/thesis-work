#!/usr/bin/env python3

import boto3
from boto3.dynamodb.conditions import Key, Attr
import pprint
import sys
import click

INEXISTENT_FIELD = 1

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('reports')

DB_FIELDS = {
    'date': 'Date',
    'architecture': 'Architecture',
    'disassembly':'Disassembly',
    'distrorelease': 'DistroRelease',
    'executablepath': 'ExecutablePath',
    'executabletimestamp': 'ExecutableTimestamp',
    'package': 'Package',
    'problemtype': 'ProblemType',
    'proccmdline': 'ProcCmdline',
    'proccwd': 'ProcCwd',
    'procmaps': 'ProcMaps',
    'procstatus': 'ProcStatus',
    'registers': 'Registers',
    'signal': 'Signal',
    'stacktrace': 'Stacktrace',
    'stacktraceaddresssignature': 'StacktraceAddressSignature',
    'stacktracetop': 'StacktraceTop',
    'threadstacktrace': 'ThreadStacktrace',
    'uname': 'Uname',
    'usergroups': 'UserGroups'
}

def parse_fields(raw_fields: list):
    new_fields = []
    for field in raw_fields:
        if field.lower() in DB_FIELDS:
            new_fields.append(DB_FIELDS[field.lower()])
        else:
            print('Field \'{}\' does not match any fields in the database!'.format(field))
            sys.exit(INEXISTENT_FIELD)
    return new_fields if new_fields else list(DB_FIELDS.values())

@click.command()
@click.option('--fields', '-f', multiple=True)
def main(fields: (str)):
    fields = parse_fields(fields)
    response = table.scan(AttributesToGet=fields)
    pretty = pprint.PrettyPrinter()
    pretty.pprint(response['Items'])

if __name__ == '__main__':
    main()