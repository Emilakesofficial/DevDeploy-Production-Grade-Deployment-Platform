output "db_endpoint" {
  description = "RDS endpoint address"
  value       = aws_db_instance.main.address
}

output "db_port" {
  description = "RDS port"
  value       = aws_db_instance.main.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.main.db_name
}

output "db_username" {
  description = "Database master username"
  value       = aws_db_instance.main.username
}

output "db_password_ssm_parameter" {
  description = "SSM Parameter name containing the database password"
  value       = aws_ssm_parameter.db_password.name
}

output "db_instance_identifier" {
  description = "RDS instance identifier"
  value       = aws_db_instance.main.identifier
}