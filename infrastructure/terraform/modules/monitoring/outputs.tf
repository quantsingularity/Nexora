# CloudWatch Log Group Outputs
output "app_log_group_name" {
  description = "Name of the application log group"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "app_log_group_arn" {
  description = "ARN of the application log group"
  value       = aws_cloudwatch_log_group.app_logs.arn
}

output "system_log_group_name" {
  description = "Name of the system log group"
  value       = aws_cloudwatch_log_group.system_logs.name
}

output "system_log_group_arn" {
  description = "ARN of the system log group"
  value       = aws_cloudwatch_log_group.system_logs.arn
}

output "security_log_group_name" {
  description = "Name of the security log group"
  value       = aws_cloudwatch_log_group.security_logs.name
}

output "security_log_group_arn" {
  description = "ARN of the security log group"
  value       = aws_cloudwatch_log_group.security_logs.arn
}

output "audit_log_group_name" {
  description = "Name of the audit log group"
  value       = aws_cloudwatch_log_group.audit_logs.name
}

output "audit_log_group_arn" {
  description = "ARN of the audit log group"
  value       = aws_cloudwatch_log_group.audit_logs.arn
}

output "cloudwatch_log_group_name" {
  description = "Primary CloudWatch log group name (for backward compatibility)"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "cloudwatch_log_group_arn" {
  description = "Primary CloudWatch log group ARN (for backward compatibility)"
  value       = aws_cloudwatch_log_group.app_logs.arn
}

# SNS Topic Outputs
output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.name
}

# CloudWatch Dashboard Outputs
output "cloudwatch_dashboard_url" {
  description = "URL of the CloudWatch dashboard"
  value       = "https://console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

# CloudWatch Alarm Outputs
output "alb_response_time_alarm_arn" {
  description = "ARN of the ALB response time alarm"
  value       = var.load_balancer_arn != null ? aws_cloudwatch_metric_alarm.alb_response_time[0].arn : null
}

output "alb_5xx_errors_alarm_arn" {
  description = "ARN of the ALB 5XX errors alarm"
  value       = var.load_balancer_arn != null ? aws_cloudwatch_metric_alarm.alb_5xx_errors[0].arn : null
}

output "rds_cpu_alarm_arn" {
  description = "ARN of the RDS CPU alarm"
  value       = var.rds_instance_id != null ? aws_cloudwatch_metric_alarm.rds_cpu[0].arn : null
}

output "rds_connections_alarm_arn" {
  description = "ARN of the RDS connections alarm"
  value       = var.rds_instance_id != null ? aws_cloudwatch_metric_alarm.rds_connections[0].arn : null
}

output "failed_logins_alarm_arn" {
  description = "ARN of the failed logins alarm"
  value       = aws_cloudwatch_metric_alarm.failed_logins.arn
}

output "application_errors_alarm_arn" {
  description = "ARN of the application errors alarm"
  value       = aws_cloudwatch_metric_alarm.application_errors.arn
}

# EventBridge Rule Outputs
output "guardduty_findings_rule_arn" {
  description = "ARN of the GuardDuty findings EventBridge rule"
  value       = aws_cloudwatch_event_rule.guardduty_findings.arn
}

output "config_compliance_rule_arn" {
  description = "ARN of the Config compliance EventBridge rule"
  value       = aws_cloudwatch_event_rule.config_compliance.arn
}

# Log Metric Filter Outputs
output "failed_ssh_logins_filter_name" {
  description = "Name of the failed SSH logins metric filter"
  value       = aws_cloudwatch_log_metric_filter.failed_ssh_logins.name
}

output "root_access_filter_name" {
  description = "Name of the root access metric filter"
  value       = aws_cloudwatch_log_metric_filter.root_access.name
}

output "application_errors_filter_name" {
  description = "Name of the application errors metric filter"
  value       = aws_cloudwatch_log_metric_filter.application_errors.name
}

# CloudWatch Insights Query Outputs
output "error_analysis_query_name" {
  description = "Name of the error analysis CloudWatch Insights query"
  value       = aws_cloudwatch_query_definition.error_analysis.name
}

output "performance_analysis_query_name" {
  description = "Name of the performance analysis CloudWatch Insights query"
  value       = aws_cloudwatch_query_definition.performance_analysis.name
}

# X-Ray Outputs
output "xray_sampling_rule_name" {
  description = "Name of the X-Ray sampling rule"
  value       = var.enable_xray_tracing ? aws_xray_sampling_rule.main[0].rule_name : null
}

output "xray_sampling_rule_arn" {
  description = "ARN of the X-Ray sampling rule"
  value       = var.enable_xray_tracing ? aws_xray_sampling_rule.main[0].arn : null
}

# Monitoring Summary
output "monitoring_summary" {
  description = "Summary of monitoring configuration"
  value = {
    log_groups_created        = 4
    sns_topic_created        = true
    dashboard_created        = true
    alarms_created           = 6
    metric_filters_created   = 3
    eventbridge_rules_created = 2
    insights_queries_created = 2
    xray_tracing_enabled     = var.enable_xray_tracing
    detailed_monitoring      = var.enable_detailed_monitoring
    security_monitoring      = var.enable_security_monitoring
    compliance_monitoring    = var.enable_compliance_monitoring
    log_retention_days       = var.log_retention_days
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance status indicators for monitoring"
  value = {
    centralized_logging      = true
    log_encryption          = true
    audit_trail_enabled     = true
    security_monitoring     = var.enable_security_monitoring
    compliance_monitoring   = var.enable_compliance_monitoring
    alerting_configured     = length(var.alert_email_endpoints) > 0
    dashboard_available     = var.enable_dashboard
    log_retention_compliant = var.log_retention_days >= 365
    real_time_monitoring    = true
    automated_responses     = true
  }
}

