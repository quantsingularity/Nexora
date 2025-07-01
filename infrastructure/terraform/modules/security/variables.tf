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

variable "vpc_id" {
  description = "VPC ID where security resources will be created"
  type        = string
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
}

# Security Group Configuration
variable "app_port" {
  description = "Application port (if different from 80/443)"
  type        = number
  default     = null
}

variable "enable_ssh_access" {
  description = "Enable SSH access to application servers"
  type        = bool
  default     = false
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["10.0.0.0/8"]
  
  validation {
    condition = alltrue([
      for cidr in var.ssh_allowed_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "All SSH allowed CIDRs must be valid IPv4 CIDR blocks."
  }
}

variable "enable_db_admin_access" {
  description = "Enable database administration access"
  type        = bool
  default     = false
}

variable "db_admin_allowed_cidrs" {
  description = "CIDR blocks allowed for database administration access"
  type        = list(string)
  default     = ["10.0.0.0/8"]
  
  validation {
    condition = alltrue([
      for cidr in var.db_admin_allowed_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "All database admin allowed CIDRs must be valid IPv4 CIDR blocks."
  }
}

# Bastion Host Configuration
variable "enable_bastion_host" {
  description = "Enable bastion host security group"
  type        = bool
  default     = false
}

variable "bastion_allowed_cidrs" {
  description = "CIDR blocks allowed to access bastion host"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for cidr in var.bastion_allowed_cidrs : can(cidrhost(cidr, 0))
    ])
    error_message = "All bastion allowed CIDRs must be valid IPv4 CIDR blocks."
  }
}

# AWS WAF Configuration
variable "enable_waf" {
  description = "Enable AWS WAF for web application protection"
  type        = bool
  default     = true
}

variable "waf_rate_limit" {
  description = "Rate limit for WAF (requests per 5-minute period)"
  type        = number
  default     = 2000
  
  validation {
    condition     = var.waf_rate_limit >= 100 && var.waf_rate_limit <= 20000000
    error_message = "WAF rate limit must be between 100 and 20,000,000."
  }
}

variable "enable_geo_blocking" {
  description = "Enable geographic blocking in WAF"
  type        = bool
  default     = false
}

variable "blocked_countries" {
  description = "List of country codes to block (ISO 3166-1 alpha-2)"
  type        = list(string)
  default     = []
  
  validation {
    condition = alltrue([
      for country in var.blocked_countries : can(regex("^[A-Z]{2}$", country))
    ])
    error_message = "Country codes must be valid ISO 3166-1 alpha-2 codes (e.g., US, CN, RU)."
  }
}

# AWS Shield Configuration
variable "enable_shield" {
  description = "Enable AWS Shield Advanced for DDoS protection"
  type        = bool
  default     = false
}

# CloudTrail Configuration
variable "enable_cloudtrail" {
  description = "Enable AWS CloudTrail for audit logging"
  type        = bool
  default     = true
}

variable "cloudtrail_retention_days" {
  description = "CloudTrail log retention period in days"
  type        = number
  default     = 2555  # 7 years for financial compliance
  
  validation {
    condition     = var.cloudtrail_retention_days >= 90
    error_message = "CloudTrail retention must be at least 90 days for compliance."
  }
}

# AWS Config Configuration
variable "enable_config" {
  description = "Enable AWS Config for compliance monitoring"
  type        = bool
  default     = true
}

variable "config_retention_days" {
  description = "AWS Config retention period in days"
  type        = number
  default     = 2555  # 7 years for financial compliance
  
  validation {
    condition     = var.config_retention_days >= 90
    error_message = "Config retention must be at least 90 days for compliance."
  }
}

# GuardDuty Configuration
variable "enable_guardduty" {
  description = "Enable AWS GuardDuty for threat detection"
  type        = bool
  default     = true
}

# Inspector Configuration
variable "enable_inspector" {
  description = "Enable AWS Inspector for vulnerability assessment"
  type        = bool
  default     = true
}

