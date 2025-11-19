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

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
}

# Database Credentials
variable "db_username" {
  description = "Database master username"
  type        = string

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

# Application Secrets
variable "app_secrets" {
  description = "Map of application secrets to store in AWS Secrets Manager"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# API Keys and External Service Credentials
variable "api_keys" {
  description = "Map of API keys and external service credentials"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# SSL/TLS Certificates
variable "ssl_certificates" {
  description = "Map of SSL/TLS certificates and private keys"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# JWT Configuration
variable "enable_jwt_secrets" {
  description = "Enable JWT signing key generation and storage"
  type        = bool
  default     = true
}

# Application-Level Encryption
variable "enable_app_encryption_keys" {
  description = "Enable application-level encryption key generation and storage"
  type        = bool
  default     = true
}

# Configuration Parameters (Non-Sensitive)
variable "app_config_parameters" {
  description = "Map of non-sensitive application configuration parameters for SSM Parameter Store"
  type        = map(string)
  default     = {}
}

# Secure Configuration Parameters (Sensitive)
variable "secure_config_parameters" {
  description = "Map of sensitive configuration parameters for SSM Parameter Store"
  type        = map(string)
  default     = {}
  sensitive   = true
}

# Secret Rotation Configuration
variable "enable_secret_rotation" {
  description = "Enable automatic secret rotation"
  type        = bool
  default     = false
}

variable "rotation_lambda_arn" {
  description = "ARN of the Lambda function for secret rotation"
  type        = string
  default     = null
}

variable "rotation_interval_days" {
  description = "Number of days between automatic secret rotations"
  type        = number
  default     = 30

  validation {
    condition     = var.rotation_interval_days >= 1 && var.rotation_interval_days <= 365
    error_message = "Rotation interval must be between 1 and 365 days."
  }
}

# Backup Configuration
variable "enable_secrets_backup" {
  description = "Enable secrets backup to S3 for disaster recovery"
  type        = bool
  default     = true
}

# Audit and Monitoring Configuration
variable "audit_log_retention_days" {
  description = "Secrets access audit log retention period in days"
  type        = number
  default     = 2555  # 7 years for financial compliance

  validation {
    condition     = var.audit_log_retention_days >= 90
    error_message = "Audit log retention must be at least 90 days for compliance."
  }
}

variable "enable_access_monitoring" {
  description = "Enable monitoring of secrets access events"
  type        = bool
  default     = true
}

# Cross-Region Replication
variable "enable_cross_region_replication" {
  description = "Enable cross-region replication of secrets for disaster recovery"
  type        = bool
  default     = false
}

variable "replica_regions" {
  description = "List of regions for secret replication"
  type        = list(string)
  default     = []
}

# Access Control Configuration
variable "allowed_principals" {
  description = "List of IAM principals allowed to access secrets"
  type        = list(string)
  default     = []
}

variable "denied_principals" {
  description = "List of IAM principals explicitly denied access to secrets"
  type        = list(string)
  default     = []
}

# Compliance Configuration
variable "enable_compliance_monitoring" {
  description = "Enable compliance monitoring for secrets management"
  type        = bool
  default     = true
}

variable "compliance_frameworks" {
  description = "List of compliance frameworks to adhere to"
  type        = list(string)
  default     = ["SOX", "PCI-DSS", "SOC2"]
}

# Cost Optimization
variable "enable_cost_optimization" {
  description = "Enable cost optimization features for secrets management"
  type        = bool
  default     = true
}

# Development and Testing
variable "enable_dev_secrets" {
  description = "Enable development-specific secrets (only for dev environment)"
  type        = bool
  default     = false
}

variable "dev_secrets" {
  description = "Map of development-specific secrets"
  type        = map(string)
  default     = {}
  sensitive   = true
}
