# Auto Scaling Group Outputs
output "auto_scaling_group_id" {
  description = "ID of the Auto Scaling Group"
  value       = aws_autoscaling_group.app.id
}

output "auto_scaling_group_arn" {
  description = "ARN of the Auto Scaling Group"
  value       = aws_autoscaling_group.app.arn
}

output "auto_scaling_group_name" {
  description = "Name of the Auto Scaling Group"
  value       = aws_autoscaling_group.app.name
}

output "auto_scaling_group_min_size" {
  description = "Minimum size of the Auto Scaling Group"
  value       = aws_autoscaling_group.app.min_size
}

output "auto_scaling_group_max_size" {
  description = "Maximum size of the Auto Scaling Group"
  value       = aws_autoscaling_group.app.max_size
}

output "auto_scaling_group_desired_capacity" {
  description = "Desired capacity of the Auto Scaling Group"
  value       = aws_autoscaling_group.app.desired_capacity
}

# Launch Template Outputs
output "launch_template_id" {
  description = "ID of the Launch Template"
  value       = aws_launch_template.app.id
}

output "launch_template_arn" {
  description = "ARN of the Launch Template"
  value       = aws_launch_template.app.arn
}

output "launch_template_latest_version" {
  description = "Latest version of the Launch Template"
  value       = aws_launch_template.app.latest_version
}

# Load Balancer Outputs
output "load_balancer_id" {
  description = "ID of the Application Load Balancer"
  value       = aws_lb.app.id
}

output "load_balancer_arn" {
  description = "ARN of the Application Load Balancer"
  value       = aws_lb.app.arn
}

output "load_balancer_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = aws_lb.app.dns_name
}

output "load_balancer_zone_id" {
  description = "Zone ID of the Application Load Balancer"
  value       = aws_lb.app.zone_id
}

output "load_balancer_hosted_zone_id" {
  description = "Hosted zone ID of the Application Load Balancer"
  value       = aws_lb.app.zone_id
}

# Target Group Outputs
output "target_group_id" {
  description = "ID of the Target Group"
  value       = aws_lb_target_group.app.id
}

output "target_group_arn" {
  description = "ARN of the Target Group"
  value       = aws_lb_target_group.app.arn
}

output "target_group_name" {
  description = "Name of the Target Group"
  value       = aws_lb_target_group.app.name
}

# Listener Outputs
output "https_listener_arn" {
  description = "ARN of the HTTPS listener"
  value       = aws_lb_listener.https.arn
}

output "http_listener_arn" {
  description = "ARN of the HTTP listener"
  value       = aws_lb_listener.http.arn
}

# IAM Outputs
output "ec2_iam_role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.arn
}

output "ec2_iam_role_name" {
  description = "Name of the EC2 IAM role"
  value       = aws_iam_role.ec2_role.name
}

output "ec2_instance_profile_arn" {
  description = "ARN of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_profile.arn
}

output "ec2_instance_profile_name" {
  description = "Name of the EC2 instance profile"
  value       = aws_iam_instance_profile.ec2_profile.name
}

# Auto Scaling Policy Outputs
output "scale_up_policy_arn" {
  description = "ARN of the scale up policy"
  value       = aws_autoscaling_policy.scale_up.arn
}

output "scale_down_policy_arn" {
  description = "ARN of the scale down policy"
  value       = aws_autoscaling_policy.scale_down.arn
}

# CloudWatch Alarm Outputs
output "cpu_high_alarm_arn" {
  description = "ARN of the CPU high alarm"
  value       = aws_cloudwatch_metric_alarm.cpu_high.arn
}

output "cpu_low_alarm_arn" {
  description = "ARN of the CPU low alarm"
  value       = aws_cloudwatch_metric_alarm.cpu_low.arn
}

# S3 Bucket Outputs (for ALB logs)
output "alb_logs_bucket_name" {
  description = "Name of the S3 bucket for ALB access logs"
  value       = aws_s3_bucket.alb_logs.bucket
}

output "alb_logs_bucket_arn" {
  description = "ARN of the S3 bucket for ALB access logs"
  value       = aws_s3_bucket.alb_logs.arn
}

# Instance Information (for reference)
output "instance_ids" {
  description = "List of instance IDs (note: these are dynamic in ASG)"
  value       = []  # ASG instances are dynamic
}

output "instance_private_ips" {
  description = "List of private IPs (note: these are dynamic in ASG)"
  value       = []  # ASG instances are dynamic
}

output "ebs_volume_ids" {
  description = "List of EBS volume IDs (note: these are dynamic in ASG)"
  value       = []  # ASG volumes are dynamic
}

# AMI Information
output "ami_id" {
  description = "ID of the AMI used for instances"
  value       = data.aws_ami.amazon_linux.id
}

output "ami_name" {
  description = "Name of the AMI used for instances"
  value       = data.aws_ami.amazon_linux.name
}

# Network Information
output "availability_zones" {
  description = "Availability zones where instances can be launched"
  value       = aws_autoscaling_group.app.availability_zones
}

# Security Information
output "security_group_ids" {
  description = "Security group IDs attached to instances"
  value       = var.security_group_ids
}

# Compute Summary
output "compute_summary" {
  description = "Summary of compute configuration"
  value = {
    instance_type              = var.instance_type
    min_size                  = var.min_size
    max_size                  = var.max_size
    desired_capacity          = var.desired_capacity
    health_check_type         = var.health_check_type
    detailed_monitoring_enabled = var.enable_detailed_monitoring
    ebs_encryption_enabled    = var.enable_ebs_encryption
    imdsv2_enforced          = var.enable_imdsv2_only
    load_balancer_type       = "application"
    ssl_enabled              = var.ssl_certificate_arn != null
    access_logs_enabled      = var.enable_access_logs
    auto_scaling_enabled     = true
    high_availability        = length(var.private_subnet_ids) >= 2
  }
}

# Compliance Status
output "compliance_status" {
  description = "Compliance status indicators for compute resources"
  value = {
    encryption_at_rest       = var.enable_ebs_encryption
    detailed_monitoring      = var.enable_detailed_monitoring
    secure_metadata_service  = var.enable_imdsv2_only
    access_logging          = var.enable_access_logs
    high_availability       = length(var.private_subnet_ids) >= 2
    auto_scaling_configured = true
    health_checks_enabled   = true
    ssl_termination         = var.ssl_certificate_arn != null
    iam_roles_configured    = true
    security_groups_applied = length(var.security_group_ids) > 0
  }
}

