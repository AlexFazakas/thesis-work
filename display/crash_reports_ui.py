#!/usr/bin/env python3

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
from flask import Flask, render_template_string, request
import boto3
from boto3.dynamodb.conditions import Key, Attr
import sys
import json

app = Flask(__name__)
data = []
visible_reports = []
file_loader = FileSystemLoader('./templates')
env = Environment(loader=file_loader)

MISSING_FILE = 1

def get_reports(client):
    reports = client.scan(TableName='reports')['Items']
    index = 0
    for report in reports:
        for k in report:
            report[k] = report[k]['S']
        report['index'] = index
        index += 1
    return reports

@app.route('/full_report', methods=['GET'])
def full_report():
    global data

    index = int(request.args.get('report_index'))
    if index in range(len(data)):
        template = env.get_template('report.j2')
        output = template.render(report=data[index])
        try:
            ret = render_template_string(output)
        except TemplateSyntaxError as e:
            # This might happen if a report contains '{{' or '}}'
            # so get rid of them for the purpose of displaying relevant data
            # and render it again
            for k in data[index]:
                if '{{' in str(data[index][k]) or '}}' in str(data[index][k]):
                    data[index][k] = data[index][k].replace('{{', '').replace('}}', '')
            output = template.render(report=data[index])
            ret = render_template_string(output)
        return ret
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

def group_by(reports, group_func):
    res = {}
    for r in reports:
        key = group_func(r)
        if key not in res:
            res[key] = []
        res[key].append(r)
    return res

def date_from_report(report):
    third_space = [i for i in range(len(report['Date'])) if report['Date'][i] == ' '][2]
    return report['Date'][:third_space]

def group_reports_by_date(reports):
    res = []
    grouped = group_by(reports, date_from_report)
    for key in grouped:
        for report in grouped[key]:
            res.append(report)
    return res

def translate_group_by_param(group):
    d = {
        'IP': 'Source IP Address',
        'Architecture': 'Architecture',
        'Distribution': 'DistroRelease',
        'Executable': 'ExecutablePath'
    }
    return d[group]

def report_matches_date(report, date):
    if not date:
        return True
    date = date.strip()

    month = report['Date'][4:7] == date[0:3]
    day = report['Date'][8:10] == date[4:6]
    year = report['Date'][20:24] == date[7:]
    return day and month and year

def matches_other_specific_fields(report, ip, arch, distro, executable):
    ip = ip.strip()
    arch = arch.strip()
    distro = distro.strip()
    executable = executable.strip()
    return not(len(ip) > 0 and not report['Source IP Address'] == ip or\
        len(arch) > 0 and not report['Architecture'] == arch or\
        len(distro) > 0 and not report['DistroRelease'] == distro or\
        len(executable) > 0 and not report['ExecutablePath'] == executable)

def filter_reports(reports, date, ip, arch, distro, executable):
    res = []
    for report in reports:
        if not report_matches_date(report, date):
            continue
        if not matches_other_specific_fields(report, ip, arch, distro, executable):
            continue
        res.append(report)
    return res

@app.route('/', methods=['GET'])
def print_table():
    global data
    global visible_reports

    if not visible_reports:
        visible_reports = data
    date = request.args.get('date')
    ip = request.args.get('ip')
    arch = request.args.get('architecture')
    distro = request.args.get('distribution')
    executable = request.args.get('executable')
    group = request.args.get('group_by')
    if date or ip or arch or distro or executable:
        visible_reports = filter_reports(data,
                                         date,
                                         ip,
                                         arch,
                                         distro,
                                         executable)
    elif not group:
        visible_reports = data
    if group:
        if group == 'Date':
            visible_reports = group_reports_by_date(visible_reports)
        else:
            grouped = group_by(visible_reports, lambda x: x[translate_group_by_param(group)])
            visible_reports = []
            for k in grouped:
                for r in grouped[k]:
                    visible_reports.append(r)
    template = env.get_template('table.j2')
    output = template.render(reports=visible_reports, range=range(len(visible_reports)))
    return render_template_string(output)

def main():
    global data

    credentials = {}
    try:
        with open('ui_credentials.json', 'r') as f:
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