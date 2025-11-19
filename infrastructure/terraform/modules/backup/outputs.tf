# AWS Backup Vault Outputs
output "backup_vault_name" {
  description = "Name of the backup vault"
  value       = aws_backup_vault.main.name
}

output "backup_vault_arn" {
  description = "ARN of the backup vault"
  value       = aws_backup_vault.main.arn
}

output "backup_vault_recovery_points" {
  description = "Number of recovery points in the backup vault"
  value       = aws_backup_vault.main.recovery_points
}

# AWS Backup Plan Outputs
output "backup_plan_id" {
  description = "ID of the backup plan"
  value       = aws_backup_plan.main.id
}

output "backup_plan_arn" {
  description = "ARN of the backup plan"
  value       = aws_backup_plan.main.arn
}

output "backup_plan_version" {
  description = "Version of the backup plan"
  value       = aws_backup_plan.main.version
}

# Backup Selection Outputs
output "rds_backup_selection_id" {
  description = "ID of the RDS backup selection"
  value       = var.rds_instance_arn != null ? aws_backup_selection.rds_backup[0].id : null
}

output "ebs_backup_selection_id" {
  description = "ID of the EBS backup selection"
  value       = length(var.ebs_volume_arns) > 0 ? aws_backup_selection.ebs_backup[0].id : null
}

output "s3_backup_selection_id" {
  description = "ID of the S3 backup selection"
  value       = length(var.s3_bucket_arns) > 0 ? aws_backup_selection.s3_backup[0].id : null
}

output "efs_backup_selection_id" {
  description = "ID of the EFS backup selection"
  value       = length(var.efs_file_system_arns) > 0 ? aws_backup_selection.efs_backup[0].id : null
}

# IAM Role Outputs
output "backup_role_arn" {
  description = "ARN of the backup service IAM role"
  value       = aws_iam_role.backup_role.arn
}

output "backup_role_name" {
  description = "Name of the backup service IAM role"
  value       = aws_iam_role.backup_role.name
}

output "backup_validator_role_arn" {
  description = "ARN of the backup validator Lambda IAM role"
  value       = var.enable_backup_validation ? aws_iam_role.backup_validator_role[0].arn : null
}

# CloudWatch Alarm Outputs
output "backup_job_failed_alarm_arn" {
  description = "ARN of the backup job failed alarm"
  value       = aws_cloudwatch_metric_alarm.backup_job_failed.arn
}

output "backup_job_expired_alarm_arn" {
  description = "ARN of the backup job expired alarm"
  value       = aws_cloudwatch_metric_alarm.backup_job_expired.arn
}

# EventBridge Rule Outputs
output "backup_job_state_change_rule_arn" {
  description = "ARN of the backup job state change EventBridge rule"
  value       = aws_cloudwatch_event_rule.backup_job_state_change.arn
}

output "backup_validation_schedule_rule_arn" {
  description = "ARN of the backup validation schedule EventBridge rule"
  value       = var.enable_backup_validation ? aws_cloudwatch_event_rule.backup_validation_schedule[0].arn : null
}

# Lambda Function Outputs
output "backup_validator_function_arn" {
  description = "ARN of the backup validator Lambda function"
  value       = var.enable_backup_validation ? aws_lambda_function.backup_validator[0].arn : null
}

output "backup_validator_function_name" {
  description = "Name of the backup validator Lambda function"
  value       = var.enable_backup_validation ? aws_lambda_function.backup_validator[0].function_name : null
}

# S3 Bucket Outputs
output "backup_reports_bucket_name" {
  description = "Name of the backup reports S3 bucket"
  value       = var.enable_backup_reports ? aws_s3_bucket.backup_reports[0].bucket : null
}

output "backup_reports_bucket_arn" {
  description = "ARN of the backup reports S3 bucket"
  value       = var.enable_backup_reports ? aws_s3_bucket.backup_reports[0].arn : null
}

# Disaster Recovery Documentation
output "disaster_recovery_runbook_path" {
  description = "Path to the disaster recovery runbook"
  value       = var.create_dr_documentation ? local_file.disaster_recovery_runbook[0].filename : null
}

# Backup Configuration Summary
output "backup_summary" {
  description = "Summary of backup configuration"
  value = {
    backup_vault_name           = aws_backup_vault.main.name
    backup_plan_id             = aws_backup_plan.main.id
    daily_backup_enabled       = true
    weekly_backup_enabled      = true
    monthly_backup_enabled     = true
    cross_region_backup_enabled = var.enable_cross_region_backup
    backup_validation_enabled  = var.enable_backup_validation
    backup_reports_enabled     = var.enable_backup_reports
    backup_monitoring_enabled  = var.enable_backup_monitoring
    encryption_enabled         = var.enable_backup_encryption
    point_in_time_recovery     = var.enable_point_in_time_recovery
    compliance_reporting       = var.enable_compliance_reporting
    cost_optimization_enabled  = var.enable_cost_optimization
    rds_backup_configured      = var.rds_instance_arn != null
    ebs_backup_configured      = length(var.ebs_volume_arns) > 0
    s3_backup_configured       = length(var.s3_bucket_arns) > 0
    efs_backup_configured      = length(var.efs_file_system_arns) > 0
  }
}

# Backup Schedules
output "backup_schedules" {
  description = "Backup schedule configuration"
  value = {
    daily_schedule   = var.daily_backup_schedule
    weekly_schedule  = var.weekly_backup_schedule
    monthly_schedule = var.monthly_backup_schedule
    validation_schedule = var.backup_validation_schedule
  }
}

# Retention Policies
output "retention_policies" {
  description = "Backup retention policy configuration"
  value = {
    daily_retention_days   = var.daily_backup_retention_days
    weekly_retention_days  = var.weekly_backup_retention_days
    monthly_retention_days = var.monthly_backup_retention_days
    cold_storage_after_days = var.cold_storage_after_days
  }
}

# Recovery Objectives
output "recovery_objectives" {
  description = "Recovery Time and Point Objectives"
  value = {
    rto_target_hours = var.rto_target_hours
    rpo_target_hours = var.rpo_target_hours
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance status indicators for backup"
  value = {
    encryption_enabled          = var.enable_backup_encryption
    cross_region_backup        = var.enable_cross_region_backup
    automated_backup_validation = var.enable_backup_validation
    audit_logging              = var.enable_backup_reports
    compliance_frameworks      = var.compliance_frameworks
    long_term_retention        = var.monthly_backup_retention_days >= 2555
    point_in_time_recovery     = var.enable_point_in_time_recovery
    disaster_recovery_plan     = var.create_dr_documentation
    monitoring_and_alerting    = var.enable_backup_monitoring
    cost_management           = var.enable_cost_optimization
  }
}

# Security Features
output "security_features" {
  description = "Security features enabled for backup"
  value = {
    kms_encryption             = true
    cross_region_replication   = var.enable_cross_region_backup
    access_control_iam         = true
    backup_vault_encryption    = true
    secure_backup_storage      = true
    automated_validation       = var.enable_backup_validation
    audit_trail               = var.enable_backup_reports
    monitoring_alerts         = var.enable_backup_monitoring
  }
}

# Cost Information
output "cost_information" {
  description = "Cost-related information for backup"
  value = {
    cost_optimization_enabled = var.enable_cost_optimization
    monthly_budget_usd       = var.backup_cost_budget_usd
    cold_storage_transition  = var.cold_storage_after_days
    lifecycle_management     = true
    storage_class_optimization = true
  }
}

# Operational Information
output "operational_information" {
  description = "Operational information for backup management"
  value = {
    backup_window_start_hour    = var.backup_window_start_hour
    backup_window_duration_hours = var.backup_window_duration_hours
    automated_validation_enabled = var.enable_backup_validation
    reporting_enabled           = var.enable_backup_reports
    monitoring_enabled          = var.enable_backup_monitoring
    disaster_recovery_documented = var.create_dr_documentation
  }
}
