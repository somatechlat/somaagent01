# AWS Infrastructure for SOMA Stack

This folder contains Terraform/CloudFormation templates for AWS deployment.

## Structure

```
aws/
├── eks/           # EKS Kubernetes cluster
├── rds/           # RDS PostgreSQL instances
├── elasticache/   # ElastiCache Redis clusters
└── msk/           # MSK Kafka clusters
```

## Local Development

For local development, we use:
- **LocalStack** (port 4566) - S3, SQS, Lambda, etc.
- **DynamoDB Local** (port 8000) - DynamoDB emulation

## Environment Variables

```bash
# For LocalStack (S3/SQS)
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1

# For DynamoDB Local
DYNAMODB_ENDPOINT=http://localhost:8000
```

## Commands

```bash
# Start LocalStack
docker start localstack

# Start DynamoDB Local
docker start dynamodb

# Verify LocalStack health
curl http://localhost:4566/_localstack/health
```
