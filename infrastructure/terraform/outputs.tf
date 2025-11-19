# Network Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.network.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.network.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.network.public_subnet_ids
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.network.private_subnet_ids
}

output "database_subnet_ids" {
  description = "IDs of the database subnets"
  value       = module.network.database_subnet_ids
}

output "nat_gateway_ids" {
  description = "IDs of the NAT Gateways"
  value       = module.network.nat_gateway_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.network.internet_gateway_id
}

output "vpc_flow_logs_id" {
  description = "ID of the VPC Flow Logs"
  value       = module.network.vpc_flow_logs_id
}

# Security Outputs
output "app_security_group_id" {
  description = "ID of the application security group"
  value       = module.security.app_security_group_id
}

output "db_security_group_id" {
  description = "ID of the database security group"
  value       = module.security.db_security_group_id
}

output "alb_security_group_id" {
  description = "ID of the Application Load Balancer security group"
  value       = module.security.alb_security_group_id
}

output "kms_key_id" {
  description = "ID of the KMS key"
  value       = aws_kms_key.main.key_id
}

output "kms_key_arn" {
  description = "ARN of the KMS key"
  value       = aws_kms_key.main.arn
}

output "kms_alias_name" {
  description = "Name of the KMS key alias"
  value       = aws_kms_alias.main.name
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = module.security.waf_web_acl_id
}

output "cloudtrail_arn" {
  description = "ARN of the CloudTrail"
  value       = module.security.cloudtrail_arn
}

output "config_configuration_recorder_name" {
  description = "Name of the AWS Config Configuration Recorder"
  value       = module.security.config_configuration_recorder_name
}

output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = module.security.guardduty_detector_id
}

# Compute Outputs
output "app_instance_ids" {
  description = "IDs of the application instances"
  value       = module.compute.instance_ids
}

output "app_instance_private_ips" {
  description = "Private IPs of the application instances"
  value       = module.compute.instance_private_ips
}

output "auto_scaling_group_arn" {
  description = "ARN of the Auto Scaling Group"
  value       = module.compute.auto_scaling_group_arn
}

output "auto_scaling_group_name" {
  description = "Name of the Auto Scaling Group"
  value       = module.compute.auto_scaling_group_name
}

output "launch_template_id" {
  description = "ID of the Launch Template"
  value       = module.compute.launch_template_id
}

output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = module.compute.load_balancer_arn
}

output "load_balancer_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.compute.load_balancer_dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = module.compute.load_balancer_zone_id
}

output "target_group_arn" {
  description = "ARN of the Target Group"
  value       = module.compute.target_group_arn
}

# Database Outputs
output "db_instance_id" {
  description = "ID of the RDS instance"
  value       = module.database.db_instance_id
}

output "db_instance_arn" {
  description = "ARN of the RDS instance"
  value       = module.database.db_instance_arn
}

output "db_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "db_port" {
  description = "Port of the RDS instance"
  value       = module.database.db_port
}

output "db_subnet_group_name" {
  description = "Name of the DB subnet group"
  value       = module.database.db_subnet_group_name
}

output "db_parameter_group_name" {
  description = "Name of the DB parameter group"
  value       = module.database.db_parameter_group_name
}

output "db_option_group_name" {
  description = "Name of the DB option group"
  value       = module.database.db_option_group_name
}

# Storage Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = module.storage.s3_bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.storage.s3_bucket_arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = module.storage.s3_bucket_domain_name
}

output "s3_bucket_regional_domain_name" {
  description = "Regional domain name of the S3 bucket"
  value       = module.storage.s3_bucket_regional_domain_name
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = module.storage.cloudfront_distribution_id
}

output "cloudfront_distribution_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = module.storage.cloudfront_distribution_domain_name
}

# Monitoring Outputs
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch Log Group"
  value       = module.monitoring.cloudwatch_log_group_name
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch Log Group"
  value       = module.monitoring.cloudwatch_log_group_arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = module.monitoring.cloudwatch_dashboard_url
}

# Secrets Management Outputs
output "secrets_manager_secret_arns" {
  description = "ARNs of the secrets stored in AWS Secrets Manager"
  value       = module.secrets.secret_arns
  sensitive   = true
}

output "parameter_store_parameter_arns" {
  description = "ARNs of the parameters stored in AWS Systems Manager Parameter Store"
  value       = module.secrets.parameter_arns
}

# Backup Outputs
output "backup_vault_arn" {
  description = "ARN of the AWS Backup vault"
  value       = module.backup.backup_vault_arn
}

output "backup_plan_arn" {
  description = "ARN of the AWS Backup plan"
  value       = module.backup.backup_plan_arn
}

output "backup_iam_role_arn" {
  description = "ARN of the AWS Backup IAM role"
  value       = module.backup.backup_iam_role_arn
}

# Compliance and Audit Outputs
output "compliance_report" {
  description = "Compliance status summary"
  value = {
    encryption_enabled     = true
    backup_enabled        = true
    monitoring_enabled    = true
    audit_logging_enabled = var.enable_cloudtrail
    config_enabled        = var.enable_config
    guardduty_enabled     = var.enable_guardduty
    waf_enabled          = var.enable_waf
    vpc_flow_logs_enabled = true
    multi_az_enabled     = var.db_multi_az
    kms_key_rotation_enabled = true
  }
}

# Environment Information
output "environment_info" {
  description = "Environment information and metadata"
  value = {
    environment           = var.environment
    app_name             = var.app_name
    aws_region           = var.aws_region
    deployment_timestamp = timestamp()
    terraform_version    = "~> 1.0"
    aws_provider_version = "~> 5.0"
  }
}
