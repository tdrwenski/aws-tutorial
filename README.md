# Notes
- You must have your AWS credentials configured in ~/.aws/credentials
- This stack creates a VPC, and each region can only have 5 VPCs max so may fail in some regions. It works for me with `us-west-2`.
- It is faster to pull a docker image from the ECR, especially for large images

# AWS CLI commands
Set parameters for create and update commands, e.g. for Raja:
``` bash
TUTORIAL_STACK_NAME=raja-tutorial
TUTORIAL_IMAGE=169939313066.dkr.ecr.us-west-2.amazonaws.com/raja-suite-tutorial:latest
TUTORIAL_PORT=3000
TUTORIAL_NAME=raja
TUTORIAL_QUERY_STRING="?folder=/home/rajadev/tutorial"
```

Configure a second stack for test purposes with below cloud formation commands, for instance with:
``` bash
TUTORIAL_STACK_NAME=nginx-tutorial
TUTORIAL_IMAGE=nginx:alpine
TUTORIAL_PORT=80
TUTORIAL_NAME=nginx
TUTORIAL_QUERY_STRING=""
```

## create stack
``` bash
aws cloudformation create-stack \
  --stack-name $TUTORIAL_STACK_NAME \
  --template-body file://dockerized-tutorial-template.yml \
  --parameters ParameterKey=TutorialImage,ParameterValue=$TUTORIAL_IMAGE \
               ParameterKey=TutorialPort,ParameterValue=$TUTORIAL_PORT \
               ParameterKey=TutorialName,ParameterValue=$TUTORIAL_NAME \
               ParameterKey=TutorialQueryString,ParameterValue=$TUTORIAL_QUERY_STRING \
  --capabilities CAPABILITY_NAMED_IAM
```

## update stack
``` bash
aws cloudformation update-stack \
  --stack-name $TUTORIAL_STACK_NAME \
  --template-body file://dockerized-tutorial-template.yml \
  --parameters ParameterKey=TutorialImage,ParameterValue=$TUTORIAL_IMAGE \
               ParameterKey=TutorialPort,ParameterValue=$TUTORIAL_PORT \
               ParameterKey=TutorialName,ParameterValue=$TUTORIAL_NAME \
               ParameterKey=TutorialQueryString,ParameterValue=$TUTORIAL_QUERY_STRING \
  --capabilities CAPABILITY_NAMED_IAM
```

## Slackbot integration through lambda
Add lambda to S3 bucket (hpcic-tutorials in us-west-2).
``` bash
./submit-lambdas.sh
```
If you update these lambdas be sure to update the `S3ObjectVersion` in cloud formation stack.

Get URL needed in slackbot slash command.
Note that this URL remains the same even when the stack is updated, only need to redo this step if you delete and re-create the stack.
``` bash
aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='SlackCommandUrl'].OutputValue" \
  --output text
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

## get tutorial IP addresses
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name $TUTORIAL_STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='GetContainerIPCommand'].OutputValue" \
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
