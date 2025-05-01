#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <stack-name>"
  exit 1
fi

STACK_NAME="$1"

CLUSTER=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ClusterName'].OutputValue" \
  --output text)

TASKS=$(aws ecs list-tasks --cluster "$CLUSTER" --desired-status RUNNING --query 'taskArns[]' --output text)

echo "task-id,public-ip"

for TASK in $TASKS; do
  TASK_ID=$(aws ecs list-tags-for-resource --resource-arn "$TASK" \
    --query 'tags[?key==`task-id`].value' --output text)

  ENI_ID=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK" \
    --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)

  PUBLIC_IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI_ID" \
    --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

  echo "$TASK_ID,$PUBLIC_IP"
done
