variable "author_name" {
  description = "Creator"
  type        = string
  default     = "SB"
}

variable "aws_region" {
  description = "The AWS region where resources will be deployed."
  type        = string
  default     = "eu-west-2" # Change this to your preferred region
}

variable "project_name" {
  description = "A unique prefix for naming resources."
  type        = string
  default     = "energy-trading"
}

variable "kinesis_stream_name" {
  description = "Base name of the Kinesis Data Stream."
  type        = string
  default     = "market-data-stream"
}

variable "batch_instance_type" {
  description = "EC2 instance type for AWS Batch compute environment."
  type        = string
  default     = "m5.large" # Choose an appropriate instance type for your ML workload
}

variable "batch_max_vcpus" {
  description = "Maximum number of vCPUs for the AWS Batch compute environment."
  type        = number
  default     = 8
}

variable "batch_job_cpu" {
  description = "CPU units for the AWS Batch job (1024 units = 1 vCPU)."
  type        = number
  default     = 1024 # 1 vCPU
}

variable "batch_job_memory" {
  description = "Memory (in MiB) for the AWS Batch job."
  type        = number
  default     = 4096 # 4 GiB
}

variable "docker_image_name" {
  description = "Name of the Docker image repository in ECR."
  type        = string
  default     = "energy-forecaster"
}

variable "docker_image_tag" {
  description = "Tag for the Docker image in ECR."
  type        = string
  default     = "latest"
}
