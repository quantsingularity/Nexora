# Core Configuration
variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "app_name" {
  description = "Application name for resource naming and tagging"
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.app_name))
    error_message = "App name must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}

variable "kms_key_arn" {
  description = "KMS key ARN for backup encryption"
  type        = string
}

# Backup Schedule Configuration
variable "daily_backup_schedule" {
  description = "Cron expression for daily backups"
  type        = string
  default     = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC
}

variable "weekly_backup_schedule" {
  description = "Cron expression for weekly backups"
  type        = string
  default     = "cron(0 3 ? * SUN *)"  # Weekly on Sunday at 3 AM UTC
}

variable "monthly_backup_schedule" {
  description = "Cron expression for monthly backups"
  type        = string
  default     = "cron(0 4 1 * ? *)"  # Monthly on 1st at 4 AM UTC
}

# Backup Retention Configuration
variable "daily_backup_retention_days" {
  description = "Retention period for daily backups in days"
  type        = number
  default     = 30

  validation {
    condition     = var.daily_backup_retention_days >= 7
    error_message = "Daily backup retention must be at least 7 days."
  }
}

variable "weekly_backup_retention_days" {
  description = "Retention period for weekly backups in days"
  type        = number
  default     = 90

  validation {
    condition     = var.weekly_backup_retention_days >= 30
    error_message = "Weekly backup retention must be at least 30 days."
  }
}

variable "monthly_backup_retention_days" {
  description = "Retention period for monthly backups in days"
  type        = number
  default     = 2555  # 7 years for financial compliance

  validation {
    condition     = var.monthly_backup_retention_days >= 365
    error_message = "Monthly backup retention must be at least 365 days."
  }
}

variable "cold_storage_after_days" {
  description = "Days after which backups are moved to cold storage"
  type        = number
  default     = 30

  validation {
    condition     = var.cold_storage_after_days >= 30
    error_message = "Cold storage transition must be at least 30 days."
  }
}

# Resource ARNs for Backup
variable "rds_instance_arn" {
  description = "ARN of the RDS instance to backup"
  type        = string
  default     = null
}

variable "ebs_volume_arns" {
  description = "List of EBS volume ARNs to backup"
  type        = list(string)
  default     = []
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs to backup"
  type        = list(string)
  default     = []
}

variable "efs_file_system_arns" {
  description = "List of EFS file system ARNs to backup"
  type        = list(string)
  default     = []
}

# Cross-Region Backup Configuration
variable "cross_region_backup_vault_arn" {
  description = "ARN of the cross-region backup vault for disaster recovery"
  type        = string
  default     = null
}

variable "enable_cross_region_backup" {
  description = "Enable cross-region backup for disaster recovery"
  type        = bool
  default     = true
}

# Monitoring and Alerting
variable "sns_topic_arn" {
  description = "SNS topic ARN for backup alerts"
  type        = string
  default     = null
}

variable "enable_backup_monitoring" {
  description = "Enable backup job monitoring and alerting"
  type        = bool
  default     = true
}

# Backup Validation and Reporting
variable "enable_backup_validation" {
  description = "Enable automated backup validation"
  type        = bool
  default     = true
}

variable "enable_backup_reports" {
  description = "Enable backup reporting to S3"
  type        = bool
  default     = true
}

variable "backup_validation_schedule" {
  description = "Cron expression for backup validation"
  type        = string
  default     = "cron(0 6 * * ? *)"  # Daily at 6 AM UTC
}

# Disaster Recovery Configuration
variable "create_dr_documentation" {
  description = "Create disaster recovery documentation"
  type        = bool
  default     = true
}

variable "rto_target_hours" {
  description = "Recovery Time Objective target in hours"
  type        = number
  default     = 4

  validation {
    condition     = var.rto_target_hours > 0
    error_message = "RTO target must be positive."
  }
}

variable "rpo_target_hours" {
  description = "Recovery Point Objective target in hours"
  type        = number
  default     = 1

  validation {
    condition     = var.rpo_target_hours > 0
    error_message = "RPO target must be positive."
  }
}

# Compliance Configuration
variable "compliance_frameworks" {
  description = "List of compliance frameworks requiring specific backup policies"
  type        = list(string)
  default     = ["SOX", "PCI-DSS", "SOC2"]
}

variable "enable_compliance_reporting" {
  description = "Enable compliance reporting for backup policies"
  type        = bool
  default     = true
}

# Cost Optimization
variable "enable_cost_optimization" {
  description = "Enable cost optimization features for backups"
  type        = bool
  default     = true
}

variable "backup_cost_budget_usd" {
  description = "Monthly backup cost budget in USD"
  type        = number
  default     = 500

  validation {
    condition     = var.backup_cost_budget_usd > 0
    error_message = "Backup cost budget must be positive."
  }
}

# Advanced Backup Features
variable "enable_point_in_time_recovery" {
  description = "Enable point-in-time recovery for supported resources"
  type        = bool
  default     = true
}

variable "enable_backup_encryption" {
  description = "Enable backup encryption (always true for compliance)"
  type        = bool
  default     = true
}

variable "backup_window_start_hour" {
  description = "Preferred backup window start hour (UTC)"
  type        = number
  default     = 2

  validation {
    condition     = var.backup_window_start_hour >= 0 && var.backup_window_start_hour <= 23
    error_message = "Backup window start hour must be between 0 and 23."
  }
}

variable "backup_window_duration_hours" {
  description = "Backup window duration in hours"
  type        = number
  default     = 4

  validation {
    condition     = var.backup_window_duration_hours >= 1 && var.backup_window_duration_hours <= 12
    error_message = "Backup window duration must be between 1 and 12 hours."
  }
}
