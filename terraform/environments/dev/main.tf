terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "~> 5.0"
    }
  }
}

# Networking
module "networking" {
    source = "../../modules/networking"

    environment = "dev"
    project_name = "devdeploy"
    vpc_cidr = "10.0.0.0/16"
    availability_zones = ["us-west-2a", "us-west-2b"]

    tags = {
        Owner = "NuelCode"
    }
}

# Iam
module "iam" {
  source = "../../modules/iam"

  environment = "dev"
  project_name = "devdeploy"

  tags = {
    Owner = "NuelCode"
  }
}

module "database" {
  source = "../../modules/database"

  environment = "dev"
  project_name = "devdeploy"

  # Pass data from other modules
  vpc_id = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  private_security_group_id = module.networking.private_security_group_id

  db_name = "devdeploy"
  db_username = "devdeploy_admin"
  db_instance_class = "db.t3.micro"
  allocated_storage = 20

  tags = {
    Owner = "NuelCode"
  }
}

module "compute" {
  source = "../../modules/compute"

  environment = "dev"
  project_name = "devdeploy"

  vpc_id = module.networking.vpc_id
  public_subnet_ids = module.networking.public_subnet_ids
  public_security_group_id = module.networking.public_security_group_id
  iam_instance_profile = module.iam.ec2_instance_profile_name

  instance_type = "t3.micro"
  key_name = ""

  tags = {
    Owner = "NuelCode"
  }
}