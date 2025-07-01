# Secrets Manager Secret ARNs
output "database_credentials_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.database_credentials.arn
  sensitive   = true
}

output "database_credentials_secret_name" {
  description = "Name of the database credentials secret"
  value       = aws_secretsmanager_secret.database_credentials.name
  sensitive   = true
}

output "app_secrets_arns" {
  description = "Map of application secret ARNs"
  value       = { for k, v in aws_secretsmanager_secret.app_secrets : k => v.arn }
  sensitive   = true
}

output "app_secrets_names" {
  description = "Map of application secret names"
  value       = { for k, v in aws_secretsmanager_secret.app_secrets : k => v.name }
  sensitive   = true
}

output "api_keys_secret_arn" {
  description = "ARN of the API keys secret"
  value       = length(var.api_keys) > 0 ? aws_secretsmanager_secret.api_keys[0].arn : null
  sensitive   = true
}

output "api_keys_secret_name" {
  description = "Name of the API keys secret"
  value       = length(var.api_keys) > 0 ? aws_secretsmanager_secret.api_keys[0].name : null
  sensitive   = true
}

output "ssl_certificates_secret_arn" {
  description = "ARN of the SSL certificates secret"
  value       = length(var.ssl_certificates) > 0 ? aws_secretsmanager_secret.ssl_certificates[0].arn : null
  sensitive   = true
}

output "ssl_certificates_secret_name" {
  description = "Name of the SSL certificates secret"
  value       = length(var.ssl_certificates) > 0 ? aws_secretsmanager_secret.ssl_certificates[0].name : null
  sensitive   = true
}

output "jwt_keys_secret_arn" {
  description = "ARN of the JWT keys secret"
  value       = var.enable_jwt_secrets ? aws_secretsmanager_secret.jwt_keys[0].arn : null
  sensitive   = true
}

output "jwt_keys_secret_name" {
  description = "Name of the JWT keys secret"
  value       = var.enable_jwt_secrets ? aws_secretsmanager_secret.jwt_keys[0].name : null
  sensitive   = true
}

output "encryption_keys_secret_arn" {
  description = "ARN of the application encryption keys secret"
  value       = var.enable_app_encryption_keys ? aws_secretsmanager_secret.encryption_keys[0].arn : null
  sensitive   = true
}

output "encryption_keys_secret_name" {
  description = "Name of the application encryption keys secret"
  value       = var.enable_app_encryption_keys ? aws_secretsmanager_secret.encryption_keys[0].name : null
  sensitive   = true
}

# All Secret ARNs (for convenience)
output "secret_arns" {
  description = "List of all secret ARNs"
  value = compact(concat(
    [aws_secretsmanager_secret.database_credentials.arn],
    values(aws_secretsmanager_secret.app_secrets)[*].arn,
    length(var.api_keys) > 0 ? [aws_secretsmanager_secret.api_keys[0].arn] : [],
    length(var.ssl_certificates) > 0 ? [aws_secretsmanager_secret.ssl_certificates[0].arn] : [],
    var.enable_jwt_secrets ? [aws_secretsmanager_secret.jwt_keys[0].arn] : [],
    var.enable_app_encryption_keys ? [aws_secretsmanager_secret.encryption_keys[0].arn] : []
  ))
  sensitive = true
}

# SSM Parameter Store Parameter ARNs
output "app_config_parameter_arns" {
  description = "Map of application configuration parameter ARNs"
  value       = { for k, v in aws_ssm_parameter.app_config : k => v.arn }
}

output "app_config_parameter_names" {
  description = "Map of application configuration parameter names"
  value       = { for k, v in aws_ssm_parameter.app_config : k => v.name }
}

output "secure_config_parameter_arns" {
  description = "Map of secure configuration parameter ARNs"
  value       = { for k, v in aws_ssm_parameter.secure_config : k => v.arn }
  sensitive   = true
}

output "secure_config_parameter_names" {
  description = "Map of secure configuration parameter names"
  value       = { for k, v in aws_ssm_parameter.secure_config : k => v.name }
  sensitive   = true
}

# All Parameter ARNs (for convenience)
output "parameter_arns" {
  description = "List of all SSM parameter ARNs"
  value = concat(
    values(aws_ssm_parameter.app_config)[*].arn,
    values(aws_ssm_parameter.secure_config)[*].arn
  )
}

# IAM Role and Policy Outputs
output "secrets_access_role_arn" {
  description = "ARN of the secrets access IAM role"
  value       = aws_iam_role.secrets_access_role.arn
}

output "secrets_access_role_name" {
  description = "Name of the secrets access IAM role"
  value       = aws_iam_role.secrets_access_role.name
}

output "secrets_access_instance_profile_arn" {
  description = "ARN of the secrets access instance profile"
  value       = aws_iam_instance_profile.secrets_access_profile.arn
}

output "secrets_access_instance_profile_name" {
  description = "Name of the secrets access instance profile"
  value       = aws_iam_instance_profile.secrets_access_profile.name
}

# Monitoring and Audit Outputs
output "secrets_audit_log_group_name" {
  description = "Name of the secrets audit log group"
  value       = aws_cloudwatch_log_group.secrets_audit.name
}

output "secrets_audit_log_group_arn" {
  description = "ARN of the secrets audit log group"
  value       = aws_cloudwatch_log_group.secrets_audit.arn
}

output "secrets_access_event_rule_arn" {
  description = "ARN of the secrets access EventBridge rule"
  value       = aws_cloudwatch_event_rule.secrets_access.arn
}

# Backup Outputs
output "secrets_backup_bucket_name" {
  description = "Name of the secrets backup S3 bucket"
  value       = var.enable_secrets_backup ? aws_s3_bucket.secrets_backup[0].bucket : null
}

output "secrets_backup_bucket_arn" {
  description = "ARN of the secrets backup S3 bucket"
  value       = var.enable_secrets_backup ? aws_s3_bucket.secrets_backup[0].arn : null
}

# Secret Rotation Outputs
output "database_credentials_rotation_enabled" {
  description = "Whether database credentials rotation is enabled"
  value       = var.enable_secret_rotation
}

output "rotation_interval_days" {
  description = "Secret rotation interval in days"
  value       = var.rotation_interval_days
}

# Secrets Management Summary
output "secrets_summary" {
  description = "Summary of secrets management configuration"
  value = {
    total_secrets_count           = length(compact(concat(
      [aws_secretsmanager_secret.database_credentials.arn],
      values(aws_secretsmanager_secret.app_secrets)[*].arn,
      length(var.api_keys) > 0 ? [aws_secretsmanager_secret.api_keys[0].arn] : [],
      length(var.ssl_certificates) > 0 ? [aws_secretsmanager_secret.ssl_certificates[0].arn] : [],
      var.enable_jwt_secrets ? [aws_secretsmanager_secret.jwt_keys[0].arn] : [],
      var.enable_app_encryption_keys ? [aws_secretsmanager_secret.encryption_keys[0].arn] : []
    )))
    total_parameters_count        = length(aws_ssm_parameter.app_config) + length(aws_ssm_parameter.secure_config)
    database_credentials_managed  = true
    app_secrets_count            = length(var.app_secrets)
    api_keys_managed             = length(var.api_keys) > 0
    ssl_certificates_managed     = length(var.ssl_certificates) > 0
    jwt_keys_enabled             = var.enable_jwt_secrets
    app_encryption_keys_enabled  = var.enable_app_encryption_keys
    secret_rotation_enabled      = var.enable_secret_rotation
    secrets_backup_enabled       = var.enable_secrets_backup
    access_monitoring_enabled    = var.enable_access_monitoring
    compliance_monitoring_enabled = var.enable_compliance_monitoring
    kms_encryption_enabled       = true
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance status indicators for secrets management"
  value = {
    encryption_at_rest           = true  # All secrets encrypted with KMS
    access_control_implemented   = true  # IAM roles and policies
    audit_logging_enabled        = var.enable_access_monitoring
    secret_rotation_available    = var.enable_secret_rotation
    backup_and_recovery         = var.enable_secrets_backup
    cross_region_replication    = var.enable_cross_region_replication
    compliance_frameworks_supported = var.compliance_frameworks
    least_privilege_access      = true  # Specific IAM policies
    secure_storage              = true  # AWS Secrets Manager and SSM
    automated_monitoring        = var.enable_access_monitoring
    disaster_recovery_ready     = var.enable_secrets_backup || var.enable_cross_region_replication
  }
}

# Security Features
output "security_features" {
  description = "Security features enabled for secrets management"
  value = {
    kms_encryption              = true
    secrets_manager_integration = true
    ssm_parameter_store        = true
    iam_role_based_access      = true
    cloudwatch_audit_logging   = var.enable_access_monitoring
    eventbridge_monitoring     = var.enable_access_monitoring
    automatic_rotation         = var.enable_secret_rotation
    backup_encryption          = var.enable_secrets_backup
    cross_region_backup        = var.enable_cross_region_replication
    compliance_monitoring      = var.enable_compliance_monitoring
  }
}

# Access Information for Applications
output "access_information" {
  description = "Information for applications to access secrets"
  value = {
    iam_role_arn               = aws_iam_role.secrets_access_role.arn
    instance_profile_name      = aws_iam_instance_profile.secrets_access_profile.name
    secrets_path_prefix        = "/${var.app_name}/${var.environment}/"
    config_path_prefix         = "/${var.app_name}/${var.environment}/config/"
    secure_config_path_prefix  = "/${var.app_name}/${var.environment}/secure-config/"
    kms_key_id                = var.kms_key_id
  }
  sensitive = true
}

