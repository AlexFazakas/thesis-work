#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
from flask import Flask, render_template_string, request
import boto3
from boto3.dynamodb.conditions import Key, Attr
import pprint
import sys
import json

app = Flask(__name__)
data = []
file_loader = FileSystemLoader('./templates')
env = Environment(loader=file_loader)

MISSING_FILE = 1

def get_reports(client):
    reports = client.scan(TableName='reports')['Items']
    for report in reports:
        for k in report:
            report[k] = report[k]['S']
    return reports

@app.route('/full_report', methods=['GET'])
def full_report():
    global data

    index = int(request.args.get('report_index'))
    if index in range(len(data)):
        template = env.get_template('report.j2')
        output = template.render(report=data[index])
        return render_template_string(output)
    else:
        return 'Index out of range! There are only {} (0-indexed) reports in the database.'.format(
            len(data)
        )

@app.route('/raw_report', methods=['GET'])
def raw_report():
    global data

    index = int(request.args.get('report_index'))
    if index in range(len(data)):
        return json.dumps(data[index])
    else:
        return 'Index out of range! There are only {} (0-indexed)  reports in the database.'.format(
            len(data)
        )

@app.route('/', methods=['GET'])
def print_table():
    global data

    template = env.get_template('table.j2')
    output = template.render(reports=data, range=range(len(data)))
    return render_template_string(output)

def main():
    global data

    credentials = {}
    try:
        with open ('ui_credentials.json', 'r') as f:
            credentials = json.load(f)
    except OSError:
        print(
'''Missing credentials file. 
There should be a file called \'ui_credentials.json\' in the current directory.'''
        )
        sys.exit(MISSING_FILE)
    client = boto3.client('dynamodb',
                          aws_access_key_id=credentials['AccessKeyId'],
                          aws_secret_access_key=credentials['SecretAccessKey']
                        )
    data = get_reports(client)
    app.run()

if __name__ == '__main__':
    main()