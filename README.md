# AWS Tutorial Set up

This CloudFormation stack deploys containerized tutorials on AWS Fargate or EC2.
Fargate has the advantage of being serverless, while EC2 has more hardware options like GPUs.
Tasks (docker containers) can be launched via CLI commands or Slack bot integration.
Tasks are automatically stopped after the specified timeout.
