# Notes
- You must have your AWS credentials configured in ~/.aws/credentials
- This stack creates a VPC, and each region can only have 5 VPCs max so may fail in some regions. It works for me with `us-west-2`.

# AWS CLI commands
## create stack
``` bash
aws cloudformation create-stack \
  --stack-name raja-tutorial \
  --template-body file://dockerized-tutorial-template.yml \
  --parameters ParameterKey=TutorialImage,ParameterValue=ghcr.io/llnl/raja-suite-tutorial/tutorial:latest \
               ParameterKey=TutorialPort,ParameterValue=3000 \
               ParameterKey=TutorialName,ParameterValue=raja \
  --capabilities CAPABILITY_NAMED_IAM
```

## update stack
``` bash
aws cloudformation update-stack \
  --stack-name raja-tutorial \
  --template-body file://dockerized-tutorial-template.yml \
  --parameters ParameterKey=TutorialImage,ParameterValue=ghcr.io/llnl/raja-suite-tutorial/tutorial:latest \
               ParameterKey=TutorialPort,ParameterValue=3000 \
               ParameterKey=TutorialName,ParameterValue=raja \
  --capabilities CAPABILITY_NAMED_IAM
```

## Slackbot integration through lambda
Add lambda to S3 bucket (hpcic-tutorials in us-west-2).
```
zip launch-function.zip launch-function.py
aws s3 cp launch-function.zip s3://hpcic-tutorials/slackbot/launch-function.zip
zip notify-function.zip notify-function.py
aws s3 cp notify-function.zip s3://hpcic-tutorials/slackbot/notify-function.zip
```

Get URL needed in slackbot slash command
```
aws cloudformation describe-stacks \
  --stack-name raja-tutorial \
  --query "Stacks[0].Outputs[?OutputKey=='SlackCommandUrl'].OutputValue" \
  --output text
```

## start task (container)
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name raja-tutorial \
  --query 'Stacks[0].Outputs[?OutputKey==`RunTaskCommandTemplate`].OutputValue' \
  --output text)"
```

## start multiple tasks
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name raja-tutorial \
  --query "Stacks[0].Outputs[?OutputKey=='LaunchMultipleTasksCommand'].OutputValue" \
  --output text)"

launch_tasks 3
```

## get tutorial IP addresses
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name raja-tutorial \
  --query "Stacks[0].Outputs[?OutputKey=='GetContainerIPCommand'].OutputValue" \
  --output text)"
```

## delete all manually launched tasks
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name raja-tutorial \
  --query 'Stacks[0].Outputs[?OutputKey==`CleanupCommand`].OutputValue' \
  --output text)"
```

## delete stack
``` bash
aws cloudformation delete-stack --stack-name raja-tutorial
```
