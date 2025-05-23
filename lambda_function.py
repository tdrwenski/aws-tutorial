import base64
import json
import boto3
import urllib.parse
import time

cf = boto3.client("cloudformation")
ecs = boto3.client("ecs")
ec2 = boto3.client("ec2")

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
    params = urllib.parse.parse_qs(raw_body)
    print(f"params = {params}")
    text_values = params.get("text", [])
    text = text_values[0].strip() if text_values else ""

    # Require a stack name
    if not text:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "ephemeral",  # Only visible to the user
                "text": "You must specify a stack name.\nUsage: `/launch <stack-name>`"
            })
        }

    stack_name = text

    try:
        stack = cf.describe_stacks(StackName=stack_name)["Stacks"][0]
        outputs = stack["Outputs"]

        cluster = get_cf_output(outputs, "ClusterName")
        task_def = get_cf_output(outputs, "TaskDefinitionArn")
        subnet_id = get_cf_output(outputs, "PublicSubnetId")
        sg_id = get_cf_output(outputs, "SecurityGroupId")

        response = ecs.run_task(
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

        task_arn = response["tasks"][0]["taskArn"]
        ecs.get_waiter("tasks_running").wait(cluster=cluster, tasks=[task_arn])

        task_desc = ecs.describe_tasks(cluster=cluster, tasks=[task_arn])
        eni_id = next(d["value"] for d in task_desc["tasks"][0]["attachments"][0]["details"]
                      if d["name"] == "networkInterfaceId")

        eni = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni_id])
        public_ip = eni["NetworkInterfaces"][0]["Association"]["PublicIp"]

        msg = f"Task launched in stack `{stack_name}`.\nPublic IP: `{public_ip}`"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "in_channel",
                "text": msg
            })
        }

    except Exception as e:
        msg = f"Failed with {e}"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "response_type": "ephemeral",
                "text": msg
            })
        }
