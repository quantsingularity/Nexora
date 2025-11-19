terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    # Enhanced backend configuration with encryption
    encrypt        = true
    kms_key_id     = "alias/terraform-state-key"
    dynamodb_table = "terraform-state-lock"
  }
}

# Configure AWS provider with enhanced security
provider "aws" {
  region = var.aws_region

  # Enhanced default tags for compliance and governance
  default_tags {
    tags = merge(var.default_tags, {
      ManagedBy           = "Terraform"
      SecurityCompliance  = "Financial"
      DataClassification  = "Confidential"
      BackupRequired      = "true"
      MonitoringEnabled   = "true"
      ComplianceFramework = "SOX,PCI-DSS,SOC2"
      LastUpdated         = formatdate("YYYY-MM-DD", timestamp())
    })
  }

  # Assume role for cross-account access if specified
  dynamic "assume_role" {
    for_each = var.assume_role_arn != null ? [1] : []
    content {
      role_arn     = var.assume_role_arn
      session_name = "terraform-${var.environment}"
    }
  }
}

# Data sources for enhanced security
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
data "aws_availability_zones" "available" {
  state = "available"
}

# KMS key for encryption
resource "aws_kms_key" "main" {
  description             = "KMS key for ${var.app_name} ${var.environment} environment"
  deletion_window_in_days = var.kms_deletion_window
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow CloudTrail to encrypt logs"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = [
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-kms-key"
    Environment = var.environment
    Purpose     = "Encryption"
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/${var.app_name}-${var.environment}"
  target_key_id = aws_kms_key.main.key_id
}

# Enhanced network module with security features
module "network" {
  source = "./modules/network"

  environment              = var.environment
  vpc_cidr                = var.vpc_cidr
  availability_zones      = var.availability_zones
  public_subnet_cidrs     = var.public_subnet_cidrs
  private_subnet_cidrs    = var.private_subnet_cidrs
  database_subnet_cidrs   = var.database_subnet_cidrs
  enable_nat_gateway      = var.enable_nat_gateway
  enable_vpn_gateway      = var.enable_vpn_gateway
  enable_dns_hostnames    = true
  enable_dns_support      = true
  enable_flow_logs        = true
  flow_logs_retention     = var.flow_logs_retention_days
  kms_key_id             = aws_kms_key.main.arn
  app_name               = var.app_name

  # Network security enhancements
  enable_network_acls     = true
  enable_security_groups  = true
  restrict_default_sg     = true
}

# Enhanced security module
module "security" {
  source = "./modules/security"

  environment            = var.environment
  vpc_id                = module.network.vpc_id
  app_name              = var.app_name
  kms_key_id            = aws_kms_key.main.arn

  # Security enhancements
  enable_waf             = var.enable_waf
  enable_shield          = var.enable_shield
  enable_guardduty       = var.enable_guardduty
  enable_config          = var.enable_config
  enable_cloudtrail      = var.enable_cloudtrail
  enable_inspector       = var.enable_inspector

  # Compliance settings
  cloudtrail_retention_days = var.audit_log_retention_days
  config_retention_days     = var.config_retention_days

  depends_on = [module.network]
}

# Enhanced compute module with security hardening
module "compute" {
  source = "./modules/compute"

  environment            = var.environment
  vpc_id                = module.network.vpc_id
  private_subnet_ids    = module.network.private_subnet_ids
  public_subnet_ids     = module.network.public_subnet_ids
  instance_type         = var.instance_type
  key_name              = var.key_name
  app_name              = var.app_name
  kms_key_id            = aws_kms_key.main.arn

  # Security configurations
  security_group_ids    = [module.security.app_security_group_id]
  enable_detailed_monitoring = true
  enable_ebs_encryption = true
  enable_imdsv2_only    = true

  # Auto Scaling and Load Balancing
  min_size              = var.asg_min_size
  max_size              = var.asg_max_size
  desired_capacity      = var.asg_desired_capacity
  health_check_type     = "ELB"
  health_check_grace_period = 300

  depends_on = [module.network, module.security]
}

# Enhanced database module with encryption and backup
module "database" {
  source = "./modules/database"

  environment            = var.environment
  vpc_id                = module.network.vpc_id
  private_subnet_ids    = module.network.private_subnet_ids
  database_subnet_ids   = module.network.database_subnet_ids
  db_instance_class     = var.db_instance_class
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  kms_key_id            = aws_kms_key.main.arn

  # Security configurations
  security_group_ids    = [module.security.db_security_group_id]
  enable_encryption     = true
  enable_backup         = true
  backup_retention_period = var.db_backup_retention_days
  backup_window         = var.db_backup_window
  maintenance_window    = var.db_maintenance_window

  # High availability and performance
  multi_az              = var.db_multi_az
  enable_performance_insights = true
  performance_insights_retention_period = 7

  # Monitoring and logging
  enable_enhanced_monitoring = true
  monitoring_interval   = 60
  enabled_cloudwatch_logs_exports = ["error", "general", "slowquery"]

  depends_on = [module.network, module.security]
}

# Enhanced storage module with encryption and lifecycle policies
module "storage" {
  source = "./modules/storage"

  environment           = var.environment
  app_name             = var.app_name
  kms_key_id           = aws_kms_key.main.arn

  # Security configurations
  enable_encryption    = true
  enable_versioning    = true
  enable_mfa_delete    = var.enable_mfa_delete

  # Compliance and lifecycle
  enable_lifecycle_policy = true
  transition_to_ia_days   = var.s3_transition_to_ia_days
  transition_to_glacier_days = var.s3_transition_to_glacier_days
  expiration_days        = var.s3_expiration_days

  # Access logging and monitoring
  enable_access_logging  = true
  enable_server_access_logging = true

  depends_on = [module.security]
}

# Monitoring and logging module
module "monitoring" {
  source = "./modules/monitoring"

  environment           = var.environment
  app_name             = var.app_name
  kms_key_id           = aws_kms_key.main.arn

  # CloudWatch configuration
  log_retention_days   = var.cloudwatch_log_retention_days
  enable_detailed_monitoring = true

  # Alerting configuration
  sns_topic_name       = "${var.app_name}-${var.environment}-alerts"
  alert_email_endpoints = var.alert_email_endpoints

  # Monitoring targets
  vpc_id               = module.network.vpc_id
  load_balancer_arn    = module.compute.load_balancer_arn
  rds_instance_id      = module.database.db_instance_id

  depends_on = [module.network, module.compute, module.database]
}

# Secrets management module
module "secrets" {
  source = "./modules/secrets"

  environment          = var.environment
  app_name            = var.app_name
  kms_key_id          = aws_kms_key.main.arn

  # Database credentials
  db_username         = var.db_username
  db_password         = var.db_password

  # Application secrets
  app_secrets         = var.app_secrets

  depends_on = [module.security]
}

# Backup and disaster recovery module
module "backup" {
  source = "./modules/backup"

  environment         = var.environment
  app_name           = var.app_name
  kms_key_id         = aws_kms_key.main.arn

  # Backup configuration
  backup_retention_days = var.backup_retention_days
  backup_schedule      = var.backup_schedule

  # Resources to backup
  rds_instance_arn     = module.database.db_instance_arn
  ebs_volume_ids       = module.compute.ebs_volume_ids
  s3_bucket_arn        = module.storage.s3_bucket_arn

  depends_on = [module.compute, module.database, module.storage]
}
