# DB Subnet Group (must use private subnets)
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = merge(
    {
      Name        = "${var.project_name}-${var.environment}-db-subnet-group"
      Environment = var.environment
    },
    var.tags
  )
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "main" {
  identifier             = "${var.project_name}-${var.environment}-db"
  engine                 = "postgres"
  engine_version         = "14.20"
  instance_class         = var.db_instance_class
  allocated_storage      = var.allocated_storage
  storage_type           = "gp3"

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.private_security_group_id]

  skip_final_snapshot       = true   # For dev only. Change to false + final_snapshot_identifier in prod
  publicly_accessible       = false
  multi_az                  = false  # Enable in prod for HA
  backup_retention_period   = 1 # free tier
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:04:00-sun:05:00"

  # Enable performance insights (free tier has limits)
  performance_insights_enabled = true

  tags = merge(
    {
      Name        = "${var.project_name}-${var.environment}-db"
      Environment = var.environment
    },
    var.tags
  )
}

# Generate a strong random password (stored in Terraform state - we will improve this later)
resource "random_password" "db_password" {
  length  = 24
  special = true
}

# Store the password in SSM Parameter Store (better than state long-term)
resource "aws_ssm_parameter" "db_password" {
  name  = "/${var.project_name}/${var.environment}/db/password"
  type  = "SecureString"
  value = random_password.db_password.result

  tags = merge(
    {
      Environment = var.environment
    },
    var.tags
  )
}
