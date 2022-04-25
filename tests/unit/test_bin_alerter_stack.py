import aws_cdk as core
import aws_cdk.assertions as assertions

from bin_alerter.app_stack import BinAlerterStack

# example tests. To run these tests, uncomment this file along with the example
# resource in bin_alerter/bin_alerter_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = BinAlerterStack(app, "bin-alerter")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
