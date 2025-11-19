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

# CloudWatch Configuration
variable "log_retention_days" {
  description = "CloudWatch Logs retention period in days"
  type        = number
  default     = 365

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be a valid CloudWatch Logs retention period."
  }
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for resources"
  type        = bool
  default     = true
}

# SNS Configuration
variable "sns_topic_name" {
  description = "Name of the SNS topic for alerts"
  type        = string
}

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

# Resource Monitoring Configuration
variable "vpc_id" {
  description = "VPC ID for monitoring network resources"
  type        = string
  default     = null
}

variable "load_balancer_arn" {
  description = "ARN of the load balancer to monitor"
  type        = string
  default     = null
}

variable "rds_instance_id" {
  description = "RDS instance ID to monitor"
  type        = string
  default     = null
}

# Alarm Thresholds
variable "alb_response_time_threshold" {
  description = "ALB response time threshold in seconds"
  type        = number
  default     = 1

  validation {
    condition     = var.alb_response_time_threshold > 0
    error_message = "ALB response time threshold must be positive."
  }
}

variable "alb_5xx_error_threshold" {
  description = "ALB 5XX error count threshold"
  type        = number
  default     = 10

  validation {
    condition     = var.alb_5xx_error_threshold >= 0
    error_message = "ALB 5XX error threshold must be non-negative."
  }
}

variable "rds_cpu_threshold" {
  description = "RDS CPU utilization threshold percentage"
  type        = number
  default     = 80

  validation {
    condition     = var.rds_cpu_threshold > 0 && var.rds_cpu_threshold <= 100
    error_message = "RDS CPU threshold must be between 1 and 100."
  }
}

variable "rds_connections_threshold" {
  description = "RDS database connections threshold"
  type        = number
  default     = 80

  validation {
    condition     = var.rds_connections_threshold > 0
    error_message = "RDS connections threshold must be positive."
  }
}

variable "failed_login_threshold" {
  description = "Failed login attempts threshold"
  type        = number
  default     = 5

  validation {
    condition     = var.failed_login_threshold > 0
    error_message = "Failed login threshold must be positive."
  }
}

variable "application_error_threshold" {
  description = "Application error count threshold"
  type        = number
  default     = 10

  validation {
    condition     = var.application_error_threshold > 0
    error_message = "Application error threshold must be positive."
  }
}

# X-Ray Configuration
variable "enable_xray_tracing" {
  description = "Enable AWS X-Ray tracing"
  type        = bool
  default     = false
}

variable "xray_sampling_rate" {
  description = "X-Ray sampling rate (0.0 to 1.0)"
  type        = number
  default     = 0.1

  validation {
    condition     = var.xray_sampling_rate >= 0.0 && var.xray_sampling_rate <= 1.0
    error_message = "X-Ray sampling rate must be between 0.0 and 1.0."
  }
}

# Dashboard Configuration
variable "enable_dashboard" {
  description = "Enable CloudWatch dashboard creation"
  type        = bool
  default     = true
}

# Security Monitoring Configuration
variable "enable_security_monitoring" {
  description = "Enable security event monitoring"
  type        = bool
  default     = true
}

variable "enable_compliance_monitoring" {
  description = "Enable compliance monitoring"
  type        = bool
  default     = true
}

# Log Analysis Configuration
variable "enable_log_insights" {
  description = "Enable CloudWatch Logs Insights queries"
  type        = bool
  default     = true
}

# Cost Monitoring Configuration
variable "enable_cost_monitoring" {
  description = "Enable cost monitoring and alerts"
  type        = bool
  default     = true
}

variable "monthly_cost_threshold" {
  description = "Monthly cost threshold for alerts (USD)"
  type        = number
  default     = 1000

  validation {
    condition     = var.monthly_cost_threshold > 0
    error_message = "Monthly cost threshold must be positive."
  }
}
