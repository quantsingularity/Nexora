# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_arn" {
  description = "ARN of the VPC"
  value       = aws_vpc.main.arn
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "vpc_default_security_group_id" {
  description = "ID of the default security group"
  value       = aws_vpc.main.default_security_group_id
}

output "vpc_default_network_acl_id" {
  description = "ID of the default network ACL"
  value       = aws_vpc.main.default_network_acl_id
}

output "vpc_default_route_table_id" {
  description = "ID of the default route table"
  value       = aws_vpc.main.default_route_table_id
}

# Subnet Outputs
output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "public_subnet_arns" {
  description = "ARNs of the public subnets"
  value       = aws_subnet.public[*].arn
}

output "public_subnet_cidr_blocks" {
  description = "CIDR blocks of the public subnets"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "private_subnet_arns" {
  description = "ARNs of the private subnets"
  value       = aws_subnet.private[*].arn
}

output "private_subnet_cidr_blocks" {
  description = "CIDR blocks of the private subnets"
  value       = aws_subnet.private[*].cidr_block
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = aws_subnet.database[*].id
}

output "database_subnet_arns" {
  description = "ARNs of the database subnets"
  value       = aws_subnet.database[*].arn
}

output "database_subnet_cidr_blocks" {
  description = "CIDR blocks of the database subnets"
  value       = aws_subnet.database[*].cidr_block
}

# Gateway Outputs
output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

output "internet_gateway_arn" {
  description = "ARN of the Internet Gateway"
  value       = aws_internet_gateway.main.arn
}

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "Public IPs of the NAT Gateways"
  value       = aws_eip.nat[*].public_ip
}

output "vpn_gateway_id" {
  description = "ID of the VPN Gateway"
  value       = var.enable_vpn_gateway ? aws_vpn_gateway.main[0].id : null
}

# Route Table Outputs
output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "IDs of the private route tables"
  value       = aws_route_table.private[*].id
}

output "database_route_table_ids" {
  description = "IDs of the database route tables"
  value       = aws_route_table.database[*].id
}

# Network ACL Outputs
output "public_network_acl_id" {
  description = "ID of the public network ACL"
  value       = var.enable_network_acls ? aws_network_acl.public[0].id : null
}

output "private_network_acl_id" {
  description = "ID of the private network ACL"
  value       = var.enable_network_acls ? aws_network_acl.private[0].id : null
}

output "database_network_acl_id" {
  description = "ID of the database network ACL"
  value       = var.enable_network_acls ? aws_network_acl.database[0].id : null
}

# VPC Flow Logs Outputs
output "vpc_flow_logs_id" {
  description = "ID of the VPC Flow Logs"
  value       = var.enable_flow_logs ? aws_flow_log.vpc[0].id : null
}

output "vpc_flow_logs_log_group_name" {
  description = "Name of the VPC Flow Logs CloudWatch Log Group"
  value       = var.enable_flow_logs ? aws_cloudwatch_log_group.vpc_flow_logs[0].name : null
}

# VPC Endpoint Outputs
output "s3_vpc_endpoint_id" {
  description = "ID of the S3 VPC endpoint"
  value       = var.enable_vpc_endpoints ? aws_vpc_endpoint.s3[0].id : null
}

output "dynamodb_vpc_endpoint_id" {
  description = "ID of the DynamoDB VPC endpoint"
  value       = var.enable_vpc_endpoints ? aws_vpc_endpoint.dynamodb[0].id : null
}

output "interface_vpc_endpoint_ids" {
  description = "IDs of the interface VPC endpoints"
  value       = aws_vpc_endpoint.interface[*].id
}

output "vpc_endpoint_security_group_id" {
  description = "ID of the VPC endpoint security group"
  value       = var.enable_vpc_endpoints ? aws_security_group.vpc_endpoint[0].id : null
}

# Availability Zone Outputs
output "availability_zones" {
  description = "List of availability zones used"
  value       = var.availability_zones
}

# Network Summary
output "network_summary" {
  description = "Summary of network configuration"
  value = {
    vpc_id                    = aws_vpc.main.id
    vpc_cidr                  = aws_vpc.main.cidr_block
    public_subnets_count      = length(aws_subnet.public)
    private_subnets_count     = length(aws_subnet.private)
    database_subnets_count    = length(aws_subnet.database)
    nat_gateways_count        = length(aws_nat_gateway.main)
    availability_zones_count  = length(var.availability_zones)
    flow_logs_enabled         = var.enable_flow_logs
    vpc_endpoints_enabled     = var.enable_vpc_endpoints
    network_acls_enabled      = var.enable_network_acls
    vpn_gateway_enabled       = var.enable_vpn_gateway
  }
}

