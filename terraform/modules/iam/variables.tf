variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name prefix"
  type        = string
  default     = "devdeploy"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
