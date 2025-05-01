# create stack
``` bash
aws cloudformation create-stack \
  --stack-name raja-tutorial \
  --template-body file://dockerized-tutorial-template.yml \
  --parameters ParameterKey=TutorialImage,ParameterValue=ghcr.io/llnl/raja-suite-tutorial/tutorial:latest \
               ParameterKey=TutorialPort,ParameterValue=3000 \
               ParameterKey=TutorialName,ParameterValue=raja \
  --capabilities CAPABILITY_NAMED_IAM
```

# update stack
``` bash
aws cloudformation update-stack \
  --stack-name raja-tutorial \
  --template-body file://dockerized-tutorial-template.yml \
  --parameters ParameterKey=TutorialImage,ParameterValue=ghcr.io/llnl/raja-suite-tutorial/tutorial:latest \
               ParameterKey=TutorialPort,ParameterValue=3000 \
               ParameterKey=TutorialName,ParameterValue=raja \
  --capabilities CAPABILITY_NAMED_IAM
```

# start task (container)
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name raja-tutorial \
  --query 'Stacks[0].Outputs[?OutputKey==`RunTaskCommandTemplate`].OutputValue' \
  --output text)"
```

# get tutorial IP addresses
``` bash
./list-tasks-ips.sh raja-tutorial
```

# delete manually launched tasks
``` bash
eval "$(aws cloudformation describe-stacks \
  --stack-name raja-tutorial \
  --query 'Stacks[0].Outputs[?OutputKey==`CleanupCommand`].OutputValue' \
  --output text)"
```

# delete stack
``` bash
aws cloudformation delete-stack --stack-name raja-tutorial
```
