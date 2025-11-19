# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/aws/application/${var.app_name}-${var.environment}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-app-logs"
    Environment = var.environment
    Purpose     = "Application-Logging"
  }
}

# CloudWatch Log Group for system logs
resource "aws_cloudwatch_log_group" "system_logs" {
  name              = "/aws/ec2/${var.app_name}-${var.environment}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-system-logs"
    Environment = var.environment
    Purpose     = "System-Logging"
  }
}

# CloudWatch Log Group for security logs
resource "aws_cloudwatch_log_group" "security_logs" {
  name              = "/aws/security/${var.app_name}-${var.environment}"
  retention_in_days = var.log_retention_days * 2  # Keep security logs longer
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-security-logs"
    Environment = var.environment
    Purpose     = "Security-Logging"
  }
}

# CloudWatch Log Group for audit logs
resource "aws_cloudwatch_log_group" "audit_logs" {
  name              = "/aws/audit/${var.app_name}-${var.environment}"
  retention_in_days = 2555  # 7 years for financial compliance
  kms_key_id        = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-audit-logs"
    Environment = var.environment
    Purpose     = "Audit-Logging"
  }
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  name              = var.sns_topic_name
  kms_master_key_id = var.kms_key_id

  tags = {
    Name        = "${var.app_name}-${var.environment}-alerts"
    Environment = var.environment
    Purpose     = "Alerting"
  }
}

# SNS Topic Policy
resource "aws_sns_topic_policy" "alerts" {
  arn = aws_sns_topic.alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "cloudwatch.amazonaws.com",
            "events.amazonaws.com"
          ]
        }
        Action = [
          "SNS:Publish"
        ]
        Resource = aws_sns_topic.alerts.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}

# SNS Topic Subscriptions for email alerts
resource "aws_sns_topic_subscription" "email_alerts" {
  count     = length(var.alert_email_endpoints)
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email_endpoints[count.index]
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.app_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", var.load_balancer_arn != null ? split("/", var.load_balancer_arn)[1] : ""],
            [".", "TargetResponseTime", ".", "."],
            [".", "HTTPCode_Target_2XX_Count", ".", "."],
            [".", "HTTPCode_Target_4XX_Count", ".", "."],
            [".", "HTTPCode_Target_5XX_Count", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "Application Load Balancer Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", "${var.app_name}-${var.environment}-asg"],
            [".", "NetworkIn", ".", "."],
            [".", "NetworkOut", ".", "."],
            [".", "DiskReadOps", ".", "."],
            [".", "DiskWriteOps", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "EC2 Instance Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = var.rds_instance_id != null ? [
            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", var.rds_instance_id],
            [".", "DatabaseConnections", ".", "."],
            [".", "ReadLatency", ".", "."],
            [".", "WriteLatency", ".", "."],
            [".", "ReadIOPS", ".", "."],
            [".", "WriteIOPS", ".", "."]
          ] : []
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "RDS Database Metrics"
          period  = 300
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 18
        width  = 24
        height = 6

        properties = {
          query   = "SOURCE '${aws_cloudwatch_log_group.app_logs.name}' | fields @timestamp, @message | sort @timestamp desc | limit 100"
          region  = data.aws_region.current.name
          title   = "Recent Application Logs"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-dashboard"
    Environment = var.environment
    Purpose     = "Monitoring-Dashboard"
  }
}

# CloudWatch Alarms for Application Load Balancer
resource "aws_cloudwatch_metric_alarm" "alb_response_time" {
  count               = var.load_balancer_arn != null ? 1 : 0
  alarm_name          = "${var.app_name}-${var.environment}-alb-response-time"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "TargetResponseTime"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Average"
  threshold           = "1"
  alarm_description   = "This metric monitors ALB response time"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = split("/", var.load_balancer_arn)[1]
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-alb-response-time-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_errors" {
  count               = var.load_balancer_arn != null ? 1 : 0
  alarm_name          = "${var.app_name}-${var.environment}-alb-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors ALB 5XX errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    LoadBalancer = split("/", var.load_balancer_arn)[1]
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-alb-5xx-errors-alarm"
    Environment = var.environment
  }
}

# CloudWatch Alarms for RDS
resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  count               = var.rds_instance_id != null ? 1 : 0
  alarm_name          = "${var.app_name}-${var.environment}-rds-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS CPU utilization"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-rds-cpu-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  count               = var.rds_instance_id != null ? 1 : 0
  alarm_name          = "${var.app_name}-${var.environment}-rds-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors RDS database connections"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  tags = {
    Name        = "${var.app_name}-${var.environment}-rds-connections-alarm"
    Environment = var.environment
  }
}

# CloudWatch Alarms for Security Events
resource "aws_cloudwatch_metric_alarm" "failed_logins" {
  alarm_name          = "${var.app_name}-${var.environment}-failed-logins"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "FailedLoginAttempts"
  namespace           = "Custom/Security"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors failed login attempts"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-failed-logins-alarm"
    Environment = var.environment
  }
}

# CloudWatch Log Metric Filters for Security Events
resource "aws_cloudwatch_log_metric_filter" "failed_ssh_logins" {
  name           = "${var.app_name}-${var.environment}-failed-ssh-logins"
  log_group_name = aws_cloudwatch_log_group.security_logs.name
  pattern        = "[timestamp, request_id, event_type=\"FAILED_LOGIN\", ...]"

  metric_transformation {
    name      = "FailedLoginAttempts"
    namespace = "Custom/Security"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "root_access" {
  name           = "${var.app_name}-${var.environment}-root-access"
  log_group_name = aws_cloudwatch_log_group.security_logs.name
  pattern        = "[timestamp, request_id, event_type=\"ROOT_ACCESS\", ...]"

  metric_transformation {
    name      = "RootAccessAttempts"
    namespace = "Custom/Security"
    value     = "1"
  }
}

# EventBridge Rules for Security Events
resource "aws_cloudwatch_event_rule" "guardduty_findings" {
  name        = "${var.app_name}-${var.environment}-guardduty-findings"
  description = "Capture GuardDuty findings"

  event_pattern = jsonencode({
    source      = ["aws.guardduty"]
    detail-type = ["GuardDuty Finding"]
    detail = {
      severity = [7.0, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9, 9.0, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 10.0]
    }
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-guardduty-findings-rule"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "guardduty_sns" {
  rule      = aws_cloudwatch_event_rule.guardduty_findings.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.alerts.arn
}

# EventBridge Rule for Config Compliance
resource "aws_cloudwatch_event_rule" "config_compliance" {
  name        = "${var.app_name}-${var.environment}-config-compliance"
  description = "Capture AWS Config compliance changes"

  event_pattern = jsonencode({
    source      = ["aws.config"]
    detail-type = ["Config Rules Compliance Change"]
    detail = {
      newEvaluationResult = {
        complianceType = ["NON_COMPLIANT"]
      }
    }
  })

  tags = {
    Name        = "${var.app_name}-${var.environment}-config-compliance-rule"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_event_target" "config_sns" {
  rule      = aws_cloudwatch_event_rule.config_compliance.name
  target_id = "SendToSNS"
  arn       = aws_sns_topic.alerts.arn
}

# Custom Metrics for Application Performance
resource "aws_cloudwatch_log_metric_filter" "application_errors" {
  name           = "${var.app_name}-${var.environment}-application-errors"
  log_group_name = aws_cloudwatch_log_group.app_logs.name
  pattern        = "[timestamp, request_id, level=\"ERROR\", ...]"

  metric_transformation {
    name      = "ApplicationErrors"
    namespace = "Custom/Application"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "application_errors" {
  alarm_name          = "${var.app_name}-${var.environment}-application-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApplicationErrors"
  namespace           = "Custom/Application"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors application errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  treat_missing_data  = "notBreaching"

  tags = {
    Name        = "${var.app_name}-${var.environment}-application-errors-alarm"
    Environment = var.environment
  }
}

# CloudWatch Insights Queries for common investigations
resource "aws_cloudwatch_query_definition" "error_analysis" {
  name = "${var.app_name}-${var.environment}-error-analysis"

  log_group_names = [
    aws_cloudwatch_log_group.app_logs.name
  ]

  query_string = <<EOF
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() by bin(5m)
| sort @timestamp desc
EOF
}

resource "aws_cloudwatch_query_definition" "performance_analysis" {
  name = "${var.app_name}-${var.environment}-performance-analysis"

  log_group_names = [
    aws_cloudwatch_log_group.app_logs.name
  ]

  query_string = <<EOF
fields @timestamp, @message
| filter @message like /response_time/
| parse @message "response_time=* " as response_time
| stats avg(response_time), max(response_time), min(response_time) by bin(5m)
| sort @timestamp desc
EOF
}

# X-Ray Tracing (if enabled)
resource "aws_xray_sampling_rule" "main" {
  count = var.enable_xray_tracing ? 1 : 0

  rule_name      = "${var.app_name}-${var.environment}-sampling-rule"
  priority       = 9000
  version        = 1
  reservoir_size = 1
  fixed_rate     = 0.1
  url_path       = "*"
  host           = "*"
  http_method    = "*"
  service_type   = "*"
  service_name   = "*"
  resource_arn   = "*"

  tags = {
    Name        = "${var.app_name}-${var.environment}-xray-sampling-rule"
    Environment = var.environment
  }
}
