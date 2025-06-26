# Notes
- You must have your AWS credentials configured in ~/.aws/credentials
- Use region `us-west-2`-- This stack creates a VPC, and each region can only have 5 VPCs max so may fail in e.g. `us-east-1`.
- For large docker images, use ECR (also `us-west-2`).
The SOCI indexer will automatically be used (you will see index next to image in ECR after a few minutes) and speed up pull time.
See SOCI indexer info below.

# AWS CLI commands
Set parameters for create and update commands, e.g. for Raja:
``` bash
TUTORIAL_STACK_NAME=raja-tutorial
TUTORIAL_IMAGE=169939313066.dkr.ecr.us-west-2.amazonaws.com/raja-suite-tutorial:latest
TUTORIAL_PORT=3000
TUTORIAL_NAME=raja
TUTORIAL_QUERY_STRING="?folder=/home/rajadev/tutorial"
TASK_TIMEOUT_HOURS=6
```

## deploy stack (create or update)
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
  --capabilities CAPABILITY_NAMED_IAM
```

## Lambdas
Add lambdas to S3 bucket (hpcic-tutorials in us-west-2).
``` bash
./submit-lambdas.sh
```

If you update these lambdas be sure to update the `S3ObjectVersion` in cloud formation stack. You can retrieve this with e.g.:
``` base
aws s3api list-object-versions --bucket hpcic-tutorials --prefix slackbot/cleanup-tasks-function.zip --query 'Versions[0].VersionId' --output text
```

## start task (container)
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`RunTaskCommandTemplate`].OutputValue' \
  --output text)"
```

## start multiple tasks
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='LaunchMultipleTasksCommand'].OutputValue" \
  --output text)"

launch_tasks 3
```

## get tutorial URLs
All running tasks:
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='GetContainerUrlCommand'].OutputValue" \
  --output text)"
```

CLI launched tasks only:
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='GetCliTaskUrlCommand'].OutputValue" \
  --output text)"
```

## delete all manually launched tasks
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CleanupCommand`].OutputValue' \
  --output text)"
```

## delete stack
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


# SOCI indexer for docker images
SOCI (Seekable OCI) enables lazy loading of container images on AWS Fargate, allowing containers to start without waiting for the entire image to download. This can reduce startup times by 50-70% for large images.

## Deploy the SOCI Index Builder
Deploy the official AWS SOCI Index Builder CloudFormation stack, which will automatically detect ECR pushes and create indices for matching images
```
aws cloudformation create-stack \
  --stack-name soci-index-builder \
  --template-url https://aws-quickstart.s3.us-east-1.amazonaws.com/cfn-ecr-aws-soci-index-builder/templates/SociIndexBuilder.yml \
  --parameters ParameterKey=SociRepositoryImageTagFilters,ParameterValue="raja-suite-tutorial:*" \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```
