# AWS Lambda Function for secrets rotation


```shell
aws cloudformation package --template-file aws_secretsmanager_tenant_token_rotation.yaml --s3-bucket ${BUCKET_NAME} --s3-prefix conduktor_gateway_creds_rotation --output-template-file function.template --use-json

aws cloudformation deploy --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND --template-file function.template --stack-name fn--cdk-gw-rotation --parameter-overrides VpcId=vpc-06d42997bcb3e6f6c SubnetIds=subnet-05a29c79445d349b5,subnet-0e04c19e8b1e3f3ac CdkGatewayApiSecretArn=arn:aws:secretsmanager:eu-west-1:752667399118:secret:/conduktor/proxy/stg/apiuser-YPXaKy CDKGatewayApiURL=https://stg.kafka.nonprod.sc.js-devops.co.uk:8888 NewTokenLifetimeInSeconds=7200 PermissionsBoundary=arn:aws:iam::752667399118:policy/ccoe/js-developer


```
