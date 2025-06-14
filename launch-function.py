import base64
import json
import boto3
import urllib.parse
import time

cf = boto3.client("cloudformation")
ecs = boto3.client("ecs")
events = boto3.client("events")

def get_cf_output(outputs, key):
    for output in outputs:
        if output["OutputKey"] == key:
            return output["OutputValue"]
    raise Exception(f"Output key {key} not found")

def lambda_handler(event, context):
    raw_body = event.get("body", "")
    if event.get("isBase64Encoded", False):
        raw_body = base64.b64decode(raw_body).decode("utf-8")

    print("RAW EVENT BODY:", raw_body)

    stack_name = event["pathParameters"]["stack_name"]
    print(f"stack_name = {stack_name}")
    if not stack_name:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Stack name is required"})
        }

    params = urllib.parse.parse_qs(raw_body)
    response_url = params.get("response_url", [""])[0]
    user = params.get("user_name", ["unknown"])[0]

    try:
        # Look up stack outputs
        stack = cf.describe_stacks(StackName=stack_name)["Stacks"][0]
        outputs = stack["Outputs"]
        cluster = get_cf_output(outputs, "ClusterName")
        task_def = get_cf_output(outputs, "TaskDefinitionArn")
        subnet_id = get_cf_output(outputs, "PublicSubnetId")
        sg_id = get_cf_output(outputs, "SecurityGroupId")

        # Launch ECS task
        run_response = ecs.run_task(
            cluster=cluster,
            launchType="FARGATE",
            taskDefinition=task_def,
            count=1,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": [subnet_id],
                    "securityGroups": [sg_id],
                    "assignPublicIp": "ENABLED"
                }
            },
            tags=[
                {"key": "task-id", "value": f"task-{int(time.time())}"}
            ]
        )

        task_arn = run_response["tasks"][0]["taskArn"]
        tutorial_port = get_cf_output(outputs, "TutorialPort")
        tutorial_query_string = get_cf_output(outputs, "TutorialQueryString")

        # Emit event for async follow-up
        events.put_events(
            Entries=[{
                "Source": "custom.slackbot",
                "DetailType": "TaskStarted",
                "Detail": json.dumps({
                    "task_arn": task_arn,
                    "cluster": cluster,
                    "stack": stack_name,
                    "response_url": response_url,
                    "user": user,
                    "port": tutorial_port,
                    "query_string": tutorial_query_string
                })
            }]
        )

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "ephemeral",
                "text": f"Task is launching for `{stack_name}`.\nYou’ll get a message in a few minutes when it’s ready."
            })
        }

    except Exception as e:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "ephemeral",
                "text": f"Failed to launch task: {e}"
            })
        }
