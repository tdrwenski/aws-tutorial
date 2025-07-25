# AWS Tutorial Set up

This CloudFormation stack deploys containerized tutorials on AWS ECS with EC2 instances.
Tasks (docker containers) can be launched via CLI commands or Slack bot integration.

**Scaling behavior:**
- **Automatic scale UP**: Instances are launched automatically when tasks need them
- **Manual pre-warming**: Use DesiredCapacity parameter to keep instances ready
- **Automatic cleanup**: Tasks and their instances are terminated after timeout

See below for setting up AMI.
Notes:
- You must have your AWS credentials configured in `~/.aws/credentials`
- You can set your region with `region = us-east-1` in `~/.aws/config`.

# AWS CLI commands
Set parameters for create and update commands, e.g. for Raja:
``` bash
TUTORIAL_STACK_NAME=raja-tutorial
TUTORIAL_IMAGE=raja-suite-tutorial:latest
TUTORIAL_PORT=3000
TUTORIAL_NAME=raja
TUTORIAL_QUERY_STRING="?folder=/home/rajadev/tutorial"
TASK_TIMEOUT_HOURS=8 # Low for testing
INSTANCE_TYPE=g4dn.xlarge
KEY_PAIR_NAME=""  # Leave empty to disable SSH, or specify key pair name
TUTORIAL_AMI=ami-0ace94ec55fdbb964
DESIRED_CAPACITY=0  # Number of instances to pre-warm (0 = no pre-warming, 10 = keep 10 ready)
```

or for MFEM:
``` bash
TUTORIAL_STACK_NAME=mfem-tutorial
TUTORIAL_IMAGE=ghcr.io/mfem/containers/developer-cpu:latest
TUTORIAL_PORT=3000
ADDITIONAL_PORTS="8000,8080"
TUTORIAL_NAME=mfem
TUTORIAL_QUERY_STRING="?folder=/home/euler/mfem"
TASK_TIMEOUT_HOURS=1 # Low for testing
INSTANCE_TYPE=g4dn.xlarge
KEY_PAIR_NAME="tutorial-key-east"  # Leave empty to disable SSH, or specify key pair name
TUTORIAL_AMI=ami-05e9292d97072fe11 # AWS ECS/GPU AMI
DESIRED_CAPACITY=0  # Number of instances to pre-warm (0 = no pre-warming, 10 = keep 10 ready)
```

## Deploy stack
This creates or updates a cloudformation stack and waits until changes are complete:
``` bash
aws cloudformation deploy \
  --stack-name $TUTORIAL_STACK_NAME \
  --template-file dockerized-tutorial-template.yml \
  --parameter-overrides \
    TutorialImage=$TUTORIAL_IMAGE \
    TutorialPort=$TUTORIAL_PORT \
    AdditionalPorts="$ADDITIONAL_PORTS" \
    TutorialName=$TUTORIAL_NAME \
    TutorialQueryString=$TUTORIAL_QUERY_STRING \
    TaskTimeoutHours=$TASK_TIMEOUT_HOURS \
    InstanceType=$INSTANCE_TYPE \
    KeyPairName=$KEY_PAIR_NAME \
    TutorialAMI=$TUTORIAL_AMI \
    DesiredCapacity=$DESIRED_CAPACITY \
  --capabilities CAPABILITY_NAMED_IAM
```

## Lambdas
Add lambdas to S3 bucket (hpcic-tutorials-lambdas in us-east-1).
``` bash
./submit-lambdas.sh
```

If you update these lambdas be sure to update the `S3ObjectVersion` in cloud formation stack. You can retrieve this with e.g.:
``` bash
aws s3api list-object-versions \
    --bucket hpcic-tutorials-lambdas \
    --prefix slackbot-ec2/ \
    --query 'Versions[?IsLatest==`true`].[Key,VersionId]' \
    --output table
```

## Launch tasks from CLI
Launch tasks from CLI and wait for tutorial URLs to be returned:
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='LaunchTasksCommand'].OutputValue" \
  --output text)"

# Launch a single task
launch_tasks 1

# Launch multiple tasks
launch_tasks 3
```

## Get container URLs
To get URLs for all running tasks:
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='GetContainerUrlCommand'].OutputValue" \
  --output text)"
```

To get URLs for CLI launched tasks only:
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='GetCliTaskUrlCommand'].OutputValue" \
  --output text)"
```

## Delete all tasks
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CleanupCommand`].OutputValue' \
  --output text)"
```

## Scale instances manually
``` bash
# Get Auto Scaling Group name
ASG_NAME=$(aws cloudformation describe-stack-resources \
  --stack-name $TUTORIAL_STACK_NAME \
  --logical-resource-id AutoScalingGroup \
  --query 'StackResources[0].PhysicalResourceId' \
  --output text)

# Scale to N instances (e.g. 0 to shut down, 100 to pre-warm)
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name $ASG_NAME \
  --desired-capacity 0

# Check current utilization
CLUSTER_NAME=$(aws cloudformation describe-stack-resources \
  --stack-name $TUTORIAL_STACK_NAME \
  --logical-resource-id Cluster \
  --query 'StackResources[0].PhysicalResourceId' \
  --output text)
RUNNING_TASKS=$(aws ecs list-tasks --cluster $CLUSTER_NAME --desired-status RUNNING --query 'length(taskArns[])')
INSTANCES=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names $ASG_NAME --query 'AutoScalingGroups[0].Instances[?LifecycleState==`InService`]' --output json | jq length)
echo "Running tasks: $RUNNING_TASKS, Available instances: $INSTANCES"
```

## Delete stack
``` bash
aws cloudformation delete-stack --stack-name $TUTORIAL_STACK_NAME
```

# Slackbot integration
Go to the [Slack API](https://api.slack.com/). Choose "Your apps" and create or choose existing app, then go to slash commands. You just need to make a command name, description, and set the request URL to:

``` bash
aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='SlackCommandUrl'].OutputValue" \
  --output text
```

Note that this URL remains the same even when the stack is updated, only need to redo this step if you delete and re-create the stack.

# Creating an AMI
To start from a GPU-optimized AMI with ECS and Docker installed:
```
aws ssm get-parameters \
  --names /aws/service/ecs/optimized-ami/amazon-linux-2/gpu/recommended/image_id \
  --region us-east-1 \
  --query "Parameters[0].Value" \
  --output text
```
You can run an instance with this AMI, ssh to it, pull docker images and make other updates, and then create a new AMI.
