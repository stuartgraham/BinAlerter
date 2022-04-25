from aws_cdk import (
    App,
    Environment
)
from bin_alerter.pipeline_stack import PipelineStack

app = App()
aws_env = Environment(account="811799881965", region="eu-west-1")

PipelineStack(app, "BinAlerterPipeline", 
    env=aws_env
    )

app.synth()
