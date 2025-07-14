# AWS Tutorial Set up

This CloudFormation stack deploys containerized tutorials on AWS ECS with EC2 instances.
Tasks (docker containers) can be launched via CLI commands or Slack bot integration.
Tasks are automatically stopped after the specified timeout.
See below for setting up AMI.

# Set up notes
- You must have your AWS credentials configured in `~/.aws/credentials`
- Use region `us-west-2`-- This stack creates a VPC, and each region can only have 5 VPCs max so may fail in e.g. `us-east-1`. You can set your region with `region = us-west-2` in `~/.aws/config`.
- For large docker images, use the ECR (also in `us-west-2`).

# AWS CLI commands
Set parameters for create and update commands, e.g. for Raja:
``` bash
TUTORIAL_STACK_NAME=raja-tutorial
TUTORIAL_IMAGE=raja-suite-tutorial:latest
TUTORIAL_PORT=3000
TUTORIAL_NAME=raja
TUTORIAL_QUERY_STRING="?folder=/home/rajadev/tutorial"
TASK_TIMEOUT_HOURS=6
INSTANCE_TYPE=g4dn.xlarge
KEY_PAIR_NAME="tutorial-key"  # Leave empty to disable SSH, or specify key pair name
TUTORIAL_AMI=ami-0dacb0ed3ad1f62de
MIN_INSTANCES=0  # 0 = scale to zero, 1+ = pre-warmed instances
MAX_INSTANCES=10  # Maximum instances to scale up to
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
    TutorialName=$TUTORIAL_NAME \
    TutorialQueryString=$TUTORIAL_QUERY_STRING \
    TaskTimeoutHours=$TASK_TIMEOUT_HOURS \
    InstanceType=$INSTANCE_TYPE \
    KeyPairName=$KEY_PAIR_NAME \
    TutorialAMI=$TUTORIAL_AMI \
    MinInstances=$MIN_INSTANCES \
    MaxInstances=$MAX_INSTANCES \
  --capabilities CAPABILITY_NAMED_IAM
```

## Lambdas
Add lambdas to S3 bucket (hpcic-tutorials in us-west-2).
``` bash
./submit-lambdas.sh
```

If you update these lambdas be sure to update the `S3ObjectVersion` in cloud formation stack. You can retrieve this with e.g.:
``` bash
aws s3api list-object-versions \
    --bucket hpcic-tutorials \
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

## Stop all instances manually
``` bash
# Get Auto Scaling Group name
ASG_NAME=$(aws cloudformation describe-stack-resources \
  --stack-name $TUTORIAL_STACK_NAME \
  --logical-resource-id AutoScalingGroup \
  --query 'StackResources[0].PhysicalResourceId' \
  --output text)

# Scale to zero instances
aws autoscaling set-desired-capacity \
  --auto-scaling-group-name $ASG_NAME \
  --desired-capacity 0

# Or force terminate:
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[?State.Name==`running`].InstanceId' \
  --output text | xargs aws ec2 terminate-instances --instance-ids
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
  --region us-west-2 \
  --query "Parameters[0].Value" \
  --output text
```
You can run an instance with this AMI, ssh to it, pull docker images and make other updates, and then create a new AMI.
