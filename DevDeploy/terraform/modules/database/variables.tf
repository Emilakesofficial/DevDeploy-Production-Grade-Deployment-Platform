variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "devdeploy"
}

variable "vpc_id" {
  description = "VPC ID where the database will be created"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "private_security_group_id" {
  description = "Security group ID that will be allowed to connect to the database"
  type        = string
}

variable "db_name" {
  description = "Name of the initial database"
  type        = string
  default     = "devdeploy"
}

variable "db_username" {
  description = "Master username for the database"
  type        = string
  default     = "devdeploy_admin"
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
