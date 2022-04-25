from aws_cdk import (
    Stack,
    SecretValue,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_codebuild as codebuild,
    pipelines as pipelines
)
from constructs import Construct

from bin_alerter.app_stack import BinAlerterStage
from bin_alerter.buildspec import build_spec as linked_build_spec

class PipelineStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ECR
        ecr_repo = ecr.Repository(self, "ECRRepo",
            repository_name="binalerterworcesterbot"
        )
        ecr_repo.add_lifecycle_rule(max_image_count=10)

        # Github Source
        git_hub = pipelines.CodePipelineSource.git_hub(
                    "stuartgraham/BinAlerter",
                    "main",
                    authentication=SecretValue.secrets_manager("github-token")
                )

        # Pipeline
        ## Synth
        pipeline = pipelines.CodePipeline(self, "Pipeline",
            synth = pipelines.ShellStep("Synth",
                input = git_hub,
                commands=[
                    "pip install -r requirements.txt", "npm install -g aws-cdk", "cdk synth"
                ]
            ),
            pipeline_name="BinAlerterPipeline"
        )

        ## Container build
        build_spec = codebuild.BuildSpec.from_object(linked_build_spec)
        build_role = iam.Role(self, "CodeBuildRole", 
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryPowerUser")
            ]
        )
        build_role.add_to_policy(iam.PolicyStatement(
                resources=["*"],
                actions=["ssm:PutParameter"]
        ))

        build_environment = codebuild.BuildEnvironment(
            build_image=codebuild.LinuxBuildImage.STANDARD_5_0,
            compute_type=codebuild.ComputeType.SMALL,
            privileged=True
            )

        container_build = pipelines.CodeBuildStep("ContainerBuild",
            build_environment = build_environment,
            input = git_hub,
            partial_build_spec=build_spec,
            commands=[],
            role=build_role,
            env={
                "AWS_ACCOUNT_ID": self.account,
                "REPO_NAME":  f"{self.account}.dkr.ecr.{self.region}.amazonaws.com/{ecr_repo.repository_name}"
            }
        )

        # App deploy
        bin_alerter_app = BinAlerterStage(self, "BinAlerterApp", ecr_repo=ecr_repo)
        pipeline.add_stage(bin_alerter_app, pre=[container_build])
