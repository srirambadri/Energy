terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0" # Ensure you're using a recent version of the AWS provider
    }
  }
}

provider "aws" {
  region = var.aws_region
}

provider "aws" {
  alias  = "iam"
  region = var.aws_region
}