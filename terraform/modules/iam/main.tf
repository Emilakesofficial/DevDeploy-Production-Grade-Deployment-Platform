# EC2 Instance Role
resource "aws_iam_role" "ec2_instance_role" {
    name = "${var.project_name}-${var.environment}-ec2-instance-role"

    assume_role_policy = jsonencode({
        Version = "2012-10-17"
        Statement = [
            {
                Effect = "Allow"
                Principal = {
                    Service = "ec2.amazonaws.com"
                }
                Action = "sts:AssumeRole"
            }
        ]
    })

    tags = merge(
        {
            Name = "${var.project_name}-${var.environment}-ec2-instance-role"
            Environment = var.environment
        },
        var.tags
    )
}

# Instance profile
resource "aws_iam_instance_profile" "ec2_instance_profile" {
    name = "${var.project_name}-${var.environment}-ec2-instance-profile"
    role = aws_iam_role.ec2_instance_role.name
}

# PERMISSION
# 1. SSM Managed Instance Core (allows SSM Session Manager instead of SSH keys)
resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# 2. CloudWatch Logs (for application and system logs)
resource "aws_iam_policy" "ec2_cloudwatch" {
  name = "${var.project_name}-${var.environment}-ec2-cloudwatch"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_cloudwatch_attach" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = aws_iam_policy.ec2_cloudwatch.arn
}

# 3. Basic S3 access (for future use - artifacts, static files, etc.)
resource "aws_iam_policy" "ec2_s3_access" {
  name = "${var.project_name}-${var.environment}-ec2-s3"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-*",
          "arn:aws:s3:::${var.project_name}-*/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_s3_attach" {
  role       = aws_iam_role.ec2_instance_role.name
  policy_arn = aws_iam_policy.ec2_s3_access.arn
}

