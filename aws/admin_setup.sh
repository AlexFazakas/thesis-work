#!/bin/bash

aws dynamodb create-table \
    --table-name "reports" \
    --attribute-definitions AttributeName="Source IP Address",AttributeType=S \
    --key-schema AttributeName="Source IP Address",KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

aws lambda create-function \
    --function-name add_report \
    --runtime python3.8 \
    --role arn:aws:iam::090022703728:role/service-role/lambda_basic_execution \
    --handler lambda.lambda_handler \
    --zip-file fileb://lambda.zip

aws apigateway create-rest-api --name "crash_report_api"
APIGATEWAY_ID=$(aws apigateway get-rest-apis | grep -B 1 "crash_report_api" | head -1 | cut -d '"' -f 4)
RESOURCE_ID=$(aws apigateway get-resources --rest-api-id ${APIGATEWAY_ID} | grep id | cut -d'"' -f4)
aws apigateway create-resource --rest-api-id ${APIGATEWAY_ID} \
      --parent-id ${RESOURCE_ID} \
      --path-part add_report \

aws apigateway put-method --rest-api-id ${APIGATEWAY_ID} \
       --resource-id ${RESOURCE_ID} \
       --http-method POST \
       --authorization-type "NONE"

aws apigateway put-integration \
        --rest-api-id ${APIGATEWAY_ID} \
        --resource-id ${RESOURCE_ID} \
        --http-method POST \
        --type AWS \
        --integration-http-method POST \
        --uri arn:aws:apigateway:eu-central-1:lambda:path/2020-04-27/arn:aws:lambda:eu-central-1:090022703728:function:add_report/invocations

aws apigateway create-deployment \
        --rest-api-id ${APIGATEWAY_ID} \
        --stage-name test
