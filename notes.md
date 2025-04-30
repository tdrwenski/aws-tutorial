# TODO
- use port 3000 instead of 80
- try to define VPC and subnet?
- way to scale/ create more containers

# Find VPC (or can do in console)
``` bash
aws ec2 describe-vpcs --query "Vpcs[*].{ID:VpcId,IsDefault:IsDefault}" --output table
```

# Find Subnet (public one)
``` bash
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=<your-vpc-id> \
  --query "Subnets[*].{ID:SubnetId,AZ:AvailabilityZone}" --output table
```

# create stack
``` bash
aws cloudformation create-stack \
  --stack-name raja-vscode \
  --template-body file://raja-tutorial-fargate.yml \
  --parameters ParameterKey=VpcId,ParameterValue=vpc-05f480585932bbb68 \
               ParameterKey=SubnetId,ParameterValue=subnet-0442b01e66a745423  \
  --capabilities CAPABILITY_NAMED_IAM
```

# update stack
``` bash
aws cloudformation update-stack \
  --stack-name raja-vscode \
  --template-body file://raja-tutorial-fargate.yml \
  --parameters ParameterKey=VpcId,ParameterValue=vpc-05f480585932bbb68 \
            ParameterKey=SubnetId,ParameterValue=subnet-0442b01e66a745423  \
  --capabilities CAPABILITY_NAMED_IAM
```

# task arn
``` bash
aws ecs list-tasks --cluster raja-cluster  
```

# describe task
``` bash
aws ecs describe-tasks --cluster raja-cluster \
  --tasks <task-arn> \
  --query 'tasks[0].attachments[0].details'
```
