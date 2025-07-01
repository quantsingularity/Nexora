# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Database credentials secret
resource "aws_secretsmanager_secret" "database_credentials" {
  name                    = "${var.app_name}/${var.environment}/database/master-credentials"
  description             = "Master database credentials for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-db-master-credentials"
    Environment = var.environment
    Purpose     = "Database-Credentials"
    Type        = "Master-Credentials"
  }
}

resource "aws_secretsmanager_secret_version" "database_credentials" {
  secret_id = aws_secretsmanager_secret.database_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
  })
}

# Application secrets
resource "aws_secretsmanager_secret" "app_secrets" {
  for_each = var.app_secrets

  name                    = "${var.app_name}/${var.environment}/application/${each.key}"
  description             = "Application secret: ${each.key} for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-app-${each.key}"
    Environment = var.environment
    Purpose     = "Application-Secret"
    SecretType  = each.key
  }
}

resource "aws_secretsmanager_secret_version" "app_secrets" {
  for_each = var.app_secrets

  secret_id     = aws_secretsmanager_secret.app_secrets[each.key].id
  secret_string = each.value
}

# API keys and external service credentials
resource "aws_secretsmanager_secret" "api_keys" {
  count = length(var.api_keys) > 0 ? 1 : 0

  name                    = "${var.app_name}/${var.environment}/api-keys"
  description             = "API keys and external service credentials for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-api-keys"
    Environment = var.environment
    Purpose     = "API-Keys"
  }
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  count = length(var.api_keys) > 0 ? 1 : 0

  secret_id     = aws_secretsmanager_secret.api_keys[0].id
  secret_string = jsonencode(var.api_keys)
}

# SSL/TLS certificates
resource "aws_secretsmanager_secret" "ssl_certificates" {
  count = length(var.ssl_certificates) > 0 ? 1 : 0

  name                    = "${var.app_name}/${var.environment}/ssl-certificates"
  description             = "SSL/TLS certificates for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-ssl-certificates"
    Environment = var.environment
    Purpose     = "SSL-Certificates"
  }
}

resource "aws_secretsmanager_secret_version" "ssl_certificates" {
  count = length(var.ssl_certificates) > 0 ? 1 : 0

  secret_id     = aws_secretsmanager_secret.ssl_certificates[0].id
  secret_string = jsonencode(var.ssl_certificates)
}

# JWT signing keys
resource "aws_secretsmanager_secret" "jwt_keys" {
  count = var.enable_jwt_secrets ? 1 : 0

  name                    = "${var.app_name}/${var.environment}/jwt-keys"
  description             = "JWT signing keys for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-jwt-keys"
    Environment = var.environment
    Purpose     = "JWT-Keys"
  }
}

# Generate JWT signing key if enabled
resource "random_password" "jwt_secret" {
  count   = var.enable_jwt_secrets ? 1 : 0
  length  = 64
  special = true
}

resource "aws_secretsmanager_secret_version" "jwt_keys" {
  count = var.enable_jwt_secrets ? 1 : 0

  secret_id = aws_secretsmanager_secret.jwt_keys[0].id
  secret_string = jsonencode({
    signing_key = random_password.jwt_secret[0].result
    algorithm   = "HS256"
    issuer      = "${var.app_name}-${var.environment}"
    audience    = "${var.app_name}-${var.environment}-users"
  })
}

# Encryption keys for application-level encryption
resource "aws_secretsmanager_secret" "encryption_keys" {
  count = var.enable_app_encryption_keys ? 1 : 0

  name                    = "${var.app_name}/${var.environment}/encryption-keys"
  description             = "Application-level encryption keys for ${var.app_name} ${var.environment}"
  kms_key_id             = var.kms_key_id
  recovery_window_in_days = var.environment == "prod" ? 30 : 7

  tags = {
    Name        = "${var.app_name}-${var.environment}-encryption-keys"
    Environment = var.environment
    Purpose     = "Application-Encryption"
  }
}

# Generate application encryption keys
resource "random_password" "app_encryption_key" {
  count   = var.enable_app_encryption_keys ? 1 : 0
  length  = 32
  special = false
}

resource "random_password" "app_encryption_iv" {
  count   = var.enable_app_encryption_keys ? 1 : 0
  length  = 16
  special = false
}

resource "aws_secretsmanager_secret_version" "encryption_keys" {
  count = var.enable_app_encryption_keys ? 1 : 0

  secret_id = aws_secretsmanager_secret.encryption_keys[0].id
  secret_string = jsonencode({
    encryption_key = random_password.app_encryption_key[0].result
    iv_key        = random_password.app_encryption_iv[0].result
    algorithm     = "AES-256-CBC"
  })
}

# Systems Manager Parameter Store for non-sensitive configuration
resource "aws_ssm_parameter" "app_config" {
  for_each = var.app_config_parameters

  name  = "/${var.app_name}/${var.environment}/config/${each.key}"
  type  = "String"
  value = each.value
  description = "Application configuration parameter: ${each.key}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-config-${each.key}"
    Environment = var.environment
    Purpose     = "Application-Configuration"
    Type        = "Non-Sensitive"
  }
}

# Secure string parameters for sensitive configuration
resource "aws_ssm_parameter" "secure_config" {
  for_each = var.secure_config_parameters

  name   = "/${var.app_name}/${var.environment}/secure-config/${each.key}"
  type   = "SecureString"
  value  = each.value
  key_id = var.kms_key_id
  description = "Secure configuration parameter: ${each.key}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-secure-config-${each.key}"
    Environment = var.environment
    Purpose     = "Secure-Configuration"
    Type        = "Sensitive"
  }
}

# IAM role for applications to access secrets
resource "aws_iam_role" "secrets_access_role" {
  name = "${var.app_name}-${var.environment}-secrets-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "ec2.amazonaws.com",
            "ecs-tasks.amazonaws.com",
            "lambda.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-secrets-access-role"
    Environment = var.environment
    Purpose     = "Secrets-Access"
  }
}

# IAM policy for secrets access
resource "aws_iam_role_policy" "secrets_access_policy" {
  name = "${var.app_name}-${var.environment}-secrets-access-policy"
  role = aws_iam_role.secrets_access_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.database_credentials.arn,
          "${aws_secretsmanager_secret.database_credentials.arn}:*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          for secret in aws_secretsmanager_secret.app_secrets : secret.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = concat(
          length(var.api_keys) > 0 ? [aws_secretsmanager_secret.api_keys[0].arn] : [],
          length(var.ssl_certificates) > 0 ? [aws_secretsmanager_secret.ssl_certificates[0].arn] : [],
          var.enable_jwt_secrets ? [aws_secretsmanager_secret.jwt_keys[0].arn] : [],
          var.enable_app_encryption_keys ? [aws_secretsmanager_secret.encryption_keys[0].arn] : []
        )
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.app_name}/${var.environment}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey"
        ]
        Resource = var.kms_key_id
      }
    ]
  })
}

# IAM instance profile for EC2 instances
resource "aws_iam_instance_profile" "secrets_access_profile" {
  name = "${var.app_name}-${var.environment}-secrets-access-profile"
  role = aws_iam_role.secrets_access_role.name

  tags = {
    Name        = "${var.app_name}-${var.environment}-secrets-access-profile"
    Environment = var.environment
    Purpose     = "Secrets-Access"
  }
}

# CloudWatch Log Group for secrets access auditing
resource "aws_cloudwatch_log_group" "secrets_audit" {
  name              = "/aws/secretsmanager/${var.app_name}-${var.environment}"
  retention_in_days = var.audit_log_retention_days
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-secrets-audit-logs"
    Environment = var.environment
    Purpose     = "Secrets-Audit"
  }
}

# EventBridge rule for secrets access monitoring
resource "aws_cloudwatch_event_rule" "secrets_access" {
  name        = "${var.app_name}-${var.environment}-secrets-access"
  description = "Monitor secrets access events"

  event_pattern = jsonencode({
    source      = ["aws.secretsmanager"]
    detail-type = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource = ["secretsmanager.amazonaws.com"]
      eventName   = ["GetSecretValue"]
      resources = {
        ARN = [for secret in concat(
          [aws_secretsmanager_secret.database_credentials],
          values(aws_secretsmanager_secret.app_secrets),
          length(var.api_keys) > 0 ? [aws_secretsmanager_secret.api_keys[0]] : [],
          length(var.ssl_certificates) > 0 ? [aws_secretsmanager_secret.ssl_certificates[0]] : [],
          var.enable_jwt_secrets ? [aws_secretsmanager_secret.jwt_keys[0]] : [],
          var.enable_app_encryption_keys ? [aws_secretsmanager_secret.encryption_keys[0]] : []
        ) : secret.arn]
      }
    }
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-secrets-access-rule"
    Environment = var.environment
    Purpose     = "Secrets-Monitoring"
  }
}

# CloudWatch Log Stream for secrets access events
resource "aws_cloudwatch_log_stream" "secrets_access" {
  name           = "secrets-access-events"
  log_group_name = aws_cloudwatch_log_group.secrets_audit.name
}

# EventBridge target to send events to CloudWatch Logs
resource "aws_cloudwatch_event_target" "secrets_access_logs" {
  rule      = aws_cloudwatch_event_rule.secrets_access.name
  target_id = "SendToCloudWatchLogs"
  arn       = aws_cloudwatch_log_group.secrets_audit.arn
}

# Secret rotation for database credentials (if enabled)
resource "aws_secretsmanager_secret_rotation" "database_credentials" {
  count = var.enable_secret_rotation ? 1 : 0

  secret_id           = aws_secretsmanager_secret.database_credentials.id
  rotation_lambda_arn = var.rotation_lambda_arn
  
  rotation_rules {
    automatically_after_days = var.rotation_interval_days
  }

  depends_on = [aws_secretsmanager_secret_version.database_credentials]
}

# Backup secrets to S3 for disaster recovery
resource "aws_s3_bucket" "secrets_backup" {
  count  = var.enable_secrets_backup ? 1 : 0
  bucket = "${var.app_name}-${var.environment}-secrets-backup-${random_id.secrets_backup_suffix[0].hex}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-secrets-backup"
    Environment = var.environment
    Purpose     = "Secrets-Backup"
  }
}

resource "random_id" "secrets_backup_suffix" {
  count       = var.enable_secrets_backup ? 1 : 0
  byte_length = 4
}

resource "aws_s3_bucket_server_side_encryption_configuration" "secrets_backup" {
  count  = var.enable_secrets_backup ? 1 : 0
  bucket = aws_s3_bucket.secrets_backup[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_id
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "secrets_backup" {
  count  = var.enable_secrets_backup ? 1 : 0
  bucket = aws_s3_bucket.secrets_backup[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "secrets_backup" {
  count  = var.enable_secrets_backup ? 1 : 0
  bucket = aws_s3_bucket.secrets_backup[0].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

