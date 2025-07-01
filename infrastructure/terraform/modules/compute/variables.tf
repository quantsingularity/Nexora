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
  description = "VPC ID where compute resources will be created"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for EC2 instances"
  type        = list(string)
  
  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "At least 2 private subnet IDs must be provided for high availability."
  }
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for load balancer"
  type        = list(string)
  
  validation {
    condition     = length(var.public_subnet_ids) >= 2
    error_message = "At least 2 public subnet IDs must be provided for high availability."
  }
}

variable "security_group_ids" {
  description = "List of security group IDs to attach to instances"
  type        = list(string)
}

variable "kms_key_id" {
  description = "KMS key ID for encryption"
  type        = string
}

# EC2 Configuration
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

# Auto Scaling Configuration
variable "min_size" {
  description = "Minimum size of the Auto Scaling Group"
  type        = number
  default     = 1
  
  validation {
    condition     = var.min_size >= 1
    error_message = "ASG minimum size must be at least 1."
  }
}

variable "max_size" {
  description = "Maximum size of the Auto Scaling Group"
  type        = number
  default     = 10
  
  validation {
    condition     = var.max_size >= 1
    error_message = "ASG maximum size must be at least 1."
  }
}

variable "desired_capacity" {
  description = "Desired capacity of the Auto Scaling Group"
  type        = number
  default     = 2
  
  validation {
    condition     = var.desired_capacity >= 1
    error_message = "ASG desired capacity must be at least 1."
  }
}

variable "health_check_type" {
  description = "Type of health check for Auto Scaling Group"
  type        = string
  default     = "ELB"
  
  validation {
    condition     = contains(["EC2", "ELB"], var.health_check_type)
    error_message = "Health check type must be either EC2 or ELB."
  }
}

variable "health_check_grace_period" {
  description = "Health check grace period in seconds"
  type        = number
  default     = 300
  
  validation {
    condition     = var.health_check_grace_period >= 0
    error_message = "Health check grace period must be non-negative."
  }
}

# Security Configuration
variable "enable_detailed_monitoring" {
  description = "Enable detailed monitoring for EC2 instances"
  type        = bool
  default     = true
}

variable "enable_ebs_encryption" {
  description = "Enable EBS encryption for instance volumes"
  type        = bool
  default     = true
}

variable "enable_imdsv2_only" {
  description = "Require IMDSv2 for instance metadata access"
  type        = bool
  default     = true
}

# SSL/TLS Configuration
variable "ssl_certificate_arn" {
  description = "ARN of the SSL certificate for HTTPS listener"
  type        = string
  default     = null
}

# Load Balancer Configuration
variable "enable_deletion_protection" {
  description = "Enable deletion protection for load balancer"
  type        = bool
  default     = null  # Will be set based on environment in main.tf
}

variable "enable_access_logs" {
  description = "Enable access logs for load balancer"
  type        = bool
  default     = true
}

# Application Configuration
variable "app_port" {
  description = "Application port (if different from 80)"
  type        = number
  default     = null
}

variable "health_check_path" {
  description = "Health check path for target group"
  type        = string
  default     = "/health"
}

variable "health_check_matcher" {
  description = "HTTP status codes for successful health checks"
  type        = string
  default     = "200"
}

# Scaling Configuration
variable "scale_up_threshold" {
  description = "CPU utilization threshold for scaling up"
  type        = number
  default     = 80
  
  validation {
    condition     = var.scale_up_threshold > 0 && var.scale_up_threshold <= 100
    error_message = "Scale up threshold must be between 1 and 100."
  }
}

variable "scale_down_threshold" {
  description = "CPU utilization threshold for scaling down"
  type        = number
  default     = 20
  
  validation {
    condition     = var.scale_down_threshold > 0 && var.scale_down_threshold <= 100
    error_message = "Scale down threshold must be between 1 and 100."
  }
}

variable "scaling_cooldown" {
  description = "Cooldown period in seconds between scaling actions"
  type        = number
  default     = 300
  
  validation {
    condition     = var.scaling_cooldown >= 0
    error_message = "Scaling cooldown must be non-negative."
  }
}

# Storage Configuration
variable "root_volume_size" {
  description = "Size of the root EBS volume in GB"
  type        = number
  default     = 20
  
  validation {
    condition     = var.root_volume_size >= 8
    error_message = "Root volume size must be at least 8 GB."
  }
}

variable "data_volume_size" {
  description = "Size of the additional data EBS volume in GB"
  type        = number
  default     = 50
  
  validation {
    condition     = var.data_volume_size >= 1
    error_message = "Data volume size must be at least 1 GB."
  }
}

variable "volume_type" {
  description = "EBS volume type"
  type        = string
  default     = "gp3"
  
  validation {
    condition     = contains(["gp2", "gp3", "io1", "io2"], var.volume_type)
    error_message = "Volume type must be one of: gp2, gp3, io1, io2."
  }
}

# Backup Configuration
variable "enable_backup" {
  description = "Enable automated backups for EBS volumes"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups"
  type        = number
  default     = 30
  
  validation {
    condition     = var.backup_retention_days >= 1
    error_message = "Backup retention days must be at least 1."
  }
}

