#!/usr/bin/env python3

from flask import Flask
from flask import request
from flask import jsonify
from urllib.parse import parse_qs
import boto3
import requests
import json
from problem_report import ProblemReport


app = Flask(__name__)
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('reports')

@app.route('/report', methods=['POST'])
def add_report():
    data = parse_qs(request.get_data().decode('utf-8'))
    for k in data:
        if len(data[k]) == 1:
            data[k] = data[k][0]
    table.put_item(Item=data)
    response = jsonify(success=True)
    response.status_code = 200
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)