import boto3
import time
import json
import requests

ecs = boto3.client("ecs")
ec2 = boto3.client("ec2")

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))

    detail = event["detail"]
    cluster = detail["cluster"]
    task_arn = detail["task_arn"]
    response_url = detail["response_url"]

    try:
        start_time = time.time()

        for attempt in range(100):
            task = ecs.describe_tasks(cluster=cluster, tasks=[task_arn])["tasks"][0]
            last_status = task["lastStatus"]
            print(f"[Attempt {attempt}] Task status: {last_status}")

            if last_status == "RUNNING":
                break
            time.sleep(5)
        else:
            send_response(response_url, "Task is taking too long to start. Try again in a minute.")
            return

        elapsed = time.time() - start_time
        print(f"Total wait time: {elapsed:.1f} seconds")

        container_instance_arn = task["containerInstanceArn"]
        # Get the actual EC2 instance ID from the container instance
        container_instances = ecs.describe_container_instances(
            cluster=cluster,
            containerInstances=[container_instance_arn]
        )
        instance_id = container_instances["containerInstances"][0]["ec2InstanceId"]
        host_port = task["containers"][0]["networkBindings"][0]["hostPort"]
        instance_desc = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = instance_desc["Reservations"][0]["Instances"][0]["PublicIpAddress"]

        query_string = detail.get("query_string", "")

        # Send IP to Slack
        send_response(response_url, f"Your container is ready at `http://{public_ip}:{host_port}{query_string}`")

    except Exception as e:
        print("Error:", e)
        send_response(response_url, f"Error retrieving container IP: {e}")


def send_response(url, message):
    try:
        response = requests.post(url, json={
            "response_type": "in_channel",
            "text": message
        })
        print(f"Slack response status: {response.status_code}")
    except Exception as e:
        print("Failed to post to Slack:", e)
