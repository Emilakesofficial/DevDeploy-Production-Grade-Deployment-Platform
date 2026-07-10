data "aws_ami" "amazon_linux_2023" {
    most_recent = true
    owners = ["amazon"]

    filter {
        name = "name"
        values = ["al2023-ami-*-x86_64"]
    }
    filter {
        name = "virtualization-type"
        values = ["hvm"]
    }
}

locals {
    user_data = <<-EOF
      #!/bin/bash
      set -0
      echo "=== Starting DevDeploy user data ==="

      dnf update -y
      dnf install -y docker git htop jq

      systemctl enable docker
      systemctl start docker
      usermod -aG docker ec2-user

      # Docker Compose v2
    curl -SL https://github.com/docker/compose/releases/download/v2.29.1/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

    mkdir -p /opt/devdeploy
    chown -R ec2-user:ec2-user /opt/devdeploy

    docker network create devdeploy || true

    echo "=== Docker + Docker Compose ready ===" > /var/log/user-data.log
  EOF 
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = [var.public_security_group_id]
  iam_instance_profile   = var.iam_instance_profile

  user_data                   = base64encode(local.user_data)
  user_data_replace_on_change = true

  key_name = var.key_name != "" ? var.key_name : null

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = merge(
    {
      Name        = "${var.project_name}-${var.environment}-app-server"
      Environment = var.environment
      Role        = "application"
    },
    var.tags
  )

  lifecycle {
    ignore_changes = [user_data]
  }
}
