# Random suffix for resource names to ensure global uniqueness
resource "random_id" "suffix" {
  byte_length = 2
}

# Data source for AWS account ID, needed for CloudWatch Logs ARN
data "aws_caller_identity" "current" {}

# VPC and Subnet 
data "aws_vpc" "default" {
  default = true
}

# New data source to get all subnet IDs within the default VPC
data "aws_subnets" "default_vpc_subnets" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
# --- S3 Buckets ---

# S3 Bucket for raw market data from Kinesis Firehose
resource "aws_s3_bucket" "market_data_raw_bucket" {
  bucket = "${var.project_name}-market-data-raw-${random_id.suffix.hex}"
  tags = {
    Project   = var.project_name
    Purpose   = "RawMarketData"
    ManagedBy = var.author_name
  }
}

# S3 Bucket for Kinesis Firehose error records
resource "aws_s3_bucket" "firehose_error_bucket" {
  bucket = "${var.project_name}-firehose-errors-${random_id.suffix.hex}"
  tags = {
    Project   = var.project_name
    Purpose   = "FirehoseErrors"
    ManagedBy = var.author_name
  }
}

# S3 Bucket for processed forecast results
resource "aws_s3_bucket" "forecast_results_bucket" {
  bucket = "${var.project_name}-forecast-results-${random_id.suffix.hex}"
  tags = {
    Project   = var.project_name
    Purpose   = "ForecastResults"
    ManagedBy = var.author_name
  }
}

# --- Kinesis Data Stream ---

resource "aws_kinesis_stream" "market_data_stream" {
  name             = "${var.kinesis_stream_name}-${random_id.suffix.hex}"
  shard_count      = 1
  retention_period = 24

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

# --- IAM Role for Kinesis Firehose ---

resource "aws_iam_role" "firehose_delivery_role" {
  name = "${var.project_name}-firehose-delivery-role-${random_id.suffix.hex}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "firehose.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

resource "aws_iam_role_policy" "firehose_delivery_policy" {
  name = "${var.project_name}-firehose-delivery-policy-${random_id.suffix.hex}"
  role = aws_iam_role.firehose_delivery_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.market_data_raw_bucket.arn,
          "${aws_s3_bucket.market_data_raw_bucket.arn}/*",
          aws_s3_bucket.firehose_error_bucket.arn,
          "${aws_s3_bucket.firehose_error_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "kinesis:DescribeStream",
          "kinesis:GetShardIterator",
          "kinesis:GetRecords"
        ],
        Effect = "Allow",
        Resource = aws_kinesis_stream.market_data_stream.arn
      },
      {
        Action = [
          "logs:PutLogEvents"
        ],
        Effect = "Allow",
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/kinesisfirehose/*"
      }
    ]
  })
}


# --- Kinesis Data Firehose Delivery Stream ---

resource "aws_kinesis_firehose_delivery_stream" "market_data_delivery_stream" {
  name        = "${var.project_name}-delivery-stream-${random_id.suffix.hex}"
  destination = "extended_s3"
  
  # Source from Kinesis Data Stream
  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.market_data_stream.arn
    role_arn           = aws_iam_role.firehose_delivery_role.arn
  }

  extended_s3_configuration {
    role_arn            = aws_iam_role.firehose_delivery_role.arn
    bucket_arn          = aws_s3_bucket.market_data_raw_bucket.arn
    prefix              = "raw_market_data/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/"
    error_output_prefix = "errors/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/hour=!{timestamp:HH}/!{firehose:error-output-type}/" 
    
    compression_format = "GZIP"
  }

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

# --- ECR Repository for Docker Image ---

resource "aws_ecr_repository" "energy_forecaster_repo" {
  name                 = var.docker_image_name
  image_tag_mutability = "MUTABLE" 

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

# --- AWS Batch Compute Environment and Job Queue ---

# IAM Role for AWS Batch Service
resource "aws_iam_role" "batch_service_role" {
  name = "${var.project_name}-batch-service-role-${random_id.suffix.hex}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "batch.amazonaws.com"
        }
      }
    ]
  })
  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

# Attach the standard AWSBatchServiceRole managed policy
resource "aws_iam_role_policy_attachment" "batch_service_role_attachment" {
  role       = aws_iam_role.batch_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBatchServiceRole"
}

# Add an inline policy to grant ecs:DeleteCluster for cleanup
resource "aws_iam_role_policy" "batch_service_inline_ecs_delete_policy" {
  name = "${var.project_name}-batch-service-ecs-delete-policy-${random_id.suffix.hex}"
  role = aws_iam_role.batch_service_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "ecs:DeleteCluster",
          "ecs:DescribeClusters", # Often useful for cleanup orchestration
        ],
        Effect = "Allow",
        Resource = "arn:aws:ecs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:cluster/*" # Allow deleting any ECS cluster managed by Batch
      }
    ]
  })
}


# IAM Role for EC2 Instances in Batch Compute Environment
resource "aws_iam_role" "batch_instance_role" {
  name = "${var.project_name}-batch-instance-role-${random_id.suffix.hex}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

resource "aws_iam_instance_profile" "batch_instance_profile" {
  name = "${var.project_name}-batch-instance-profile-${random_id.suffix.hex}"
  role = aws_iam_role.batch_instance_role.name
  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

resource "aws_iam_role_policy_attachment" "batch_instance_policy_attachment" {
  role       = aws_iam_role.batch_instance_role.name
  # Correct policy ARN for EC2 instances used by ECS/Batch
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role" 
  depends_on = [aws_iam_role.batch_instance_role] # Explicit dependency added
}

# New resource to create a dedicated security group for Batch Compute Environment
resource "aws_security_group" "batch_compute_sg" {
  name        = "${var.project_name}-batch-compute-sg-${random_id.suffix.hex}"
  description = "Allow all outbound traffic for AWS Batch compute instances"
  vpc_id      = data.aws_vpc.default.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1" # All protocols
    cidr_blocks = ["0.0.0.0/0"] # All IPs
  }

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}


resource "aws_batch_compute_environment" "energy_forecaster_ce" {
  compute_environment_name = "${var.project_name}-compute-env-${random_id.suffix.hex}"
  type                     = "MANAGED"
  state                    = "ENABLED" 

  compute_resources {
    type                      = "EC2"
    instance_type             = [var.batch_instance_type]
    min_vcpus                 = 0
    max_vcpus                 = var.batch_max_vcpus
    desired_vcpus             = 0 # AWS Batch manages this
    instance_role             = aws_iam_instance_profile.batch_instance_profile.arn
    # Use subnet_ids from the new data source
    subnets                   = data.aws_subnets.default_vpc_subnets.ids
    # Add security group IDs from the newly created SG
    security_group_ids        = [aws_security_group.batch_compute_sg.id]

    allocation_strategy = "BEST_FIT_PROGRESSIVE" 

    ec2_configuration {
      image_type = "ECS_AL2" 
    }
  }

  service_role = aws_iam_role.batch_service_role.arn

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

resource "aws_batch_job_queue" "energy_forecaster_jq" {
  name     = "${var.project_name}-job-queue-${random_id.suffix.hex}"
  state    = "ENABLED"
  priority = 1

  compute_environment_order {
    compute_environment = aws_batch_compute_environment.energy_forecaster_ce.arn
    order               = 1
  }

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

# --- AWS Batch Job Definition ---

# IAM Role for AWS Batch Job Execution (Task Role)
resource "aws_iam_role" "batch_job_role" {
  name = "${var.project_name}-batch-job-role-${random_id.suffix.hex}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}

resource "aws_iam_role_policy" "batch_job_policy" {
  name = "${var.project_name}-batch-job-policy-${random_id.suffix.hex}"
  role = aws_iam_role.batch_job_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.market_data_raw_bucket.arn,
          "${aws_s3_bucket.market_data_raw_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "s3:PutObject"
        ],
        Effect = "Allow",
        Resource = [
          aws_s3_bucket.forecast_results_bucket.arn,
          "${aws_s3_bucket.forecast_results_bucket.arn}/*"
        ]
      },
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/batch/job*"
        Effect = "Allow"
      },
      {
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetAuthorizationToken"
        ],
        Effect = "Allow",
        Resource = "*" # ECR permissions for pulling image
      }
    ]
  })
}

resource "aws_batch_job_definition" "energy_forecaster_jd" {
  name = "${var.project_name}-job-definition-${random_id.suffix.hex}"
  type = "container"
  platform_capabilities = ["EC2"] 

  container_properties = jsonencode({
    image = "${aws_ecr_repository.energy_forecaster_repo.repository_url}:${var.docker_image_tag}"
    command = [] # Entrypoint is defined in Dockerfile
    environment = [
      { name = "INPUT_S3_BUCKET", value = aws_s3_bucket.market_data_raw_bucket.bucket },
      { name = "OUTPUT_S3_BUCKET", value = aws_s3_bucket.forecast_results_bucket.bucket },
      { name = "S3_KEY_PREFIX", value = "raw_market_data/" } 
    ]
    resourceRequirements = [
      { type = "VCPU", value = tostring(var.batch_job_cpu) }, 
      { type = "MEMORY", value = tostring(var.batch_job_memory) }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group = "/aws/batch/job" 
        awslogs-region = var.aws_region
        awslogs-stream-prefix = "batch"
      }
    }
    executionRoleArn = aws_iam_role.batch_job_role.arn # Role for ECS task execution
    jobRoleArn       = aws_iam_role.batch_job_role.arn # Role for permissions within the container (S3 access)
  })

  tags = {
    Project   = var.project_name
    ManagedBy = var.author_name
  }
}
