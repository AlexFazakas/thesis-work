#!/bin/bash

set -eu

REGION=$(aws configure get region)
ACCOUNT=$(aws sts get-caller-identity \
            --query Account \
            --output text)
echo 'Generating a policy JSON to allow the lambda function to insert into the DynamoDB table'
python3 policies_generator.py ${REGION} ${ACCOUNT}

echo 'Creating a "reports" DynamoDB table'
aws dynamodb create-table \
    --table-name "reports" \
    --attribute-definitions AttributeName="Date",AttributeType=S \
    --key-schema AttributeName="Date",KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 1> /dev/null

echo 'Creating an AWS policy with the generated JSON'
LAMBDA_POLICY_ARN=$(aws iam create-policy \
                  --policy-name crashReportsLambdaPolicy \
                  --policy-document file://lambda_policy.json | jq -r '.["Policy"]["Arn"]')

UI_POLICY_ARN=$(aws iam create-policy \
               --policy-name crashReportsUIPolicy \
               --policy-document file://ui_policy.json | jq -r '.["Policy"]["Arn"]')

echo 'Creating an AWS policy with the generated JSON'
aws iam attach-role-policy \
    --role-name lambda_basic_execution \
    --policy-arn ${LAMBDA_POLICY_ARN} 1> /dev/null

echo 'Creating a lambda function in order to handle requests'
FUNCTION_ARN=$(aws lambda create-function \
            --function-name add_report \
            --runtime python3.8 \
            --role arn:aws:iam::${ACCOUNT}:role/service-role/lambda_basic_execution \
            --handler lambda.lambda_handler \
            --zip-file fileb://lambda.zip | jq -r '.["FunctionArn"]')

echo 'Creating the API gateway'
APIGATEWAY_ID=$(aws apigatewayv2 create-api \
                --name crash_report_api \
                --protocol-type HTTP | jq -r '.["ApiId"]')

INTEGRATION_ID=$(aws apigatewayv2 create-integration \
    --api-id ${APIGATEWAY_ID} \
    --integration-type AWS_PROXY \
    --integration-uri ${FUNCTION_ARN} \
    --integration-method POST \
    --payload-format-version 2.0 | jq -r '.["IntegrationId"]')

aws apigatewayv2 create-route \
    --api-id ${APIGATEWAY_ID} \
    --route-key 'POST /add_report' \
    --target integrations/${INTEGRATION_ID} 1> /dev/null

aws apigatewayv2 create-stage \
    --api-id ${APIGATEWAY_ID} \
    --auto-deploy \
    --stage-name default 1> /dev/null

aws lambda add-permission \
    --statement-id cbdc4870-6d50-5c6e-8159-8ecefa4ae332 \
    --action lambda:InvokeFunction \
    --function-name ${FUNCTION_ARN} \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT}:${APIGATEWAY_ID}/*/*/add_report" 1> /dev/null

aws iam create-user --user-name reportsUIUser 1> /dev/null
aws iam create-access-key --user-name reportsUIUser | jq '.["AccessKey"]' | jq '{"AccessKeyId", "SecretAccessKey"}' > ui_credentials.json
aws iam attach-user-policy --user-name reportsUIUser --policy-arn ${UI_POLICY_ARN}

echo "Everything is now setup. The following URL is where you should be sending your reports:"
echo "https://${APIGATEWAY_ID}.execute-api.${REGION}.amazonaws.com/default/add_report"