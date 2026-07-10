terraform {
  backend "s3" {
    bucket       = "devdeploy-terraform-state-bucket"
    key          = "environment/dev/terraform.tfstate"
    region       = "us-west-2"
    use_lockfile = true
    encrypt      = true
  }
}