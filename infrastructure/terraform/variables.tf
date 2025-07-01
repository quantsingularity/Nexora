# Core Configuration Variables
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
  
  validation {
    condition = can(regex("^[a-z]{2}-[a-z]+-[0-9]$", var.aws_region))
    error_message = "AWS region must be in the format: us-west-2, eu-west-1, etc."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "app_name" {
  description = "Application name - used for resource naming and tagging"
  type        = string
  
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]*[a-z0-9]$", var.app_name))
    error_message = "App name must start with a letter, contain only lowercase letters, numbers, and hyphens, and end with a letter or number."
  }
}

# Network Configuration Variables
variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
  
  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b", "us-west-2c"]
  
  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones must be specified for high availability."
  }
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.4.0/24", "10.0.5.0/24", "10.0.6.0/24"]
}

variable "database_subnet_cidrs" {
  description = "CIDR blocks for database subnets"
  type        = list(string)
  default     = ["10.0.7.0/24", "10.0.8.0/24", "10.0.9.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway for hybrid connectivity"
  type        = bool
  default     = false
}

variable "flow_logs_retention_days" {
  description = "VPC Flow Logs retention period in days"
  type        = number
  default     = 30
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.flow_logs_retention_days)
    error_message = "Flow logs retention days must be a valid CloudWatch Logs retention period."
  }
}

# Compute Configuration Variables
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
  
  validation {
    condition = can(regex("^[a-z][0-9][a-z]?\\.[a-z0-9]+$", var.instance_type))
    error_message = "Instance type must be a valid EC2 instance type (e.g., t3.medium, m5.large)."
  }
}

variable "key_name" {
  description = "SSH key name for EC2 instances"
  type        = string
  default     = null
}

variable "asg_min_size" {
  description = "Minimum size of the Auto Scaling Group"
  type        = number
  default     = 1
  
  validation {
    condition     = var.asg_min_size >= 1
    error_message = "ASG minimum size must be at least 1."
  }
}

variable "asg_max_size" {
  description = "Maximum size of the Auto Scaling Group"
  type        = number
  default     = 10
  
  validation {
    condition     = var.asg_max_size >= var.asg_min_size
    error_message = "ASG maximum size must be greater than or equal to minimum size."
  }
}

variable "asg_desired_capacity" {
  description = "Desired capacity of the Auto Scaling Group"
  type        = number
  default     = 2
}

# Database Configuration Variables
variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
  
  validation {
    condition = can(regex("^db\\.[a-z0-9]+\\.[a-z0-9]+$", var.db_instance_class))
    error_message = "DB instance class must be a valid RDS instance type (e.g., db.t3.micro, db.r5.large)."
  }
}

variable "db_name" {
  description = "Database name"
  type        = string
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "Database name must start with a letter and contain only alphanumeric characters and underscores."
  }
}

variable "db_username" {
  description = "Database master username"
  type        = string
  sensitive   = true
  
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_username)) && length(var.db_username) >= 3
    error_message = "Database username must start with a letter, be at least 3 characters long, and contain only alphanumeric characters and underscores."
  }
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.db_password) >= 12
    error_message = "Database password must be at least 12 characters long."
  }
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment for RDS"
  type        = bool
  default     = true
}

variable "db_backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 30
  
  validation {
    condition     = var.db_backup_retention_days >= 7 && var.db_backup_retention_days <= 35
    error_message = "Backup retention period must be between 7 and 35 days for compliance."
  }
}

variable "db_backup_window" {
  description = "Preferred backup window"
  type        = string
  default     = "03:00-04:00"
}

variable "db_maintenance_window" {
  description = "Preferred maintenance window"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# Security Configuration Variables
variable "enable_waf" {
  description = "Enable AWS WAF for web application protection"
  type        = bool
  default     = true
}

variable "enable_shield" {
  description = "Enable AWS Shield Advanced for DDoS protection"
  type        = bool
  default     = false
}

variable "enable_guardduty" {
  description = "Enable AWS GuardDuty for threat detection"
  type        = bool
  default     = true
}

variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "enable_cloudtrail" {
  description = "Enable AWS CloudTrail for audit logging"
  type        = bool
  default     = true
}

variable "enable_inspector" {
  description = "Enable AWS Inspector for vulnerability assessment"
  type        = bool
  default     = true
}

variable "kms_deletion_window" {
  description = "KMS key deletion window in days"
  type        = number
  default     = 30
  
  validation {
    condition     = var.kms_deletion_window >= 7 && var.kms_deletion_window <= 30
    error_message = "KMS deletion window must be between 7 and 30 days."
  }
}

# Compliance and Audit Variables
variable "audit_log_retention_days" {
  description = "CloudTrail log retention period in days"
  type        = number
  default     = 2555  # 7 years for financial compliance
  
  validation {
    condition     = var.audit_log_retention_days >= 365
    error_message = "Audit log retention must be at least 365 days for compliance."
  }
}

variable "config_retention_days" {
  description = "AWS Config retention period in days"
  type        = number
  default     = 2555  # 7 years for financial compliance
}

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 365
  
  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.cloudwatch_log_retention_days)
    error_message = "CloudWatch log retention days must be a valid retention period."
  }
}

# Storage Configuration Variables
variable "enable_mfa_delete" {
  description = "Enable MFA delete for S3 buckets"
  type        = bool
  default     = false  # Requires root account access to enable
}

variable "s3_transition_to_ia_days" {
  description = "Days after which objects are transitioned to IA storage class"
  type        = number
  default     = 30
}

variable "s3_transition_to_glacier_days" {
  description = "Days after which objects are transitioned to Glacier storage class"
  type        = number
  default     = 90
}

variable "s3_expiration_days" {
  description = "Days after which objects are permanently deleted"
  type        = number
  default     = 2555  # 7 years for financial compliance
}

# Backup Configuration Variables
variable "backup_retention_days" {
  description = "AWS Backup retention period in days"
  type        = number
  default     = 2555  # 7 years for financial compliance
}

variable "backup_schedule" {
  description = "AWS Backup schedule expression"
  type        = string
  default     = "cron(0 2 ? * * *)"  # Daily at 2 AM
}

# Monitoring and Alerting Variables
variable "alert_email_endpoints" {
  description = "List of email addresses for alerts"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for email in var.alert_email_endpoints : can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", email))
    ])
    error_message = "All email addresses must be valid."
  }
}

# Application Secrets Variables
variable "app_secrets" {
  description = "Map of application secrets to store in AWS Secrets Manager"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# Cross-Account Access Variables
variable "assume_role_arn" {
  description = "ARN of the role to assume for cross-account access"
  type        = string
  default     = null
}

# Default Tags
variable "default_tags" {
  description = "Default tags for all resources"
  type        = map(string)
  default = {
    Terraform           = "true"
    ManagedBy          = "Terraform"
    SecurityCompliance = "Financial"
    DataClassification = "Confidential"
    BackupRequired     = "true"
    MonitoringEnabled  = "true"
  }
  
  validation {
    condition = alltrue([
      for key, value in var.default_tags : can(regex("^[a-zA-Z0-9+\\-=._:/@]+$", key)) && can(regex("^[a-zA-Z0-9+\\-=._:/@\\s]+$", value))
    ])
    error_message = "Tag keys and values must contain only valid characters."
  }
}

