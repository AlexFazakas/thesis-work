import json
import boto3
import base64
from urllib.parse import parse_qs

DB_FIELDS = [
    'Date',
    'Architecture',
    'Disassembly',
    'DistroRelease',
    'ExecutablePath',
    'ExecutableTimestamp',
    'Package',
    'ProblemType',
    'ProcCmdline',
    'ProcCwd',
    'ProcMaps',
    'ProcStatus',
    'Registers',
    'Signal',
    'Stacktrace',
    'StacktraceAddressSignature',
    'StacktraceTop',
    'ThreadStacktrace',
    'Uname',
    'UserGroups',
    'Source IP Address'
]

def is_valid_report(report):
    for key in DB_FIELDS:
        if key not in report:
            return False, key
    return True, None

def lambda_handler(event, context):
    table = boto3.resource('dynamodb').Table('reports')
    try:
        report = parse_qs(base64.b64decode(event['body']).decode('utf-8'),
                          strict_parsing=True)
    except:
        return {
            'statusCode': 400,
            'body': 'Couldn\'t parse the request data into a dictionary object.'
        }
    report['Source IP Address'] = event['requestContext']['http']['sourceIp']
    for k in report:
        if len(report[k]) == 1:
            report[k] = report[k][0]
    print(report.keys())
    is_valid, missing_key = is_valid_report(report)
    if not is_valid:
        return {
            'statusCode': 400,
            'body': 'The report is missing the following field: {}.'.format(
                missing_key
            )
        }
    table.put_item(Item=report)
    return {
        'statusCode': 200,
        'body': 'Added the new report to the database'
    }

