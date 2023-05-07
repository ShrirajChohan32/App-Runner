from aws_cdk import (
    # Duration,
    Stack,
    aws_apprunner as apprunner,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_logs as logs,
    aws_autoscaling as autoscaling,
    aws_elasticloadbalancingv2 as elbv2,
    aws_ecr as ecr,
    aws_ecr_assets as ecr_assets,
    aws_ecs as ecs,
    NestedStack,
    aws_route53_targets as targets,
    # aws_sqs as sqs,
)
from constructs import Construct
from aws_cdk import CfnTag

import aws_cdk as cdk
from aws_cdk.aws_ecr_assets import DockerImageAsset
# from cdk_ecr_deployment import ECRDeployment, DockerImageName
import os


class AppRunnerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #########################

        policy_doc = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "apprunner:CreateService",
                        "apprunner:DescribeService",
                        "apprunner:UpdateService",
                        "apprunner:DeleteService",
                        "apprunner:ListTagsForResource",
                        "apprunner:TagResource",
                        "apprunner:UntagResource"
                    ],
                    resources=["*"]
                )
            ]
        )

        AppRunner_task_role = iam.Role(
            self, "apprunner_task_execution_role",
            assumed_by=iam.ServicePrincipal("tasks.apprunner.amazonaws.com"),
            inline_policies={
                "MyPolicy": policy_doc
            }
        )

        role_arn = AppRunner_task_role.role_arn


        ECR_policy_doc = iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:DescribeImages",
                        "ecr:GetRepositoryPolicy",
                        "ecr:DescribeRepositories",
                        "ecr:ListImages",
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability"
                    ],
                    resources=["*"]
                )
            ]
        )

        # Add a policy to the role to allow App Runner to access ECR
        AppRunner_build_role = iam.Role(
            self, "build_execution_role",
            assumed_by=iam.ServicePrincipal("build.apprunner.amazonaws.com"),
            inline_policies={
                "MyPolicy": ECR_policy_doc
            }
        )

        build_arn = AppRunner_build_role.role_arn


        #Private ECR
        private_image = apprunner.CfnService(self, "Private-Service",
            service_name="nginx",       
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
                    access_role_arn=build_arn       # Assign A role that will the APP runner, fetch image from ECR
                ),
                image_repository=apprunner.CfnService.ImageRepositoryProperty(
                    image_configuration=apprunner.CfnService.ImageConfigurationProperty(port="80"), # Define port for the image
                    image_identifier="123456789012.dkr.ecr.ap-southeast-2.amazonaws.com/my-repo:latest",    # URI of the private ECR image.
                    image_repository_type="ECR" 
                    
                )
            ),
            instance_configuration=apprunner.CfnService.InstanceConfigurationProperty(
                cpu="1024",
                memory="2048",
            )
        )

            # We must add the task execution role ARN to the properties of the App Runner service
            # The property name is "authentication_configuration"
        authentication_configuration=apprunner.CfnService.AuthenticationConfigurationProperty(
            access_role_arn=role_arn    
            )
        
        # output the Private App Runner service URL
        cdk.CfnOutput(self, "AppRunnerPrivateService", value=private_image.attr_service_url)



        #########
        ### Public Service
        #########

        service = apprunner.CfnService(self, "Service",
            service_name="nginx",   
            source_configuration=apprunner.CfnService.SourceConfigurationProperty(
                image_repository=apprunner.CfnService.ImageRepositoryProperty(
                    image_configuration=apprunner.CfnService.ImageConfigurationProperty(port="8000"),     # App Runner's image port number
                    image_identifier="public.ecr.aws/aws-containers/hello-app-runner:latest",   # Public ECR image name
                    image_repository_type="ECR_PUBLIC"      #  Defining that the ECR can be pulled publicly 
                )
            ),
            instance_configuration=apprunner.CfnService.        # Creating APP runner instance configuration
            InstanceConfigurationProperty(
                cpu="1024", 
                memory="2048",
            )
        )

        cdk.CfnOutput(self, "AppRunnerService", value=service.attr_service_url)







        