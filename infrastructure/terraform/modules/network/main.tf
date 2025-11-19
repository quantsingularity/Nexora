# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# VPC with enhanced security configuration
resource "aws_vpc" "main" {
  cidr_block                       = var.vpc_cidr
  enable_dns_support               = var.enable_dns_support
  enable_dns_hostnames             = var.enable_dns_hostnames
  assign_generated_ipv6_cidr_block = false
  instance_tenancy                 = "default"

  tags = {
    Name                = "${var.app_name}-${var.environment}-vpc"
    Environment         = var.environment
    SecurityCompliance  = "Financial"
    NetworkSegmentation = "Enabled"
  }
}

# Default security group - restrict all traffic
resource "aws_default_security_group" "default" {
  count  = var.restrict_default_sg ? 1 : 0
  vpc_id = aws_vpc.main.id

  # Remove all default rules
  ingress = []
  egress  = []

  tags = {
    Name        = "${var.app_name}-${var.environment}-default-sg-restricted"
    Environment = var.environment
    Purpose     = "Restricted-Default"
  }
}

# Public subnets for load balancers and NAT gateways
resource "aws_subnet" "public" {
  count                           = length(var.public_subnet_cidrs)
  vpc_id                          = aws_vpc.main.id
  cidr_block                      = var.public_subnet_cidrs[count.index]
  availability_zone               = var.availability_zones[count.index]
  map_public_ip_on_launch         = false  # Security best practice
  assign_ipv6_address_on_creation = false

  tags = {
    Name                     = "${var.app_name}-${var.environment}-public-subnet-${count.index + 1}"
    Environment              = var.environment
    Tier                     = "Public"
    "kubernetes.io/role/elb" = "1"  # For EKS load balancers
  }
}

# Private subnets for application servers
resource "aws_subnet" "private" {
  count                           = length(var.private_subnet_cidrs)
  vpc_id                          = aws_vpc.main.id
  cidr_block                      = var.private_subnet_cidrs[count.index]
  availability_zone               = var.availability_zones[count.index]
  map_public_ip_on_launch         = false
  assign_ipv6_address_on_creation = false

  tags = {
    Name                              = "${var.app_name}-${var.environment}-private-subnet-${count.index + 1}"
    Environment                       = var.environment
    Tier                             = "Private"
    "kubernetes.io/role/internal-elb" = "1"  # For EKS internal load balancers
  }
}

# Database subnets for enhanced security isolation
resource "aws_subnet" "database" {
  count                           = length(var.database_subnet_cidrs)
  vpc_id                          = aws_vpc.main.id
  cidr_block                      = var.database_subnet_cidrs[count.index]
  availability_zone               = var.availability_zones[count.index]
  map_public_ip_on_launch         = false
  assign_ipv6_address_on_creation = false

  tags = {
    Name        = "${var.app_name}-${var.environment}-database-subnet-${count.index + 1}"
    Environment = var.environment
    Tier        = "Database"
    Purpose     = "Database-Only"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.app_name}-${var.environment}-igw"
    Environment = var.environment
  }
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count  = var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0
  domain = "vpc"

  tags = {
    Name        = "${var.app_name}-${var.environment}-nat-eip-${count.index + 1}"
    Environment = var.environment
    Purpose     = "NAT-Gateway"
  }

  depends_on = [aws_internet_gateway.main]
}

# NAT Gateways for private subnet internet access
resource "aws_nat_gateway" "main" {
  count         = var.enable_nat_gateway ? length(var.public_subnet_cidrs) : 0
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name        = "${var.app_name}-${var.environment}-nat-gateway-${count.index + 1}"
    Environment = var.environment
  }

  depends_on = [aws_internet_gateway.main]
}

# VPN Gateway for hybrid connectivity
resource "aws_vpn_gateway" "main" {
  count  = var.enable_vpn_gateway ? 1 : 0
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.app_name}-${var.environment}-vpn-gateway"
    Environment = var.environment
    Purpose     = "Hybrid-Connectivity"
  }
}

# Route tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  dynamic "route" {
    for_each = var.enable_vpn_gateway ? [1] : []
    content {
      cidr_block = "10.0.0.0/8"  # On-premises CIDR
      gateway_id = aws_vpn_gateway.main[0].id
    }
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-public-route-table"
    Environment = var.environment
    Tier        = "Public"
  }
}

resource "aws_route_table" "private" {
  count  = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.main.id

  dynamic "route" {
    for_each = var.enable_nat_gateway ? [1] : []
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.main[count.index].id
    }
  }

  dynamic "route" {
    for_each = var.enable_vpn_gateway ? [1] : []
    content {
      cidr_block = "10.0.0.0/8"  # On-premises CIDR
      gateway_id = aws_vpn_gateway.main[0].id
    }
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-private-route-table-${count.index + 1}"
    Environment = var.environment
    Tier        = "Private"
  }
}

resource "aws_route_table" "database" {
  count  = length(var.database_subnet_cidrs)
  vpc_id = aws_vpc.main.id

  # Database subnets should not have internet access for security
  dynamic "route" {
    for_each = var.enable_vpn_gateway ? [1] : []
    content {
      cidr_block = "10.0.0.0/8"  # On-premises CIDR only
      gateway_id = aws_vpn_gateway.main[0].id
    }
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-database-route-table-${count.index + 1}"
    Environment = var.environment
    Tier        = "Database"
  }
}

# Route table associations
resource "aws_route_table_association" "public" {
  count          = length(var.public_subnet_cidrs)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count          = length(var.private_subnet_cidrs)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

resource "aws_route_table_association" "database" {
  count          = length(var.database_subnet_cidrs)
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database[count.index].id
}

# Network ACLs for enhanced security
resource "aws_network_acl" "public" {
  count  = var.enable_network_acls ? 1 : 0
  vpc_id = aws_vpc.main.id

  # Allow HTTP/HTTPS inbound
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }

  # Allow ephemeral ports for return traffic
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Allow all outbound traffic
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-public-nacl"
    Environment = var.environment
    Tier        = "Public"
  }
}

resource "aws_network_acl" "private" {
  count  = var.enable_network_acls ? 1 : 0
  vpc_id = aws_vpc.main.id

  # Allow traffic from public subnets
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 65535
  }

  # Allow ephemeral ports for return traffic
  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 1024
    to_port    = 65535
  }

  # Allow all outbound traffic
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-private-nacl"
    Environment = var.environment
    Tier        = "Private"
  }
}

resource "aws_network_acl" "database" {
  count  = var.enable_network_acls ? 1 : 0
  vpc_id = aws_vpc.main.id

  # Allow traffic only from private subnets
  ingress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 3306  # MySQL/Aurora
    to_port    = 3306
  }

  ingress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 5432  # PostgreSQL
    to_port    = 5432
  }

  # Allow ephemeral ports for return traffic
  ingress {
    protocol   = "tcp"
    rule_no    = 120
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 1024
    to_port    = 65535
  }

  # Allow outbound traffic only to VPC
  egress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = var.vpc_cidr
    from_port  = 0
    to_port    = 65535
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-database-nacl"
    Environment = var.environment
    Tier        = "Database"
  }
}

# Network ACL associations
resource "aws_network_acl_association" "public" {
  count          = var.enable_network_acls ? length(var.public_subnet_cidrs) : 0
  network_acl_id = aws_network_acl.public[0].id
  subnet_id      = aws_subnet.public[count.index].id
}

resource "aws_network_acl_association" "private" {
  count          = var.enable_network_acls ? length(var.private_subnet_cidrs) : 0
  network_acl_id = aws_network_acl.private[0].id
  subnet_id      = aws_subnet.private[count.index].id
}

resource "aws_network_acl_association" "database" {
  count          = var.enable_network_acls ? length(var.database_subnet_cidrs) : 0
  network_acl_id = aws_network_acl.database[0].id
  subnet_id      = aws_subnet.database[count.index].id
}

# VPC Flow Logs for security monitoring
resource "aws_flow_log" "vpc" {
  count           = var.enable_flow_logs ? 1 : 0
  iam_role_arn    = aws_iam_role.flow_log[0].arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_logs[0].arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id

  tags = {
    Name        = "${var.app_name}-${var.environment}-vpc-flow-logs"
    Environment = var.environment
    Purpose     = "Security-Monitoring"
  }
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  count             = var.enable_flow_logs ? 1 : 0
  name              = "/aws/vpc/flowlogs/${var.app_name}-${var.environment}"
  retention_in_days = var.flow_logs_retention
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-vpc-flow-logs"
    Environment = var.environment
    Purpose     = "Security-Monitoring"
  }
}

# IAM role for VPC Flow Logs
resource "aws_iam_role" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  name  = "${var.app_name}-${var.environment}-vpc-flow-log-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-vpc-flow-log-role"
    Environment = var.environment
    Purpose     = "VPC-Flow-Logs"
  }
}

# IAM policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_log" {
  count = var.enable_flow_logs ? 1 : 0
  name  = "${var.app_name}-${var.environment}-vpc-flow-log-policy"
  role  = aws_iam_role.flow_log[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# VPC Endpoints for secure AWS service access
resource "aws_vpc_endpoint" "s3" {
  count           = var.enable_vpc_endpoints ? 1 : 0
  vpc_id          = aws_vpc.main.id
  service_name    = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id,
    aws_route_table.database[*].id
  )

  tags = {
    Name        = "${var.app_name}-${var.environment}-s3-endpoint"
    Environment = var.environment
    Purpose     = "Secure-AWS-Access"
  }
}

resource "aws_vpc_endpoint" "dynamodb" {
  count           = var.enable_vpc_endpoints ? 1 : 0
  vpc_id          = aws_vpc.main.id
  service_name    = "com.amazonaws.${data.aws_region.current.name}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id,
    aws_route_table.database[*].id
  )

  tags = {
    Name        = "${var.app_name}-${var.environment}-dynamodb-endpoint"
    Environment = var.environment
    Purpose     = "Secure-AWS-Access"
  }
}

# Interface endpoints for other AWS services
locals {
  interface_endpoints = var.enable_vpc_endpoints ? [
    "ec2",
    "ssm",
    "ssmmessages",
    "ec2messages",
    "kms",
    "secretsmanager",
    "monitoring",
    "logs"
  ] : []
}

resource "aws_vpc_endpoint" "interface" {
  count               = length(local.interface_endpoints)
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.${local.interface_endpoints[count.index]}"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoint[0].id]
  private_dns_enabled = true

  tags = {
    Name        = "${var.app_name}-${var.environment}-${local.interface_endpoints[count.index]}-endpoint"
    Environment = var.environment
    Purpose     = "Secure-AWS-Access"
  }
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoint" {
  count       = var.enable_vpc_endpoints ? 1 : 0
  name        = "${var.app_name}-${var.environment}-vpc-endpoint-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-vpc-endpoint-sg"
    Environment = var.environment
    Purpose     = "VPC-Endpoints"
  }
}
