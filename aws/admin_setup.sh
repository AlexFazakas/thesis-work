#!/bin/bash

aws dynamodb create-table \
    --table-name "reports" \
    --attribute-definitions AttributeName="Source IP Address",AttributeType=S \
    --key-schema AttributeName="Source IP Address",KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

FUNCTION_ARN=$(aws lambda create-function \
            --function-name add_report \
            --runtime python3.8 \
            --role arn:aws:iam::090022703728:role/service-role/lambda_basic_execution \
            --handler lambda.lambda_handler \
            --zip-file fileb://lambda.zip | jq -r '.["FunctionArn"]')
echo ${FUNCTION_ARN}

APIGATEWAY_ID=$(aws apigatewayv2 create-api \
                --name crash_report_api \
                --protocol-type HTTP | jq -r '.["ApiId"]')
echo ${APIGATEWAY_ID}
INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id ${APIGATEWAY_ID} \
    --integration-type AWS_PROXY \
    --integration-uri ${FUNCTION_ARN} \
    --integration-method POST \
    --payload-format-version 2.0 | jq -r '.["IntegrationId"]')
echo ${INTEGRATION_ID}
aws apigatewayv2 create-route \
    --api-id ${APIGATEWAY_ID} \
    --route-key 'POST /add_report' \
    --target integrations/${INTEGRATION_ID}
