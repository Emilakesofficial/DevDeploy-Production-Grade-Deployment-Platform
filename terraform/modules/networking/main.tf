# VPC
resource "aws_vpc" "main" {
    cidr_block = var.vpc_cidr
    enable_dns_hostnames = var.enable_dns_hostnames
    enable_dns_support = var.enable_dns_support

    tags = merge (
        {
            Name = "${var.project_name}-${var.environment}-vpc"
            Environment = var.environment
            Project = var.project_name
        },
        var.tags
    )
}

# INTERNET GATEWAY(PUBLIC SUBNETS)
resource "aws_internet_gateway" "main" {
    vpc_id = aws_vpc.main.id

    tags = merge (
        {
            Name = "${var.project_name}-${var.environment}-igw"
            Environment = var.environment
        },
        var.tags
    )
}

# PUBLIC SUBNETS 
resource "aws_subnet" "public" {
    count = length(var.public_subnet_cidrs)
    vpc_id = aws_vpc.main.id
    cidr_block = var.public_subnet_cidrs[count.index]
    availability_zone = var.availability_zones[count.index]
    map_public_ip_on_launch = true

    tags = merge(
        {
            Name = "${var.project_name}-${var.environment}-public-${var.availability_zones[count.index]}"
            Environment = var.environment
            Type = "public"
        },
        var.tags
    )
}

# PRIVATE SUBNETS
resource "aws_subnet" "private" {
    count = length(var.private_subnet_cidrs)
    vpc_id = aws_vpc.main.id
    cidr_block = var.private_subnet_cidrs[count.index]
    availability_zone = var.availability_zones[count.index]

    tags = merge(
        {
            Name = "${var.project_name}-${var.environment}-private-${var.availability_zones[count.index]}"
            Environment = var.environment
            Type = "private"
        },
        var.tags
    )
}

# PUBLIC ROUTE TABLE
resource "aws_route_table" "public" {
    vpc_id = aws_vpc.main.id

    route {
        cidr_block = "0.0.0.0/0"
        gateway_id = aws_internet_gateway.main.id
    }

    tags = merge (
        {
            Name = "${var.project_name}-${var.environment}-public-rt"
            Environment = var.environment
            Type = "public"
        },
        var.tags
    )
}

# ASSOCIATE PUBLIC SUBNETS WITH THE PUBLIC ROUTE TABLE
resource "aws_route_table_association" "public" {
    count = length(aws_subnet.public)
    subnet_id = aws_subnet.public[count.index].id
    route_table_id = aws_route_table.public.id
}

# PRIVATE ROUTE TABLE(one per AZ)
resource "aws_route_table" "private" {
    count = length(aws_subnet.private)
    vpc_id = aws_vpc.main.id

    tags = merge(
        {
            Name = "${var.project_name}-${var.environment}-private-rt-${var.availability_zones[count.index]}"
            Environment = var.environment
            Type = "private"
        },
        var.tags
    )
}

resource "aws_route_table_association" "private" {
    count = length(aws_subnet.private)
    subnet_id = aws_subnet.private[count.index].id
    route_table_id = aws_route_table.private[count.index].id
}

# SECURITY GROUPS
# Security group for public resources(EC2, NGINX, etc.)
resource "aws_security_group" "public" {
    name = "${var.project_name}-${var.environment}-public-sg"
    description = "Security group for public-facing resources"
    vpc_id = aws_vpc.main.id

    # Allow SSH from anywhere
    ingress {
        description = "SSH"
        from_port = 22
        to_port = 22
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    # Allow HTTP
    ingress {
        description = "HTTP"
        from_port = 80
        to_port = 80
        protocol = "tcp"
        cidr_blocks = ["0.0.0.0/0"]
    }

    # Allow all outbound
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = merge(
        {
            Name = "${var.project_name}-${var.environment}-public-sg"
            Environment = var.environment
            Type = "public"
        },
        var.tags
    )
}

# Security group for private resources (RDS)
resource "aws_security_group" "private" {
    name = "${var.project_name}-${var.environment}-private-sg"
    description = "Security group for private resources (RDS)"
    vpc_id = aws_vpc.main.id

    # Allow all outbound
    egress {
        from_port = 0
        to_port = 0
        protocol = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    tags = merge(
        {
            Name = "${var.project_name}-${var.environment}-private-sg"
            Environment = var.environment
            Type = "private"
        },
        var.tags
    )
}

# Allow PostgreSQL from public SG to private SG (we will use this for RDS later)
resource "aws_security_group_rule" "postgres_from_public" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.private.id
  source_security_group_id = aws_security_group.public.id
  description              = "PostgreSQL access from public SG"
}