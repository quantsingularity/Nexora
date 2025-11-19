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

# Security Configuration
variable "enable_encryption" {
  description = "Enable S3 bucket encryption with KMS"
  type        = bool
  default     = true
}

variable "enable_versioning" {
  description = "Enable S3 bucket versioning"
  type        = bool
  default     = true
}

variable "enable_mfa_delete" {
  description = "Enable MFA delete for S3 bucket (requires root account access)"
  type        = bool
  default     = false
}

# Lifecycle Management
variable "enable_lifecycle_policy" {
  description = "Enable S3 lifecycle policy for cost optimization"
  type        = bool
  default     = true
}

variable "transition_to_ia_days" {
  description = "Days after which objects are transitioned to IA storage class"
  type        = number
  default     = 30

  validation {
    condition     = var.transition_to_ia_days >= 30
    error_message = "Transition to IA must be at least 30 days."
  }
}

variable "transition_to_glacier_days" {
  description = "Days after which objects are transitioned to Glacier storage class"
  type        = number
  default     = 90

  validation {
    condition     = var.transition_to_glacier_days >= 90
    error_message = "Transition to Glacier must be at least 90 days."
  }
}

variable "expiration_days" {
  description = "Days after which objects are permanently deleted (0 = never delete)"
  type        = number
  default     = 2555  # 7 years for financial compliance

  validation {
    condition     = var.expiration_days >= 0
    error_message = "Expiration days must be non-negative."
  }
}

# Logging Configuration
variable "enable_access_logging" {
  description = "Enable S3 access logging"
  type        = bool
  default     = true
}

variable "enable_server_access_logging" {
  description = "Enable S3 server access logging"
  type        = bool
  default     = true
}

# CloudFront Configuration
variable "enable_cloudfront" {
  description = "Enable CloudFront distribution for content delivery"
  type        = bool
  default     = false
}

variable "waf_web_acl_id" {
  description = "WAF Web ACL ID to associate with CloudFront distribution"
  type        = string
  default     = null
}

# Static Website Configuration
variable "enable_static_website" {
  description = "Enable static website hosting"
  type        = bool
  default     = false
}

# Backup Configuration
variable "enable_backup_bucket" {
  description = "Create a separate bucket for backups"
  type        = bool
  default     = true
}

# Monitoring Configuration
variable "sns_topic_arn" {
  description = "SNS topic ARN for S3 bucket alarms"
  type        = string
  default     = null
}

variable "bucket_size_alarm_threshold" {
  description = "S3 bucket size alarm threshold in bytes"
  type        = number
  default     = 107374182400  # 100 GB

  validation {
    condition     = var.bucket_size_alarm_threshold > 0
    error_message = "Bucket size alarm threshold must be positive."
  }
}

# Inventory Configuration
variable "enable_inventory" {
  description = "Enable S3 inventory for compliance and cost optimization"
  type        = bool
  default     = true
}

# Cross-Region Replication Configuration
variable "enable_cross_region_replication" {
  description = "Enable cross-region replication for disaster recovery"
  type        = bool
  default     = false
}

variable "replication_destination_bucket" {
  description = "Destination bucket for cross-region replication"
  type        = string
  default     = null
}

variable "replication_destination_region" {
  description = "Destination region for cross-region replication"
  type        = string
  default     = null
}

# Object Lock Configuration
variable "enable_object_lock" {
  description = "Enable S3 Object Lock for compliance"
  type        = bool
  default     = false
}

variable "object_lock_mode" {
  description = "Object Lock mode (GOVERNANCE or COMPLIANCE)"
  type        = string
  default     = "COMPLIANCE"

  validation {
    condition     = contains(["GOVERNANCE", "COMPLIANCE"], var.object_lock_mode)
    error_message = "Object Lock mode must be either GOVERNANCE or COMPLIANCE."
  }
}

variable "object_lock_retention_days" {
  description = "Object Lock retention period in days"
  type        = number
  default     = 2555  # 7 years for financial compliance

  validation {
    condition     = var.object_lock_retention_days > 0
    error_message = "Object Lock retention days must be positive."
  }
}

# Intelligent Tiering Configuration
variable "enable_intelligent_tiering" {
  description = "Enable S3 Intelligent Tiering for automatic cost optimization"
  type        = bool
  default     = true
}

# Transfer Acceleration Configuration
variable "enable_transfer_acceleration" {
  description = "Enable S3 Transfer Acceleration"
  type        = bool
  default     = false
}

# Event Notification Configuration
variable "enable_event_notifications" {
  description = "Enable S3 event notifications"
  type        = bool
  default     = true
}

# Multipart Upload Configuration
variable "multipart_upload_threshold" {
  description = "Threshold in bytes for multipart uploads"
  type        = number
  default     = 104857600  # 100 MB

  validation {
    condition     = var.multipart_upload_threshold >= 5242880  # 5 MB minimum
    error_message = "Multipart upload threshold must be at least 5 MB."
  }
}

# Request Payer Configuration
variable "request_payer" {
  description = "Who pays for S3 requests and data transfer (BucketOwner or Requester)"
  type        = string
  default     = "BucketOwner"

  validation {
    condition     = contains(["BucketOwner", "Requester"], var.request_payer)
    error_message = "Request payer must be either BucketOwner or Requester."
  }
}
