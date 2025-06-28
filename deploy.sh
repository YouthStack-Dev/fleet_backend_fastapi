#!/bin/bash

set -e

# Variables (edit as needed)
AWS_REGION=ap-south-1
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME=fleet-service-manager
IMAGE_TAG=latest

# 1. Build Docker image
docker build -t $REPO_NAME .

# 2. Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# 3. Create ECR repo if it doesn't exist
aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION

# 4. Tag and push image
IMAGE_URI=$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG
docker tag $REPO_NAME:latest $IMAGE_URI
docker push $IMAGE_URI

# 5. Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name fleet-service-manager \
  --parameter-overrides \
      VpcId=$1 \
      Subnets=\"$2\" \
      DBPassword=$3 \
      ECRImageUrl=$IMAGE_URI \
  --capabilities CAPABILITY_NAMED_IAM

echo "Deployment complete. Image: $IMAGE_URI"
