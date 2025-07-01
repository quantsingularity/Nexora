# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# AWS Backup Vault for centralized backup storage
resource "aws_backup_vault" "main" {
  name        = "${var.app_name}-${var.environment}-backup-vault"
  kms_key_arn = var.kms_key_arn

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-vault"
    Environment = var.environment
    Purpose     = "Centralized-Backup"
  }
}

# AWS Backup Plan for automated backups
resource "aws_backup_plan" "main" {
  name = "${var.app_name}-${var.environment}-backup-plan"

  # Daily backups with 30-day retention
  rule {
    rule_name         = "daily_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = var.daily_backup_schedule

    lifecycle {
      cold_storage_after = var.cold_storage_after_days
      delete_after       = var.daily_backup_retention_days
    }

    recovery_point_tags = {
      BackupType  = "Daily"
      Environment = var.environment
      AppName     = var.app_name
    }

    copy_action {
      destination_vault_arn = var.cross_region_backup_vault_arn != null ? var.cross_region_backup_vault_arn : aws_backup_vault.main.arn

      lifecycle {
        cold_storage_after = var.cold_storage_after_days
        delete_after       = var.daily_backup_retention_days
      }
    }
  }

  # Weekly backups with longer retention
  rule {
    rule_name         = "weekly_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = var.weekly_backup_schedule

    lifecycle {
      cold_storage_after = var.cold_storage_after_days
      delete_after       = var.weekly_backup_retention_days
    }

    recovery_point_tags = {
      BackupType  = "Weekly"
      Environment = var.environment
      AppName     = var.app_name
    }

    copy_action {
      destination_vault_arn = var.cross_region_backup_vault_arn != null ? var.cross_region_backup_vault_arn : aws_backup_vault.main.arn

      lifecycle {
        cold_storage_after = var.cold_storage_after_days
        delete_after       = var.weekly_backup_retention_days
      }
    }
  }

  # Monthly backups for long-term retention
  rule {
    rule_name         = "monthly_backups"
    target_vault_name = aws_backup_vault.main.name
    schedule          = var.monthly_backup_schedule

    lifecycle {
      cold_storage_after = var.cold_storage_after_days
      delete_after       = var.monthly_backup_retention_days
    }

    recovery_point_tags = {
      BackupType  = "Monthly"
      Environment = var.environment
      AppName     = var.app_name
    }

    copy_action {
      destination_vault_arn = var.cross_region_backup_vault_arn != null ? var.cross_region_backup_vault_arn : aws_backup_vault.main.arn

      lifecycle {
        cold_storage_after = var.cold_storage_after_days
        delete_after       = var.monthly_backup_retention_days
      }
    }
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-plan"
    Environment = var.environment
    Purpose     = "Automated-Backup"
  }
}

# IAM role for AWS Backup service
resource "aws_iam_role" "backup_role" {
  name = "${var.app_name}-${var.environment}-backup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-role"
    Environment = var.environment
    Purpose     = "Backup-Service"
  }
}

# Attach AWS managed policies for backup service
resource "aws_iam_role_policy_attachment" "backup_service_role" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_iam_role_policy_attachment" "backup_service_role_s3" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForS3Backup"
}

resource "aws_iam_role_policy_attachment" "backup_service_role_restore" {
  role       = aws_iam_role.backup_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForRestores"
}

# Backup selection for RDS instances
resource "aws_backup_selection" "rds_backup" {
  count = var.rds_instance_arn != null ? 1 : 0

  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "${var.app_name}-${var.environment}-rds-backup-selection"
  plan_id      = aws_backup_plan.main.id

  resources = [var.rds_instance_arn]

  condition {
    string_equals {
      key   = "aws:ResourceTag/Environment"
      value = var.environment
    }
  }

  condition {
    string_equals {
      key   = "aws:ResourceTag/BackupRequired"
      value = "true"
    }
  }
}

# Backup selection for EBS volumes
resource "aws_backup_selection" "ebs_backup" {
  count = length(var.ebs_volume_arns) > 0 ? 1 : 0

  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "${var.app_name}-${var.environment}-ebs-backup-selection"
  plan_id      = aws_backup_plan.main.id

  resources = var.ebs_volume_arns

  condition {
    string_equals {
      key   = "aws:ResourceTag/Environment"
      value = var.environment
    }
  }

  condition {
    string_equals {
      key   = "aws:ResourceTag/BackupRequired"
      value = "true"
    }
  }
}

# Backup selection for S3 buckets
resource "aws_backup_selection" "s3_backup" {
  count = length(var.s3_bucket_arns) > 0 ? 1 : 0

  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "${var.app_name}-${var.environment}-s3-backup-selection"
  plan_id      = aws_backup_plan.main.id

  resources = var.s3_bucket_arns

  condition {
    string_equals {
      key   = "aws:ResourceTag/Environment"
      value = var.environment
    }
  }

  condition {
    string_equals {
      key   = "aws:ResourceTag/BackupRequired"
      value = "true"
    }
  }
}

# Backup selection for EFS file systems
resource "aws_backup_selection" "efs_backup" {
  count = length(var.efs_file_system_arns) > 0 ? 1 : 0

  iam_role_arn = aws_iam_role.backup_role.arn
  name         = "${var.app_name}-${var.environment}-efs-backup-selection"
  plan_id      = aws_backup_plan.main.id

  resources = var.efs_file_system_arns

  condition {
    string_equals {
      key   = "aws:ResourceTag/Environment"
      value = var.environment
    }
  }

  condition {
    string_equals {
      key   = "aws:ResourceTag/BackupRequired"
      value = "true"
    }
  }
}

# CloudWatch alarms for backup monitoring
resource "aws_cloudwatch_metric_alarm" "backup_job_failed" {
  alarm_name          = "${var.app_name}-${var.environment}-backup-job-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfBackupJobsFailed"
  namespace           = "AWS/Backup"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors failed backup jobs"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []
  ok_actions          = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  dimensions = {
    BackupVaultName = aws_backup_vault.main.name
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-job-failed-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "backup_job_expired" {
  alarm_name          = "${var.app_name}-${var.environment}-backup-job-expired"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfBackupJobsExpired"
  namespace           = "AWS/Backup"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors expired backup jobs"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  dimensions = {
    BackupVaultName = aws_backup_vault.main.name
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-job-expired-alarm"
    Environment = var.environment
  }
}

# EventBridge rule for backup job state changes
resource "aws_cloudwatch_event_rule" "backup_job_state_change" {
  name        = "${var.app_name}-${var.environment}-backup-job-state-change"
  description = "Capture backup job state changes"

  event_pattern = jsonencode({
    source      = ["aws.backup"]
    detail-type = ["Backup Job State Change"]
    detail = {
      state = ["FAILED", "EXPIRED", "STOPPED"]
    }
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-job-state-change-rule"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "backup_job_sns" {
  count     = var.sns_topic_arn != null ? 1 : 0
  rule      = aws_cloudwatch_event_rule.backup_job_state_change.name
  target_id = "SendToSNS"
  arn       = var.sns_topic_arn
}

# S3 bucket for backup reports and logs
resource "aws_s3_bucket" "backup_reports" {
  count  = var.enable_backup_reports ? 1 : 0
  bucket = "${var.app_name}-${var.environment}-backup-reports-${random_id.backup_reports_suffix[0].hex}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-reports"
    Environment = var.environment
    Purpose     = "Backup-Reports"
  }
}

resource "random_id" "backup_reports_suffix" {
  count       = var.enable_backup_reports ? 1 : 0
  byte_length = 4
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backup_reports" {
  count  = var.enable_backup_reports ? 1 : 0
  bucket = aws_s3_bucket.backup_reports[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "backup_reports" {
  count  = var.enable_backup_reports ? 1 : 0
  bucket = aws_s3_bucket.backup_reports[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "backup_reports" {
  count  = var.enable_backup_reports ? 1 : 0
  bucket = aws_s3_bucket.backup_reports[0].id

  rule {
    id     = "backup_reports_lifecycle"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 2555  # 7 years for financial compliance
    }
  }
}

# Lambda function for backup validation and reporting
resource "aws_lambda_function" "backup_validator" {
  count = var.enable_backup_validation ? 1 : 0

  filename         = "backup_validator.zip"
  function_name    = "${var.app_name}-${var.environment}-backup-validator"
  role            = aws_iam_role.backup_validator_role[0].arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.backup_validator_zip[0].output_base64sha256
  runtime         = "python3.9"
  timeout         = 300

  environment {
    variables = {
      BACKUP_VAULT_NAME = aws_backup_vault.main.name
      SNS_TOPIC_ARN     = var.sns_topic_arn
      S3_BUCKET_NAME    = var.enable_backup_reports ? aws_s3_bucket.backup_reports[0].bucket : ""
    }
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-validator"
    Environment = var.environment
    Purpose     = "Backup-Validation"
  }
}

# Lambda function code for backup validation
data "archive_file" "backup_validator_zip" {
  count = var.enable_backup_validation ? 1 : 0

  type        = "zip"
  output_path = "backup_validator.zip"
  source {
    content = templatefile("${path.module}/backup_validator.py", {
      app_name    = var.app_name
      environment = var.environment
    })
    filename = "index.py"
  }
}

# IAM role for backup validator Lambda
resource "aws_iam_role" "backup_validator_role" {
  count = var.enable_backup_validation ? 1 : 0
  name  = "${var.app_name}-${var.environment}-backup-validator-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-validator-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "backup_validator_policy" {
  count = var.enable_backup_validation ? 1 : 0
  name  = "${var.app_name}-${var.environment}-backup-validator-policy"
  role  = aws_iam_role.backup_validator_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "backup:ListRecoveryPoints",
          "backup:DescribeRecoveryPoint",
          "backup:ListBackupJobs",
          "backup:DescribeBackupJob"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = var.sns_topic_arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = var.enable_backup_reports ? "${aws_s3_bucket.backup_reports[0].arn}/*" : ""
      }
    ]
  })
}

# EventBridge rule to trigger backup validation
resource "aws_cloudwatch_event_rule" "backup_validation_schedule" {
  count = var.enable_backup_validation ? 1 : 0

  name                = "${var.app_name}-${var.environment}-backup-validation-schedule"
  description         = "Trigger backup validation daily"
  schedule_expression = "cron(0 6 * * ? *)"  # Daily at 6 AM UTC

  tags = {
    Name        = "${var.app_name}-${var.environment}-backup-validation-schedule"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "backup_validation_lambda" {
  count     = var.enable_backup_validation ? 1 : 0
  rule      = aws_cloudwatch_event_rule.backup_validation_schedule[0].name
  target_id = "BackupValidationLambda"
  arn       = aws_lambda_function.backup_validator[0].arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  count = var.enable_backup_validation ? 1 : 0

  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.backup_validator[0].function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.backup_validation_schedule[0].arn
}

# Disaster recovery documentation
resource "local_file" "disaster_recovery_runbook" {
  count = var.create_dr_documentation ? 1 : 0

  content = templatefile("${path.module}/disaster_recovery_runbook.md", {
    app_name              = var.app_name
    environment           = var.environment
    backup_vault_name     = aws_backup_vault.main.name
    backup_plan_id        = aws_backup_plan.main.id
    cross_region_vault    = var.cross_region_backup_vault_arn
    daily_retention       = var.daily_backup_retention_days
    weekly_retention      = var.weekly_backup_retention_days
    monthly_retention     = var.monthly_backup_retention_days
  })
  
  filename = "${path.root}/disaster_recovery_runbook_${var.app_name}_${var.environment}.md"
}

