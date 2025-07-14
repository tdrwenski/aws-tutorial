# AWS Tutorial Set up

This CloudFormation stack deploys containerized tutorials on AWS Fargate.
Tasks (docker containers) can be launched via CLI commands or Slack bot integration.
Tasks are automatically stopped after the specified timeout.

# Set up notes
- You must have your AWS credentials configured in `~/.aws/credentials`
- Use region `us-west-2`-- This stack creates a VPC, and each region can only have 5 VPCs max so may fail in e.g. `us-east-1`. You can set your region with `region = us-west-2` in `~/.aws/config`.
- For large docker images, use the ECR (also in `us-west-2`).
The SOCI indexer will automatically be used assuming the image matches the pattern in the `soci-index-builder` (see below). You will see index next to image in ECR after a few minutes and this will speed up pull time.

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
  --capabilities CAPABILITY_NAMED_IAM
```

## Lambdas
Add lambdas to S3 bucket (hpcic-tutorials in us-west-2).
``` bash
./submit-lambdas.sh
```

If you update these lambdas be sure to update the `S3ObjectVersion` in cloud formation stack. You can retrieve this with e.g.:
``` bash
aws s3api list-object-versions --bucket hpcic-tutorials --prefix slackbot/cleanup-tasks-function.zip --query 'Versions[0].VersionId' --output text
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


# SOCI indexer for docker images
SOCI (Seekable OCI) enables lazy loading of container images on AWS Fargate, allowing containers to start without waiting for the entire image to download. This can reduce startup times by 50-70% for large images. This requires the image to be in the ECR.


## Deploy the SOCI Index Builder
Deploy the official AWS SOCI Index Builder CloudFormation stack, which will automatically detect ECR pushes and create indices for matching images (currently only matching on raja image)
```
aws cloudformation create-stack \
  --stack-name soci-index-builder \
  --template-url https://aws-quickstart.s3.us-east-1.amazonaws.com/cfn-ecr-aws-soci-index-builder/templates/SociIndexBuilder.yml \
  --parameters ParameterKey=SociRepositoryImageTagFilters,ParameterValue="raja-suite-tutorial:*" \
  --capabilities CAPABILITY_IAM \
  --region us-west-2
```

## Push image to ECR
E.g. for raja image, we can make an ecr repo in our region:

```
aws ecr create-repository \
  --repository-name raja-suite-tutorial \
  --region us-west-2
```

Then we can update the image there:
```
# Get latest image from e.g. ghcr
docker pull ghcr.io/llnl/raja-suite-tutorial/tutorial:latest

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# Tag and push
docker tag ghcr.io/llnl/raja-suite-tutorial/tutorial:latest $ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/raja-suite-tutorial:latest
docker push $ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/raja-suite-tutorial:latest
```
