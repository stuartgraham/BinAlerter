from aws_cdk import (
    Stage,
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_ssm as ssm,
    aws_logs as logs,
    aws_events_targets as targets,
    aws_events as events
)
from constructs import Construct

class BinAlerterStage(Stage):
    def __init__(self, scope: Construct, id: str, ecr_repo=None, **kwargs):
        super().__init__(scope, id, **kwargs)
        self.ecr_repo = ecr_repo
        BinAlerterStack(self, 'BinAlerter', ecr_repo=self.ecr_repo)

class BinAlerterStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, ecr_repo=None, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.ecr_repo = ecr_repo

        # Lambda
        worcester_bot_latest_image = ssm.StringParameter.from_string_parameter_attributes(self, 'LatestImage',
            parameter_name='/BinAlerterWorcester/LatestImage').string_value
        worcester_telegram_bot = ssm.StringParameter.from_string_parameter_attributes(self, 'TelegramBot',
            parameter_name='/BinAlerterWorcester/TelegramBot').string_value
        worcester_chat_id = ssm.StringParameter.from_string_parameter_attributes(self, 'ChatId',
            parameter_name='/BinAlerterWorcester/ChatID').string_value
        worcester_address = ssm.StringParameter.from_string_parameter_attributes(self, 'Address',
            parameter_name='/BinAlerterWorcester/Address').string_value
        worcester_postcode = ssm.StringParameter.from_string_parameter_attributes(self, 'Postcode',
            parameter_name='/BinAlerterWorcester/Postcode').string_value


        worcester_bot_lambda = _lambda.DockerImageFunction(self, 'BinAlerter-WorcesterBot',
            code=_lambda.DockerImageCode.from_ecr(repository=ecr_repo, tag_or_digest=worcester_bot_latest_image),
            architecture=_lambda.Architecture.X86_64,
            function_name='BinAlerter-WorcesterBot',
            log_retention=logs.RetentionDays.FIVE_DAYS,
            timeout=Duration.minutes(1),
            memory_size=512,
            environment={
                        'POSTCODE': worcester_postcode,
                        'ADDRESS': worcester_address,
                        'BOT_TOKEN' : worcester_telegram_bot,
                        'CHAT_ID' : worcester_chat_id
            }
        )
        
        worcester_bot_lambda.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonEC2ContainerRegistryReadOnly'))

        lambda_target_worcester_bot = targets.LambdaFunction(worcester_bot_lambda)

        events.Rule(self, "EightPM",
            schedule=events.Schedule.cron(minute="7", hour="19"),
            targets=[lambda_target_worcester_bot]
        )