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

        # Get ENI and public IP
        eni_id = next(d["value"] for d in task["attachments"][0]["details"]
                      if d["name"] == "networkInterfaceId")

        eni_desc = ec2.describe_network_interfaces(NetworkInterfaceIds=[eni_id])
        public_ip = eni_desc["NetworkInterfaces"][0]["Association"]["PublicIp"]
        port = detail.get("port", "80")
        query_string = detail.get("query_string", "")

        # Send IP to Slack
        send_response(response_url, f"Your container is ready at `http://{public_ip}:{port}{query_string}`")

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
