#!/bin/bash

REGION=$(aws configure get region)
ACCOUNT=$(aws sts get-caller-identity \
            --query Account \
            --output text)
python3 lambda_policy_generator.py ${REGION} ${ACCOUNT}
aws dynamodb create-table \
    --table-name "reports" \
    --attribute-definitions AttributeName="Date",AttributeType=S \
    --key-schema AttributeName="Date",KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

POLICY_ARN=$(aws iam create-policy \
            --policy-name lambdaPolicy \
            --policy-document file://lambda_policy.json | jq '.["Policy"]["Arn"]')
aws iam attach-role-policy \
    --role-name lambda_basic_execution \
    --policy-arn arn:aws:iam::${ACCOUNT}:policy/lambdaPolicy
echo ${POLICY_ARN}

FUNCTION_ARN=$(aws lambda create-function \
            --function-name add_report \
            --runtime python3.8 \
            --role arn:aws:iam::${ACCOUNT}:role/service-role/lambda_basic_execution \
            --handler lambda.lambda_handler \
            --zip-file fileb://lambda.zip | jq -r '.["FunctionArn"]')

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
    --target integrations/${INTEGRATION_ID}

aws apigatewayv2 create-stage \
    --api-id ${APIGATEWAY_ID} \
    --auto-deploy \
    --stage-name default

aws lambda add-permission \
    --statement-id cbdc4870-6d50-5c6e-8159-8ecefa4ae332 \
    --action lambda:InvokeFunction \
    --function-name ${FUNCTION_ARN} \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:${REGION}:${ACCOUNT}:${APIGATEWAY_ID}/*/*/add_report"

echo "Everything is now setup. The following URL is where you should be sending your reports:"
echo "https://${APIGATEWAY_ID}.execute-api.${REGION}.amazonaws.com/default/add_report"