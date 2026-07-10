# DevDeploy Architecture

## Version 1

Internet

↓

Internet Gateway

↓

VPC

↓

Public Subnet A

↓

EC2

↓

Docker Compose

↓

NGINX

↓

Django

↓

Redis

↓

Celery Worker

↓

Celery Beat

↓

Private Subnet A

↓

Amazon RDS PostgreSQL

---

## Infrastructure

Terraform provisions

- VPC
- Public Subnets
- Private Subnets
- Route Tables
- Internet Gateway
- Security Groups
- EC2
- RDS
- S3
- Elastic IP

---

## Deployment Flow

Developer

↓

Git Push

↓

GitHub Actions CI

↓

Tests

↓

Docker Build

↓

GitHub Actions CD

↓

Terraform Apply

↓

Deploy Containers

↓

Run Migrations

↓

Collect Static

↓

Health Check

↓

Deployment Successful

---

## Docker Services

- Django
- Redis
- Celery Worker
- Celery Beat
- Flower
- NGINX

Database is Amazon RDS.

---

## Infrastructure Principles

Infrastructure is immutable.

Everything is reproducible.

Everything is provisioned using Terraform.

No manual AWS configuration.

Secrets never exist inside Git.

Infrastructure should be modular.

Deployment should be repeatable.