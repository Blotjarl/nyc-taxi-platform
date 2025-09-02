# main.tf - Terraform Configuration for AWS Resources

# --- 0. Provider Configuration ---
# Specifies that we are using the AWS provider and sets the default region
# where all our resources will be created.
provider "aws" {
  region = "us-east-1"
}

# --- 1. S3 Buckets for Data Lake ---
# We need two buckets to create a simple data lake structure.
# One for raw, unprocessed data and another for clean, processed data.

# Bucket for the raw, original taxi data files.
resource "aws_s3_bucket" "raw_data" {
  # The bucket name includes a random suffix to ensure it is globally unique.
  bucket = "nyc-taxi-raw-data-project-${random_id.id.hex}"
  tags = {
    Name        = "NYC Taxi Raw Data"
    Project     = "NYC Taxi Analytics"
  }
}

# Bucket for the cleaned and transformed data, ready for analysis.
resource "aws_s3_bucket" "processed_data" {
  bucket = "nyc-taxi-processed-data-project-${random_id.id.hex}"
  tags = {
    Name        = "NYC Taxi Processed Data"
    Project     = "NYC Taxi Analytics"
  }
}

# This resource generates a random string, used to make resource names unique.
resource "random_id" "id" {
  byte_length = 8
}

# --- 2. IAM Roles and Policies for Permissions ---
# This section defines the permissions that our AWS services will use to
# interact with each other securely (e.g., allowing Fargate to access S3).

# Defines which AWS services are allowed to "assume" (use) this role.
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com", "sagemaker.amazonaws.com", "glue.amazonaws.com"]
    }
  }
}

# Creates the IAM role with the trust policy defined above.
resource "aws_iam_role" "data_processing_role" {
  name               = "DataProcessingRole"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# Attaches pre-built AWS policies to our role.
# In a production environment, you would create custom, more restrictive policies.
resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.data_processing_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.data_processing_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# --- 3. ECR Repository for Docker Image ---
# Amazon Elastic Container Registry (ECR) is a private Docker registry where
# we will store the container image for our Python ETL script.
resource "aws_ecr_repository" "taxi_processing_repo" {
  name                 = "nyc-taxi-processor"
  image_tag_mutability = "MUTABLE"
  tags = {
    Project = "NYC Taxi Analytics"
  }
}

# --- 4. Fargate & ECS (Elastic Container Service) ---
# This defines the environment where our containerized ETL job will run.
# Fargate is the serverless compute engine for containers.
resource "aws_ecs_cluster" "main_cluster" {
  name = "main-processing-cluster"
}

# Defines the blueprint for our ETL task. It specifies the Docker image to use,
# CPU/memory, and the IAM role for permissions.
resource "aws_ecs_task_definition" "processing_task" {
  family                   = "data-processor-task"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "1024" # 1 vCPU
  memory                   = "2048" # 2 GB
  execution_role_arn       = aws_iam_role.data_processing_role.arn
  task_role_arn            = aws_iam_role.data_processing_role.arn

  container_definitions = jsonencode([
    {
      name      = "nyc-taxi-processor-container"
      image     = "${aws_ecr_repository.taxi_processing_repo.repository_url}:latest"
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/processing-task"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# Creates a log group in CloudWatch to store logs from our container.
# This is crucial for debugging.
resource "aws_cloudwatch_log_group" "processing_logs" {
  name = "/ecs/processing-task"
}

# --- 5. AWS Athena for Serverless Querying ---
# Sets up Athena, which allows us to run SQL queries directly on our
# processed data files in S3.
resource "aws_athena_workgroup" "analytics_workgroup" {
  name = "analytics"
  
  configuration {
    result_configuration {
      # This S3 path is where Athena will store query results.
      output_location = "s3://${aws_s3_bucket.processed_data.bucket}/athena-query-results/"
    }
  }
}

resource "aws_athena_database" "taxi_db" {
  name   = "nyc_taxi_db"
  bucket = aws_s3_bucket.processed_data.bucket
}

# --- 6. Outputs ---
# These outputs will display useful information in the terminal after
# Terraform applies the configuration.
output "raw_data_bucket_name" {
  value = aws_s3_bucket.raw_data.bucket
}

output "processed_data_bucket_name" {
  value = aws_s3_bucket.processed_data.bucket
}

output "ecr_repository_url" {
  value = aws_ecr_repository.taxi_processing_repo.repository_url
}

output "ecr_repository_name" {
  description = "The name of the ECR repository for the ETL container."
  value       = aws_ecr_repository.taxi_processing_repo.name
}

output "ecs_task_definition_family" {
  description = "The family name of the ECS task definition."
  value       = aws_ecs_task_definition.processing_task.family
}