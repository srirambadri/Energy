## AWS Infrastructure Creation using Terraform

This repository contains Terraform configurations to deploy a scalable and robust data pipeline on AWS

## Infrastructure Overview

**Amazon S3 Buckets:**

energy-trading-market-data-raw: Stores raw high-frequency market data ingested via Kinesis Firehose.

energy-trading-firehose-errors: Stores any error records from Kinesis Firehose data delivery.

energy-trading-forecast-results: Stores processed data or forecasting results.

**Amazon Kinesis Data Stream:**

A real-time data stream to ingest high-frequency market data.

**Amazon Kinesis Data Firehose Delivery Stream:**

A fully managed service that continuously captures data from the Kinesis Data Stream and automatically delivers it to the raw S3 bucket.

**IAM Roles & Policies:**

Appropriate IAM roles and policies are created to grant necessary permissions for Firehose to deliver data to S3.

**Amazon EC2 Security Group:**

A dedicated security group with outbound rules for general compute environment needs.

## Prerequisites

AWS CLI: Configured with credentials for your AWS account and set to the target region.
```bash
aws configure
```

## Deployment Steps

**Clone this Repository:**
```bash
git clone https://github.com/srirambadri/Energy.git
cd Terraform-AWS # e.g., cd terraform-energy-trading
```
**Initialize Terraform:**
```bash
terraform init -upgrade
```
**Review the Plan:**
```bash
terraform plan
```
**Apply the Configuration:**A
```bash
terraform apply
Enter a value: yes
```

## Inputs (Variables)

aws_region: The AWS region for deployment (default: eu-west-2).

project_name: A unique prefix for all resources (default: energy-trading).

kinesis_stream_name: Base name for the Kinesis Data Stream (default: market-data-stream).

## Outputs

kinesis_stream_name: The full name of your Kinesis Data Stream.

market_data_raw_bucket_name: The name of the S3 bucket for raw market data.

forecast_results_bucket_name: The name of the S3 bucket for future forecast results.

## Cleanup
```bash
terraform destroy
Enter a value: yes
```