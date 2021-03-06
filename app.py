import os
import sys

import aws_cdk.core as core
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_lambda as aws_lambda
import aws_cdk.aws_iam as iam
import aws_cdk.aws_apigatewayv2 as apigatewayv2
import aws_cdk.aws_apigatewayv2_integrations as apigatewayv2_integrations

import boto3

# Import the lambda function to scan for routes
sys.path.append(os.getcwd() + "/src")
import lambda_function

stage = os.environ['STAGE']
service_name = os.environ['FUNCTION']
region = os.environ['AWS_DEFAULT_REGION']
stack_name = f"{service_name}-{region}-{stage}"


class CdkStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        account = self.account

        print("")
        print(f"   Service: {service_name}")
        print(f"   Region:  {region}")
        print(f"   Stage:   {stage}")
        print(f"   Account: {account}")
        print(f"   Stack:   {stack_name}")
        print("")

        ssm = boto3.client('ssm')

        # Environment variable mapping
        environment: dict = {'dev': {
                                     'logLevel': 'DEBUG'
                                     },
                             'prod': {
                                      'logLevel': 'INFO'
                                      }
                             }

        # How to: Retrieve an existing VPC instance.
        vpc_id: str = ssm.get_parameter(Name="VpcId")['Parameter']['Value']
        vpc = ec2.Vpc.from_lookup(self, 'VPC', vpc_id=vpc_id)

        private_subnet_1_id: str = ssm.get_parameter(Name="private-subnet-1")['Parameter']['Value']
        private_subnet_2_id: str = ssm.get_parameter(Name="private-subnet-2")['Parameter']['Value']
        private_subnet_3_id: str = ssm.get_parameter(Name="private-subnet-3")['Parameter']['Value']

        # How to: Import a value exported from another stack
        # These values are imported from the simple-database stack https://github.com/SimpleServerless/simple-database/blob/main/template.yaml#L95
        # Change these lines to the appropriate values for your project
        db_host = core.Fn.import_value(f"simple-serverless-database-{stage}-Host")
        db_name = core.Fn.import_value(f"simple-serverless-database-{stage}-Name")
        app_security_group_id = core.Fn.import_value(f"simple-serverless-database-{stage}-AppSGId")

        env_variables = {
            'STAGE': stage,
            "PGHOST": db_host,
            "PGPORT": "5432",
            "PGDATABASE": db_name,
            "LOG_LEVEL": environment[stage]['logLevel']
        }

        # How to: Import a security group
        app_security_group = ec2.SecurityGroup.from_security_group_id(self, "AppSecurityGroup", app_security_group_id)

        # Create the main lambda function
        service_lambda = aws_lambda.Function(self,
                                             'LambdaFunction',
                                             runtime=aws_lambda.Runtime.PYTHON_3_8,
                                             description=service_name,
                                             code=aws_lambda.AssetCode("./dist"),
                                             function_name=service_name + "-" + stage,
                                             timeout=core.Duration.seconds(35),
                                             tracing=aws_lambda.Tracing.ACTIVE,
                                             memory_size=128,
                                             handler='lambda_function.handler',
                                             vpc=vpc,
                                             security_groups=[app_security_group],
                                             environment=env_variables)

        # Add SecretsManager permissions to lambda
        service_lambda.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["secretsmanager:DescribeSecret", "secretsmanager:GetSecretValue", "secretsmanager:List*"],
            resources=[f"arn:aws:secretsmanager:{region}:{account}:secret:simple-serverless/*"]))

        # Make a wide open security group for the secrets vpc endpoint
        vpc_endpoint_sg = ec2.SecurityGroup(self,
                                            'VpcEndpointSG',
                                            vpc=vpc,
                                            allow_all_outbound=True,
                                            description="Secret Manager VPC Endpoint SG")

        vpc_endpoint_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp_range(0, 65535),
            description="all inbound",
        )

        # How to create at VPC Endpoint to access secrets manager.
        # You can delete this if you're not too cheap to pay for a NAT instance.
        # This still costs $0.24 per day per AZ, so $0.72 for the three AZs we're using here
        # This block is the only reoccurring cost in this stack and is the only reason I delete this stack
        # when I'm not actively working on it.
        ec2.CfnVPCEndpoint(self, 'SecretsManagerVPCEndpoint',
                           service_name='com.amazonaws.us-east-2.secretsmanager',
                           vpc_endpoint_type='Interface',
                           vpc_id=vpc_id,
                           subnet_ids=[private_subnet_1_id, private_subnet_2_id, private_subnet_3_id],
                           security_group_ids=[vpc_endpoint_sg.security_group_id],
                           private_dns_enabled=True
                           )

        #
        # REST (API Gateway HTTP) stuff starts here
        #

        # How to: Import an existing HTTP API Gateway instance
        # http_api = apigatewayv2.HttpApi.from_api_id(self, id='APIGateway', http_api_id='0fdl9wlxw4')

        # How to: Create a new HTTP API Gateway instance
        http_api = apigatewayv2.HttpApi(
            self, 'APIGateway',
            api_name=f'{service_name}-api-{stage}'
        )

        integration = apigatewayv2_integrations.LambdaProxyIntegration(
            handler=service_lambda,
            payload_format_version=apigatewayv2.PayloadFormatVersion.VERSION_2_0
        )

        # How to: auto generate REST endpoints from decorators ex: @router.rest("GET", "/students").
        for route_key, endpoint in lambda_function.router.get_rest_endpoints().items():
            print(f"Creating REST endpoint for {route_key}")
            http_api.add_routes(
                path=endpoint['path'],
                methods=[apigatewayv2.HttpMethod(endpoint['method'])],
                integration=integration
            )


        core.CfnOutput(self, "RestAPIOutput",
                       value=http_api.url,
                       export_name=f"{stack_name}-RestApiUrl-{stage}")



# Sometimes AWS lets you use '-' ex: service-name and sometimes you have to or want to use camel case ex: serviceName.
# This saves me from having to create two sets of parameters
def to_camel(name):
    components = name.split('-')
    # We capitalize the first letter of each component except the first one
    # with the 'title' method and join them together.
    return ''.join(x.title() for x in components)


# Code to execute stack below
app = core.App()

# NOTE! ~/.aws/config will override the CDK_DEFAULT_ACCOUNT value no matter what you set it to in your environment variables
account = os.environ['AWS_ACCOUNT']
region = os.environ['AWS_DEFAULT_REGION']

CdkStack(app, f"{service_name}-us-east-2-dev", env={"account": account, "region": region})

app.synth()

# Possibly cleaner idea to define mulitple enviroments
# https://taimos.de/blog/deploying-your-cdk-app-to-different-stages-and-environments