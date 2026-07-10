output "s3_bucket_name" {
  description = "Name of the S3 bucket created for Terraform state"
  value       = aws_s3_bucket.terraform_state.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

output "backend_config_example" {
  value = <<EOT
terraform {
  backend "s3" {
    bucket       = "${aws_s3_bucket.terraform_state.id}"
    key          = "environments/dev/terraform.tfstate"
    region       = "${var.aws_region}"
    encrypt      = true
    use_lockfile = true
  }
}
EOT
}

