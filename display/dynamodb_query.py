#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
from flask import Flask, render_template, request
import boto3
from boto3.dynamodb.conditions import Key, Attr
import pprint
import sys
import json
import click

INEXISTENT_FIELD = 1

app = Flask(__name__)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('reports')
data = []

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
    'usergroups': 'UserGroups',
    'ip': 'Source IP Address'
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

@app.route('/raw_report', methods=['GET'])
def raw_report():
    global data

    index = request.args.get('report_index')
    return json.dumps(data[int(index)])

@app.route('/', methods=['GET'])
def print_table():
    global data

    return render_template('table.html')

@click.command()
@click.option('--fields', '-f', multiple=True)
def main(fields: (str)):
    global data

    fields = parse_fields(fields)
    data = table.scan(AttributesToGet=fields)['Items']
    file_loader = FileSystemLoader('./templates')
    env = Environment(loader=file_loader)
    template = env.get_template('table.j2')
    output = template.render(reports=data, range=range(len(data)))
    with open('templates/table.html', 'w') as f:
        f.write(output)
    app.run(debug=True)

if __name__ == '__main__':
    main()