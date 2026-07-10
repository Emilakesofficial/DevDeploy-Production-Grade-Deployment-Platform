variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project prefix"
  type        = string
  default     = "devdeploy"
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "public_security_group_id" {
  description = "Public security group ID"
  type        = string
}

variable "iam_instance_profile" {
  description = "IAM instance profile name"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.small"
}

variable "key_name" {
  description = "EC2 Key Pair (leave empty for SSM)"
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags"
  type        = map(string)
  default     = {}
}