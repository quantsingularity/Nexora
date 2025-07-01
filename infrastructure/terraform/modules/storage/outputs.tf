# Main S3 Bucket Outputs
output "s3_bucket_id" {
  description = "ID of the main S3 bucket"
  value       = aws_s3_bucket.main.id
}

output "s3_bucket_name" {
  description = "Name of the main S3 bucket"
  value       = aws_s3_bucket.main.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the main S3 bucket"
  value       = aws_s3_bucket.main.arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the main S3 bucket"
  value       = aws_s3_bucket.main.bucket_domain_name
}

output "s3_bucket_regional_domain_name" {
  description = "Regional domain name of the main S3 bucket"
  value       = aws_s3_bucket.main.bucket_regional_domain_name
}

output "s3_bucket_hosted_zone_id" {
  description = "Hosted zone ID of the main S3 bucket"
  value       = aws_s3_bucket.main.hosted_zone_id
}

output "s3_bucket_region" {
  description = "Region of the main S3 bucket"
  value       = aws_s3_bucket.main.region
}

# Access Logs Bucket Outputs
output "access_logs_bucket_name" {
  description = "Name of the access logs S3 bucket"
  value       = var.enable_access_logging ? aws_s3_bucket.access_logs[0].bucket : null
}

output "access_logs_bucket_arn" {
  description = "ARN of the access logs S3 bucket"
  value       = var.enable_access_logging ? aws_s3_bucket.access_logs[0].arn : null
}

# Website Bucket Outputs
output "website_bucket_name" {
  description = "Name of the website S3 bucket"
  value       = var.enable_static_website ? aws_s3_bucket.website[0].bucket : null
}

output "website_bucket_arn" {
  description = "ARN of the website S3 bucket"
  value       = var.enable_static_website ? aws_s3_bucket.website[0].arn : null
}

output "website_endpoint" {
  description = "Website endpoint of the S3 bucket"
  value       = var.enable_static_website ? aws_s3_bucket_website_configuration.website[0].website_endpoint : null
}

output "website_domain" {
  description = "Website domain of the S3 bucket"
  value       = var.enable_static_website ? aws_s3_bucket_website_configuration.website[0].website_domain : null
}

# Backup Bucket Outputs
output "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  value       = var.enable_backup_bucket ? aws_s3_bucket.backups[0].bucket : null
}

output "backup_bucket_arn" {
  description = "ARN of the backup S3 bucket"
  value       = var.enable_backup_bucket ? aws_s3_bucket.backups[0].arn : null
}

# CloudFront Distribution Outputs
output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.main[0].id : null
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.main[0].arn : null
}

output "cloudfront_distribution_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.main[0].domain_name : null
}

output "cloudfront_distribution_hosted_zone_id" {
  description = "Hosted zone ID of the CloudFront distribution"
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.main[0].hosted_zone_id : null
}

output "cloudfront_distribution_status" {
  description = "Status of the CloudFront distribution"
  value       = var.enable_cloudfront ? aws_cloudfront_distribution.main[0].status : null
}

# CloudFront Origin Access Control Outputs
output "cloudfront_oac_id" {
  description = "ID of the CloudFront Origin Access Control"
  value       = var.enable_cloudfront ? aws_cloudfront_origin_access_control.main[0].id : null
}

# CloudWatch Alarm Outputs
output "bucket_size_alarm_arn" {
  description = "ARN of the S3 bucket size alarm"
  value       = aws_cloudwatch_metric_alarm.bucket_size.arn
}

# Storage Configuration Summary
output "storage_summary" {
  description = "Summary of storage configuration"
  value = {
    main_bucket_name              = aws_s3_bucket.main.bucket
    encryption_enabled            = var.enable_encryption
    versioning_enabled           = var.enable_versioning
    lifecycle_policy_enabled     = var.enable_lifecycle_policy
    access_logging_enabled       = var.enable_access_logging
    server_access_logging_enabled = var.enable_server_access_logging
    cloudfront_enabled           = var.enable_cloudfront
    static_website_enabled       = var.enable_static_website
    backup_bucket_enabled        = var.enable_backup_bucket
    inventory_enabled            = var.enable_inventory
    intelligent_tiering_enabled  = var.enable_intelligent_tiering
    transfer_acceleration_enabled = var.enable_transfer_acceleration
    object_lock_enabled          = var.enable_object_lock
    cross_region_replication_enabled = var.enable_cross_region_replication
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance status indicators for storage"
  value = {
    encryption_at_rest           = var.enable_encryption
    encryption_in_transit        = true  # HTTPS enforced by bucket policy
    versioning_enabled          = var.enable_versioning
    access_logging_enabled      = var.enable_access_logging
    lifecycle_management        = var.enable_lifecycle_policy
    backup_strategy             = var.enable_backup_bucket
    data_retention_policy       = var.expiration_days > 0
    public_access_blocked       = true  # Public access blocked by default
    secure_transport_required   = true  # HTTPS required by bucket policy
    inventory_tracking          = var.enable_inventory
    object_lock_compliance      = var.enable_object_lock
    cross_region_backup         = var.enable_cross_region_replication
    intelligent_cost_optimization = var.enable_intelligent_tiering
    cdn_protection              = var.enable_cloudfront
    waf_protection              = var.enable_cloudfront && var.waf_web_acl_id != null
  }
}

# Cost Optimization Information
output "cost_optimization" {
  description = "Cost optimization features enabled"
  value = {
    lifecycle_transitions       = var.enable_lifecycle_policy
    intelligent_tiering        = var.enable_intelligent_tiering
    storage_class_transitions  = {
      to_ia_days      = var.transition_to_ia_days
      to_glacier_days = var.transition_to_glacier_days
      expiration_days = var.expiration_days
    }
    cloudfront_caching         = var.enable_cloudfront
    transfer_acceleration      = var.enable_transfer_acceleration
    multipart_upload_threshold = var.multipart_upload_threshold
  }
}

# Security Features
output "security_features" {
  description = "Security features enabled"
  value = {
    kms_encryption             = var.enable_encryption
    versioning                = var.enable_versioning
    mfa_delete                = var.enable_mfa_delete
    public_access_blocked     = true
    secure_transport_only     = true
    object_lock               = var.enable_object_lock
    access_logging            = var.enable_access_logging
    cloudfront_oac            = var.enable_cloudfront
    waf_integration           = var.enable_cloudfront && var.waf_web_acl_id != null
  }
}

# Bucket URLs for Applications
output "bucket_urls" {
  description = "Bucket URLs for application use"
  value = {
    s3_url        = "s3://${aws_s3_bucket.main.bucket}"
    https_url     = "https://${aws_s3_bucket.main.bucket_regional_domain_name}"
    cloudfront_url = var.enable_cloudfront ? "https://${aws_cloudfront_distribution.main[0].domain_name}" : null
    website_url   = var.enable_static_website ? "http://${aws_s3_bucket_website_configuration.website[0].website_endpoint}" : null
  }
}

