import boto3
import json
from datetime import datetime, timezone, timedelta

def lambda_handler(event, context):
    ecs = boto3.client('ecs')
    autoscaling = boto3.client('autoscaling')

    cluster_name = event['cluster_name']
    timeout_hours = event.get('timeout_hours', 6)
    asg_name = event.get('asg_name')  # Auto Scaling Group name
    min_instances = event.get('min_instances', 0)  # Minimum instances to keep

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

        print(f"Task cleanup complete. Stopped {stopped_count} tasks.")

        # Now handle instance scaling based on remaining tasks
        scaled_instances = 0
        if asg_name:
            scaled_instances = scale_instances_based_on_tasks(
                ecs, autoscaling, cluster_name, asg_name, min_instances
            )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'success': True,
                'stopped_tasks': stopped_count,
                'scaled_instances': scaled_instances,
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

def scale_instances_based_on_tasks(ecs, autoscaling, cluster_name, asg_name, min_instances):
    """Scale down instances if no tasks are running"""
    try:
        # Check remaining running tasks
        tasks_response = ecs.list_tasks(cluster=cluster_name, desiredStatus='RUNNING')
        running_task_count = len(tasks_response['taskArns'])

        print(f"Current running tasks: {running_task_count}")

        asg_response = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[asg_name]
        )
        if not asg_response['AutoScalingGroups']:
            print(f"Auto Scaling Group {asg_name} not found")
            return 0

        asg = asg_response['AutoScalingGroups'][0]
        current_desired = asg['DesiredCapacity']
        current_instances = len(asg['Instances'])

        print(f"ASG status - Desired: {current_desired}, Current: {current_instances}, Min: {min_instances}")

        # Calculate optimal capacity
        if running_task_count == 0:
            # No tasks running - scale down to minimum
            optimal_capacity = min_instances
            reason = "No running tasks"
        else:
            # Tasks running - calculate needed instances (assuming 1 task per instance for now)
            # You can adjust this logic based on your instance capacity
            optimal_capacity = max(min_instances, running_task_count)
            reason = f"Supporting {running_task_count} tasks"

        if optimal_capacity < current_desired:
            print(f"Scaling down to {optimal_capacity} instances ({reason})")

            autoscaling.set_desired_capacity(
                AutoScalingGroupName=asg_name,
                DesiredCapacity=optimal_capacity,
                HonorCooldown=False
            )

            scaled_instances = current_desired - optimal_capacity
            print(f"Scaled down {scaled_instances} instances")
            return scaled_instances
        else:
            print(f"No scaling needed - keeping {current_desired} instances")
            return 0

    except Exception as e:
        print(f"Error during instance scaling: {e}")
        return 0
