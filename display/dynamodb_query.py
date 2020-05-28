#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader
from flask import Flask, render_template, request
import boto3
from boto3.dynamodb.conditions import Key, Attr
import pprint
import sys
import json
import click

app = Flask(__name__)
data = []

@app.route('/raw_report', methods=['GET'])
def raw_report():
    global data

    index = request.args.get('report_index')
    return json.dumps(data[int(index)])

@app.route('/', methods=['GET'])
def print_table():
    global data

    return render_template('table.html')

def main():
    global data

    with open ('ui_credentials.json', 'r') as f:
        credentials = json.load(f)
    client = boto3.client('dynamodb',
                          aws_access_key_id=credentials['AccessKeyId'],
                          aws_secret_access_key=credentials['SecretAccessKey']
                        )
    data = client.scan(TableName='reports')['Items']
    file_loader = FileSystemLoader('./templates')
    env = Environment(loader=file_loader)
    template = env.get_template('table.j2')
    output = template.render(reports=data, range=range(len(data)))
    with open('templates/table.html', 'w') as f:
        f.write(output)
    app.run(debug=True)

if __name__ == '__main__':
    main()