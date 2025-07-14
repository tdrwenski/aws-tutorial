import boto3
import json
from datetime import datetime, timezone, timedelta

def lambda_handler(event, context):
    ecs = boto3.client('ecs')

    cluster_name = event['cluster_name']
    timeout_hours = event.get('timeout_hours', 6)

    try:
        # Calculate cutoff time
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)
        cutoff_iso = cutoff_time.isoformat()

        print(f"Cleaning up tasks older than {cutoff_iso} ({timeout_hours} hours)")

        # Get all running tasks from ECS
        tasks_response = ecs.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')

        if not tasks_response['taskArns']:
            print("No running tasks found")
            return {'cleaned_up': 0}

        # Get task details including tags
        tasks_details = ecs.describe_tasks(
            cluster=cluster_name,
            tasks=tasks_response['taskArns']
        )

        stopped_count = 0

        for task in tasks_details['tasks']:
            task_arn = task['taskArn']
            created_at = task['createdAt']

            # Check if task is older than timeout
            if created_at < cutoff_time:
                print(f"Stopping old task: {task_arn} (created: {created_at})")

                try:
                    # Stop the ECS task
                    ecs.stop_task(
                        cluster=cluster_name,
                        task=task_arn,
                        reason=f'Automatic cleanup after {timeout_hours} hours'
                    )

                    stopped_count += 1

                except Exception as e:
                    print(f"Error stopping task {task_arn}: {e}")

        print(f"Cleanup complete. Stopped {stopped_count} tasks.")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'stopped_tasks': stopped_count,
                'timeout_hours': timeout_hours
            })
        }
    except Exception as e:
        print(f"Cleanup failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
