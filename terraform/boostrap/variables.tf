variable "aws_region" {
  description = "AWS region to deploy the remote state resources"
  type        = string
  default     = "us-west-2"
}


variable "bucket_name" {
  description = "Globally unique name for the s3 bucket"
  type        = string
}
