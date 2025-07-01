# Security Group Outputs
output "alb_security_group_id" {
  description = "ID of the Application Load Balancer security group"
  value       = aws_security_group.alb.id
}

output "alb_security_group_arn" {
  description = "ARN of the Application Load Balancer security group"
  value       = aws_security_group.alb.arn
}

output "app_security_group_id" {
  description = "ID of the application security group"
  value       = aws_security_group.app.id
}

output "app_security_group_arn" {
  description = "ARN of the application security group"
  value       = aws_security_group.app.arn
}

output "db_security_group_id" {
  description = "ID of the database security group"
  value       = aws_security_group.db.id
}

output "db_security_group_arn" {
  description = "ARN of the database security group"
  value       = aws_security_group.db.arn
}

output "bastion_security_group_id" {
  description = "ID of the bastion host security group"
  value       = var.enable_bastion_host ? aws_security_group.bastion[0].id : null
}

output "bastion_security_group_arn" {
  description = "ARN of the bastion host security group"
  value       = var.enable_bastion_host ? aws_security_group.bastion[0].arn : null
}

# WAF Outputs
output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].id : null
}

output "waf_web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].arn : null
}

output "waf_web_acl_capacity" {
  description = "Capacity units consumed by the WAF Web ACL"
  value       = var.enable_waf ? aws_wafv2_web_acl.main[0].capacity : null
}

# CloudTrail Outputs
output "cloudtrail_arn" {
  description = "ARN of the CloudTrail"
  value       = var.enable_cloudtrail ? aws_cloudtrail.main[0].arn : null
}

output "cloudtrail_home_region" {
  description = "Home region of the CloudTrail"
  value       = var.enable_cloudtrail ? aws_cloudtrail.main[0].home_region : null
}

output "cloudtrail_s3_bucket_name" {
  description = "Name of the S3 bucket for CloudTrail logs"
  value       = var.enable_cloudtrail ? aws_s3_bucket.cloudtrail_logs[0].bucket : null
}

output "cloudtrail_s3_bucket_arn" {
  description = "ARN of the S3 bucket for CloudTrail logs"
  value       = var.enable_cloudtrail ? aws_s3_bucket.cloudtrail_logs[0].arn : null
}

# AWS Config Outputs
output "config_configuration_recorder_name" {
  description = "Name of the AWS Config Configuration Recorder"
  value       = var.enable_config ? aws_config_configuration_recorder.main[0].name : null
}

output "config_delivery_channel_name" {
  description = "Name of the AWS Config Delivery Channel"
  value       = var.enable_config ? aws_config_delivery_channel.main[0].name : null
}

output "config_s3_bucket_name" {
  description = "Name of the S3 bucket for AWS Config logs"
  value       = var.enable_config ? aws_s3_bucket.config_logs[0].bucket : null
}

output "config_s3_bucket_arn" {
  description = "ARN of the S3 bucket for AWS Config logs"
  value       = var.enable_config ? aws_s3_bucket.config_logs[0].arn : null
}

output "config_iam_role_arn" {
  description = "ARN of the AWS Config IAM role"
  value       = var.enable_config ? aws_iam_role.config[0].arn : null
}

# GuardDuty Outputs
output "guardduty_detector_id" {
  description = "ID of the GuardDuty detector"
  value       = var.enable_guardduty ? aws_guardduty_detector.main[0].id : null
}

output "guardduty_detector_arn" {
  description = "ARN of the GuardDuty detector"
  value       = var.enable_guardduty ? aws_guardduty_detector.main[0].arn : null
}

# Inspector Outputs
output "inspector_enabler_account_ids" {
  description = "Account IDs where Inspector is enabled"
  value       = var.enable_inspector ? aws_inspector2_enabler.main[0].account_ids : null
}

output "inspector_enabler_resource_types" {
  description = "Resource types enabled for Inspector"
  value       = var.enable_inspector ? aws_inspector2_enabler.main[0].resource_types : null
}

# Shield Outputs
output "shield_protection_id" {
  description = "ID of the Shield protection"
  value       = var.enable_shield ? aws_shield_protection.main[0].id : null
}

output "shield_protection_name" {
  description = "Name of the Shield protection"
  value       = var.enable_shield ? aws_shield_protection.main[0].name : null
}

# Security Summary
output "security_summary" {
  description = "Summary of security configurations"
  value = {
    waf_enabled           = var.enable_waf
    shield_enabled        = var.enable_shield
    cloudtrail_enabled    = var.enable_cloudtrail
    config_enabled        = var.enable_config
    guardduty_enabled     = var.enable_guardduty
    inspector_enabled     = var.enable_inspector
    bastion_host_enabled  = var.enable_bastion_host
    ssh_access_enabled    = var.enable_ssh_access
    db_admin_access_enabled = var.enable_db_admin_access
    geo_blocking_enabled  = var.enable_geo_blocking
    waf_rate_limit       = var.waf_rate_limit
    cloudtrail_retention_days = var.cloudtrail_retention_days
    config_retention_days = var.config_retention_days
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance status indicators"
  value = {
    audit_logging_enabled     = var.enable_cloudtrail
    configuration_monitoring  = var.enable_config
    threat_detection_enabled  = var.enable_guardduty
    vulnerability_scanning    = var.enable_inspector
    web_application_firewall  = var.enable_waf
    ddos_protection          = var.enable_shield
    network_segmentation     = true  # Implemented via security groups
    encryption_in_transit    = true  # HTTPS enforced
    access_controls          = true  # Security groups and NACLs
    incident_response_ready  = var.enable_guardduty && var.enable_cloudtrail
  }
}

