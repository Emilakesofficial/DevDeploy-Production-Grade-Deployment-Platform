# Networking
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.networking.private_subnet_ids
}

output "public_security_group_id" {
  description = "Security group ID for public resources (EC2)"
  value       = module.networking.public_security_group_id
}

output "private_security_group_id" {
  description = "Security group ID for private resources (RDS)"
  value       = module.networking.private_security_group_id
}

# Compute (EC2)
output "ec2_instance_id" {
  description = "ID of the application EC2 instance"
  value       = module.compute.instance_id
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance (use this to connect)"
  value       = module.compute.public_ip
}

output "ec2_private_ip" {
  description = "Private IP address of the EC2 instance"
  value       = module.compute.private_ip
}

output "ec2_instance_state" {
  description = "Current state of the EC2 instance"
  value       = module.compute.instance_state
}

# Database (RDS PostgreSQL)
output "db_endpoint" {
  description = "RDS PostgreSQL endpoint (host:port)"
  value       = module.database.db_endpoint
}

output "db_port" {
  description = "RDS port"
  value       = module.database.db_port
}

output "db_name" {
  description = "Database name"
  value       = module.database.db_name
}

output "db_username" {
  description = "Database master username"
  value       = module.database.db_username
}

output "db_password_ssm_parameter" {
  description = "SSM Parameter Store path containing the database password (use AWS CLI or SDK to retrieve)"
  value       = module.database.db_password_ssm_parameter
}

output "db_instance_identifier" {
  description = "RDS instance identifier"
  value       = module.database.db_instance_identifier
}

# IAM
output "ec2_iam_role_name" {
  description = "Name of the IAM role attached to the EC2 instance"
  value       = module.iam.ec2_instance_role_name
}

output "ec2_iam_instance_profile_name" {
  description = "Name of the IAM instance profile"
  value       = module.iam.ec2_instance_profile_name
}

# Useful Connection Commands
output "ssm_connect_command" {
  description = "AWS CLI command to connect to the EC2 instance using SSM Session Manager (recommended)"
  value       = "aws ssm start-session --target ${module.compute.instance_id}"
}

# Summary
output "infrastructure_summary" {
  value = {
    ec2_public_ip = module.compute.public_ip
    rds_endpoint  = module.database.db_endpoint
    rds_database  = module.database.db_name
  }
}