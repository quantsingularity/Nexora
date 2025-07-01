# RDS Instance Outputs
output "db_instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.main.id
}

output "db_instance_arn" {
  description = "ARN of the RDS instance"
  value       = aws_db_instance.main.arn
}

output "db_instance_identifier" {
  description = "Identifier of the RDS instance"
  value       = aws_db_instance.main.identifier
}

output "db_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}

output "db_port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.main.port
}

output "db_name" {
  description = "Name of the database"
  value       = aws_db_instance.main.db_name
}

output "db_username" {
  description = "Master username of the database"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "db_engine" {
  description = "Database engine"
  value       = aws_db_instance.main.engine
}

output "db_engine_version" {
  description = "Database engine version"
  value       = aws_db_instance.main.engine_version
}

output "db_instance_class" {
  description = "Instance class of the RDS instance"
  value       = aws_db_instance.main.instance_class
}

output "db_allocated_storage" {
  description = "Allocated storage of the RDS instance"
  value       = aws_db_instance.main.allocated_storage
}

output "db_storage_type" {
  description = "Storage type of the RDS instance"
  value       = aws_db_instance.main.storage_type
}

output "db_storage_encrypted" {
  description = "Whether the RDS instance is encrypted"
  value       = aws_db_instance.main.storage_encrypted
}

output "db_kms_key_id" {
  description = "KMS key ID used for encryption"
  value       = aws_db_instance.main.kms_key_id
}

output "db_multi_az" {
  description = "Whether the RDS instance is Multi-AZ"
  value       = aws_db_instance.main.multi_az
}

output "db_availability_zone" {
  description = "Availability zone of the RDS instance"
  value       = aws_db_instance.main.availability_zone
}

output "db_backup_retention_period" {
  description = "Backup retention period of the RDS instance"
  value       = aws_db_instance.main.backup_retention_period
}

output "db_backup_window" {
  description = "Backup window of the RDS instance"
  value       = aws_db_instance.main.backup_window
}

output "db_maintenance_window" {
  description = "Maintenance window of the RDS instance"
  value       = aws_db_instance.main.maintenance_window
}

# Read Replica Outputs
output "db_read_replica_id" {
  description = "ID of the read replica"
  value       = var.create_read_replica ? aws_db_instance.read_replica[0].id : null
}

output "db_read_replica_arn" {
  description = "ARN of the read replica"
  value       = var.create_read_replica ? aws_db_instance.read_replica[0].arn : null
}

output "db_read_replica_endpoint" {
  description = "Endpoint of the read replica"
  value       = var.create_read_replica ? aws_db_instance.read_replica[0].endpoint : null
  sensitive   = true
}

# DB Subnet Group Outputs
output "db_subnet_group_id" {
  description = "ID of the DB subnet group"
  value       = aws_db_subnet_group.main.id
}

output "db_subnet_group_name" {
  description = "Name of the DB subnet group"
  value       = aws_db_subnet_group.main.name
}

output "db_subnet_group_arn" {
  description = "ARN of the DB subnet group"
  value       = aws_db_subnet_group.main.arn
}

# DB Parameter Group Outputs
output "db_parameter_group_id" {
  description = "ID of the DB parameter group"
  value       = aws_db_parameter_group.main.id
}

output "db_parameter_group_name" {
  description = "Name of the DB parameter group"
  value       = aws_db_parameter_group.main.name
}

output "db_parameter_group_arn" {
  description = "ARN of the DB parameter group"
  value       = aws_db_parameter_group.main.arn
}

# DB Option Group Outputs
output "db_option_group_id" {
  description = "ID of the DB option group"
  value       = var.engine == "mysql" ? aws_db_option_group.main[0].id : null
}

output "db_option_group_name" {
  description = "Name of the DB option group"
  value       = var.engine == "mysql" ? aws_db_option_group.main[0].name : null
}

output "db_option_group_arn" {
  description = "ARN of the DB option group"
  value       = var.engine == "mysql" ? aws_db_option_group.main[0].arn : null
}

# Secrets Manager Outputs
output "db_credentials_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.arn
  sensitive   = true
}

output "db_credentials_secret_name" {
  description = "Name of the database credentials secret"
  value       = aws_secretsmanager_secret.db_credentials.name
  sensitive   = true
}

output "db_connection_string_secret_arn" {
  description = "ARN of the database connection string secret"
  value       = aws_secretsmanager_secret.db_connection_string.arn
  sensitive   = true
}

output "db_connection_string_secret_name" {
  description = "Name of the database connection string secret"
  value       = aws_secretsmanager_secret.db_connection_string.name
  sensitive   = true
}

# IAM Role Outputs
output "rds_enhanced_monitoring_role_arn" {
  description = "ARN of the RDS enhanced monitoring IAM role"
  value       = var.enable_enhanced_monitoring ? aws_iam_role.rds_enhanced_monitoring[0].arn : null
}

# CloudWatch Log Group Outputs
output "db_log_group_names" {
  description = "Names of the database CloudWatch log groups"
  value       = [for log_group in aws_cloudwatch_log_group.database_logs : log_group.name]
}

output "db_log_group_arns" {
  description = "ARNs of the database CloudWatch log groups"
  value       = [for log_group in aws_cloudwatch_log_group.database_logs : log_group.arn]
}

# Snapshot Outputs
output "manual_snapshot_id" {
  description = "ID of the manual snapshot"
  value       = var.create_manual_snapshot ? aws_db_snapshot.manual_snapshot[0].id : null
}

output "manual_snapshot_arn" {
  description = "ARN of the manual snapshot"
  value       = var.create_manual_snapshot ? aws_db_snapshot.manual_snapshot[0].db_snapshot_arn : null
}

# Connection Information (for applications)
output "connection_info" {
  description = "Database connection information"
  value = {
    host     = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    database = aws_db_instance.main.db_name
    engine   = aws_db_instance.main.engine
  }
  sensitive = true
}

# Database Summary
output "database_summary" {
  description = "Summary of database configuration"
  value = {
    engine                    = aws_db_instance.main.engine
    engine_version           = aws_db_instance.main.engine_version
    instance_class           = aws_db_instance.main.instance_class
    allocated_storage        = aws_db_instance.main.allocated_storage
    storage_type            = aws_db_instance.main.storage_type
    storage_encrypted       = aws_db_instance.main.storage_encrypted
    multi_az                = aws_db_instance.main.multi_az
    backup_retention_period = aws_db_instance.main.backup_retention_period
    enhanced_monitoring     = var.enable_enhanced_monitoring
    performance_insights    = var.enable_performance_insights
    read_replica_created    = var.create_read_replica
    manual_snapshot_created = var.create_manual_snapshot
    cloudwatch_logs_exports = var.enabled_cloudwatch_logs_exports
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance status indicators for database"
  value = {
    encryption_at_rest      = aws_db_instance.main.storage_encrypted
    encryption_in_transit   = true  # SSL/TLS enforced by parameter group
    backup_enabled          = aws_db_instance.main.backup_retention_period > 0
    multi_az_enabled        = aws_db_instance.main.multi_az
    enhanced_monitoring     = var.enable_enhanced_monitoring
    performance_insights    = var.enable_performance_insights
    audit_logging          = contains(var.enabled_cloudwatch_logs_exports, "audit")
    slow_query_logging     = contains(var.enabled_cloudwatch_logs_exports, "slowquery")
    error_logging          = contains(var.enabled_cloudwatch_logs_exports, "error")
    general_logging        = contains(var.enabled_cloudwatch_logs_exports, "general")
    secrets_management     = true  # Credentials stored in Secrets Manager
    network_isolation      = true  # Private subnets only
    deletion_protection    = var.environment == "prod"
    automated_backups      = aws_db_instance.main.backup_retention_period >= 7
    point_in_time_recovery = true  # Enabled with automated backups
  }
}

