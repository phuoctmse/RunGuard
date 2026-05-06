variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "runguard"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}