import boto3
import os


def lambda_handler(event, context):
    """
    Intercept an IOT message, retrieve the ARN of the SNS topic,
    then pass the message on to that SNS topic

    :param event: An IOT event message in JSON format
    :param context:
    :return: Nothing
    """

    # Unused - this is done to make pylint happy
    assert context

    # Debug
    print(event)
    print(context.aws_request_id)

    arn = os.environ['CAT_DOORBELL_SNS_TOPIC_ARN']

    client = boto3.client('sns')

    response = client.publish(
        TopicArn=arn,
        Message=event['message'],
        Subject='IOT Event Message'
    )

    if response['ResponseMetadata']['HTTPStatusCode'] != 200:
        raise Exception
