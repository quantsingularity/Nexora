# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Random password for database master user (if not provided)
resource "random_password" "master_password" {
  count   = var.db_password == null ? 1 : 0
  length  = 32
  special = true
}

# DB Subnet Group for database isolation
resource "aws_db_subnet_group" "main" {
  name       = "${var.app_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.database_subnet_ids != null ? var.database_subnet_ids : var.private_subnet_ids
  description = "Database subnet group for ${var.app_name} ${var.environment}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-subnet-group"
    Environment = var.environment
    Purpose     = "Database-Isolation"
  }
}

# DB Parameter Group for enhanced security and performance
resource "aws_db_parameter_group" "main" {
  family = var.engine == "mysql" ? "mysql8.0" : "postgres14"
  name   = "${var.app_name}-${var.environment}-db-params"
  description = "Database parameter group for ${var.app_name} ${var.environment}"

  # MySQL security parameters
  dynamic "parameter" {
    for_each = var.engine == "mysql" ? [1] : []
    content {
      name  = "log_bin_trust_function_creators"
      value = "1"
    }
  }

  dynamic "parameter" {
    for_each = var.engine == "mysql" ? [1] : []
    content {
      name  = "slow_query_log"
      value = "1"
    }
  }

  dynamic "parameter" {
    for_each = var.engine == "mysql" ? [1] : []
    content {
      name  = "long_query_time"
      value = "2"
    }
  }

  dynamic "parameter" {
    for_each = var.engine == "mysql" ? [1] : []
    content {
      name  = "general_log"
      value = "1"
    }
  }

  # PostgreSQL security parameters
  dynamic "parameter" {
    for_each = var.engine == "postgres" ? [1] : []
    content {
      name  = "log_statement"
      value = "all"
    }
  }

  dynamic "parameter" {
    for_each = var.engine == "postgres" ? [1] : []
    content {
      name  = "log_min_duration_statement"
      value = "2000"
    }
  }

  dynamic "parameter" {
    for_each = var.engine == "postgres" ? [1] : []
    content {
      name  = "log_connections"
      value = "1"
    }
  }

  dynamic "parameter" {
    for_each = var.engine == "postgres" ? [1] : []
    content {
      name  = "log_disconnections"
      value = "1"
    }
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-parameter-group"
    Environment = var.environment
    Purpose     = "Database-Configuration"
  }
}

# DB Option Group for additional features
resource "aws_db_option_group" "main" {
  count                    = var.engine == "mysql" ? 1 : 0
  name                     = "${var.app_name}-${var.environment}-db-options"
  option_group_description = "Database option group for ${var.app_name} ${var.environment}"
  engine_name              = "mysql"
  major_engine_version     = "8.0"

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-option-group"
    Environment = var.environment
    Purpose     = "Database-Options"
  }
}

# RDS Instance with enhanced security and compliance
resource "aws_db_instance" "main" {
  identifier = "${var.app_name}-${var.environment}-db"
  
  # Engine configuration
  engine                      = var.engine
  engine_version             = var.engine_version
  instance_class             = var.db_instance_class
  
  # Database configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password != null ? var.db_password : random_password.master_password[0].result
  port     = var.engine == "mysql" ? 3306 : 5432
  
  # Storage configuration with encryption
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = var.storage_type
  storage_encrypted     = var.enable_encryption
  kms_key_id           = var.enable_encryption ? var.kms_key_id : null
  iops                 = var.storage_type == "io1" || var.storage_type == "io2" ? var.iops : null
  
  # Network and security configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = var.security_group_ids
  publicly_accessible    = false
  
  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.main.name
  option_group_name    = var.engine == "mysql" ? aws_db_option_group.main[0].name : null
  
  # High availability and backup configuration
  multi_az                = var.multi_az
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window
  copy_tags_to_snapshot  = true
  delete_automated_backups = false
  deletion_protection    = var.environment == "prod" ? true : false
  skip_final_snapshot    = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${var.app_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null
  
  # Monitoring and logging
  monitoring_interval                   = var.enable_enhanced_monitoring ? var.monitoring_interval : 0
  monitoring_role_arn                  = var.enable_enhanced_monitoring ? aws_iam_role.rds_enhanced_monitoring[0].arn : null
  performance_insights_enabled         = var.enable_performance_insights
  performance_insights_retention_period = var.enable_performance_insights ? var.performance_insights_retention_period : null
  performance_insights_kms_key_id      = var.enable_performance_insights && var.enable_encryption ? var.kms_key_id : null
  enabled_cloudwatch_logs_exports      = var.enabled_cloudwatch_logs_exports
  
  # Security and compliance
  auto_minor_version_upgrade = false  # Controlled updates for compliance
  apply_immediately         = false   # Changes applied during maintenance window
  
  tags = {
    Name                = "${var.app_name}-${var.environment}-database"
    Environment         = var.environment
    Engine              = var.engine
    SecurityCompliance  = "Financial"
    BackupEnabled       = "true"
    EncryptionEnabled   = var.enable_encryption ? "true" : "false"
    MultiAZ             = var.multi_az ? "true" : "false"
    MonitoringEnabled   = var.enable_enhanced_monitoring ? "true" : "false"
  }

  depends_on = [aws_db_parameter_group.main]
}

# IAM role for RDS Enhanced Monitoring
resource "aws_iam_role" "rds_enhanced_monitoring" {
  count = var.enable_enhanced_monitoring ? 1 : 0
  name  = "${var.app_name}-${var.environment}-rds-enhanced-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-rds-enhanced-monitoring-role"
    Environment = var.environment
    Purpose     = "RDS-Enhanced-Monitoring"
  }
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  count      = var.enable_enhanced_monitoring ? 1 : 0
  role       = aws_iam_role.rds_enhanced_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Read Replica for disaster recovery and read scaling
resource "aws_db_instance" "read_replica" {
  count = var.create_read_replica ? 1 : 0
  
  identifier = "${var.app_name}-${var.environment}-db-replica"
  replicate_source_db = aws_db_instance.main.identifier
  
  instance_class = var.replica_instance_class != null ? var.replica_instance_class : var.db_instance_class
  
  # Network configuration
  publicly_accessible = false
  
  # Monitoring
  monitoring_interval = var.enable_enhanced_monitoring ? var.monitoring_interval : 0
  monitoring_role_arn = var.enable_enhanced_monitoring ? aws_iam_role.rds_enhanced_monitoring[0].arn : null
  
  # Performance Insights
  performance_insights_enabled         = var.enable_performance_insights
  performance_insights_retention_period = var.enable_performance_insights ? var.performance_insights_retention_period : null
  performance_insights_kms_key_id      = var.enable_performance_insights && var.enable_encryption ? var.kms_key_id : null
  
  # Security
  auto_minor_version_upgrade = false
  apply_immediately         = false
  
  tags = {
    Name                = "${var.app_name}-${var.environment}-database-replica"
    Environment         = var.environment
    Purpose             = "Read-Replica"
    SecurityCompliance  = "Financial"
    MonitoringEnabled   = var.enable_enhanced_monitoring ? "true" : "false"
  }
}

# DB Snapshot for point-in-time recovery
resource "aws_db_snapshot" "manual_snapshot" {
  count                  = var.create_manual_snapshot ? 1 : 0
  db_instance_identifier = aws_db_instance.main.id
  db_snapshot_identifier = "${var.app_name}-${var.environment}-manual-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-manual-snapshot"
    Environment = var.environment
    Purpose     = "Manual-Backup"
    CreatedBy   = "Terraform"
  }
}

# CloudWatch Log Groups for database logs
resource "aws_cloudwatch_log_group" "database_logs" {
  for_each = toset(var.enabled_cloudwatch_logs_exports)
  
  name              = "/aws/rds/instance/${aws_db_instance.main.id}/${each.value}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-${each.value}-logs"
    Environment = var.environment
    Purpose     = "Database-Logging"
  }
}

# Database connection secret in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "${var.app_name}/${var.environment}/database/credentials"
  description             = "Database credentials for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-credentials"
    Environment = var.environment
    Purpose     = "Database-Credentials"
  }
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password != null ? var.db_password : random_password.master_password[0].result
    engine   = var.engine
    host     = aws_db_instance.main.endpoint
    port     = aws_db_instance.main.port
    dbname   = var.db_name
    dbInstanceIdentifier = aws_db_instance.main.id
  })
}

# Database connection string secret
resource "aws_secretsmanager_secret" "db_connection_string" {
  name                    = "${var.app_name}/${var.environment}/database/connection-string"
  description             = "Database connection string for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-connection-string"
    Environment = var.environment
    Purpose     = "Database-Connection"
  }
}

resource "aws_secretsmanager_secret_version" "db_connection_string" {
  secret_id = aws_secretsmanager_secret.db_connection_string.id
  secret_string = jsonencode({
    connection_string = var.engine == "mysql" ? 
      "mysql://${var.db_username}:${var.db_password != null ? var.db_password : random_password.master_password[0].result}@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${var.db_name}" :
      "postgresql://${var.db_username}:${var.db_password != null ? var.db_password : random_password.master_password[0].result}@${aws_db_instance.main.endpoint}:${aws_db_instance.main.port}/${var.db_name}"
  })
}

