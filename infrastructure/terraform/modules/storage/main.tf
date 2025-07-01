# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Random suffix for bucket names to ensure uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Main S3 bucket for application data
resource "aws_s3_bucket" "main" {
  bucket = "${var.app_name}-${var.environment}-data-${random_id.bucket_suffix.hex}"

  tags = {
    Name                = "${var.app_name}-${var.environment}-data-bucket"
    Environment         = var.environment
    Purpose             = "Application-Data"
    SecurityCompliance  = "Financial"
    DataClassification  = "Confidential"
    BackupRequired      = "true"
  }
}

# S3 bucket versioning for data protection
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  
  versioning_configuration {
    status     = var.enable_versioning ? "Enabled" : "Suspended"
    mfa_delete = var.enable_mfa_delete ? "Enabled" : "Disabled"
  }
}

# S3 bucket encryption with KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.enable_encryption ? var.kms_key_id : null
      sse_algorithm     = var.enable_encryption ? "aws:kms" : "AES256"
    }
    bucket_key_enabled = var.enable_encryption
  }
}

# S3 bucket public access block for security
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket lifecycle configuration for cost optimization and compliance
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  count  = var.enable_lifecycle_policy ? 1 : 0
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "main_lifecycle_rule"
    status = "Enabled"

    # Transition to IA after specified days
    transition {
      days          = var.transition_to_ia_days
      storage_class = "STANDARD_IA"
    }

    # Transition to Glacier after specified days
    transition {
      days          = var.transition_to_glacier_days
      storage_class = "GLACIER"
    }

    # Transition to Deep Archive for long-term retention
    transition {
      days          = var.transition_to_glacier_days + 90
      storage_class = "DEEP_ARCHIVE"
    }

    # Delete objects after retention period
    dynamic "expiration" {
      for_each = var.expiration_days > 0 ? [1] : []
      content {
        days = var.expiration_days
      }
      
    }

    # Clean up incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }

    # Manage non-current versions
    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_transition {
      noncurrent_days = 60
      storage_class   = "GLACIER"
    }

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

# S3 bucket notification configuration for monitoring
resource "aws_s3_bucket_notification" "main" {
  bucket = aws_s3_bucket.main.id

  cloudwatch_configuration {
    cloudwatch_configuration_id = "EntireBucket"
    events                      = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }
}

# S3 bucket logging for audit trail
resource "aws_s3_bucket" "access_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = "${var.app_name}-${var.environment}-access-logs-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-access-logs"
    Environment = var.environment
    Purpose     = "Access-Logging"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "access_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.access_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_id
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "access_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.access_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "access_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.access_logs[0].id

  rule {
    id     = "access_logs_lifecycle"
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

# S3 bucket logging configuration
resource "aws_s3_bucket_logging" "main" {
  count  = var.enable_server_access_logging ? 1 : 0
  bucket = aws_s3_bucket.main.id

  target_bucket = aws_s3_bucket.access_logs[0].id
  target_prefix = "access-logs/"
}

# S3 bucket policy for secure access
resource "aws_s3_bucket_policy" "main" {
  bucket = aws_s3_bucket.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyInsecureConnections"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      },
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.main.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = var.enable_encryption ? "aws:kms" : "AES256"
          }
        }
      },
      {
        Sid    = "RequireKMSEncryption"
        Effect = var.enable_encryption ? "Deny" : "Allow"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.main.arn}/*"
        Condition = var.enable_encryption ? {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption-aws-kms-key-id" = var.kms_key_id
          }
        } : {}
      }
    ]
  })
}

# CloudFront distribution for secure content delivery
resource "aws_cloudfront_distribution" "main" {
  count = var.enable_cloudfront ? 1 : 0

  origin {
    domain_name              = aws_s3_bucket.main.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.main.bucket}"
    origin_access_control_id = aws_cloudfront_origin_access_control.main[0].id
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CloudFront distribution for ${var.app_name} ${var.environment}"
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.main.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  web_acl_id = var.waf_web_acl_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-cloudfront"
    Environment = var.environment
    Purpose     = "Content-Delivery"
  }
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "main" {
  count = var.enable_cloudfront ? 1 : 0

  name                              = "${var.app_name}-${var.environment}-oac"
  description                       = "Origin Access Control for ${var.app_name} ${var.environment}"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# Update S3 bucket policy to allow CloudFront access
resource "aws_s3_bucket_policy" "cloudfront_access" {
  count  = var.enable_cloudfront ? 1 : 0
  bucket = aws_s3_bucket.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${aws_s3_bucket.main.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.main[0].arn
          }
        }
      },
      {
        Sid    = "DenyInsecureConnections"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:*"
        Resource = [
          aws_s3_bucket.main.arn,
          "${aws_s3_bucket.main.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })

  depends_on = [aws_cloudfront_distribution.main]
}

# S3 bucket for static website hosting (if enabled)
resource "aws_s3_bucket" "website" {
  count  = var.enable_static_website ? 1 : 0
  bucket = "${var.app_name}-${var.environment}-website-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-website"
    Environment = var.environment
    Purpose     = "Static-Website"
  }
}

resource "aws_s3_bucket_website_configuration" "website" {
  count  = var.enable_static_website ? 1 : 0
  bucket = aws_s3_bucket.website[0].id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "website" {
  count  = var.enable_static_website ? 1 : 0
  bucket = aws_s3_bucket.website[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_id
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  count  = var.enable_static_website ? 1 : 0
  bucket = aws_s3_bucket.website[0].id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# S3 bucket for backups
resource "aws_s3_bucket" "backups" {
  count  = var.enable_backup_bucket ? 1 : 0
  bucket = "${var.app_name}-${var.environment}-backups-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "${var.app_name}-${var.environment}-backups"
    Environment = var.environment
    Purpose     = "Backup-Storage"
  }
}

resource "aws_s3_bucket_versioning" "backups" {
  count  = var.enable_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "backups" {
  count  = var.enable_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_id
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "backups" {
  count  = var.enable_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "backups" {
  count  = var.enable_backup_bucket ? 1 : 0
  bucket = aws_s3_bucket.backups[0].id

  rule {
    id     = "backup_lifecycle_rule"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    # Keep backups for 7 years for financial compliance
    expiration {
      days = 2555
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# CloudWatch metrics for S3 bucket monitoring
resource "aws_cloudwatch_metric_alarm" "bucket_size" {
  alarm_name          = "${var.app_name}-${var.environment}-s3-bucket-size"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "BucketSizeBytes"
  namespace           = "AWS/S3"
  period              = "86400"  # Daily
  statistic           = "Average"
  threshold           = var.bucket_size_alarm_threshold
  alarm_description   = "This metric monitors S3 bucket size"
  alarm_actions       = var.sns_topic_arn != null ? [var.sns_topic_arn] : []

  dimensions = {
    BucketName  = aws_s3_bucket.main.bucket
    StorageType = "StandardStorage"
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-s3-bucket-size-alarm"
    Environment = var.environment
  }
}

# S3 bucket inventory for compliance and cost optimization
resource "aws_s3_bucket_inventory" "main" {
  count  = var.enable_inventory ? 1 : 0
  bucket = aws_s3_bucket.main.id
  name   = "EntireBucketInventory"

  included_object_versions = "All"

  schedule {
    frequency = "Daily"
  }

  destination {
    bucket {
      format     = "CSV"
      bucket_arn = aws_s3_bucket.main.arn
      prefix     = "inventory/"
      encryption {
        sse_kms {
          key_id = var.kms_key_id
        }
      }
    }
  }

  optional_fields = [
    "Size",
    "LastModifiedDate",
    "StorageClass",
    "ETag",
    "IsMultipartUploaded",
    "ReplicationStatus",
    "EncryptionStatus",
    "ObjectLockRetainUntilDate",
    "ObjectLockMode",
    "ObjectLockLegalHoldStatus",
    "IntelligentTieringAccessTier"
  ]
}

