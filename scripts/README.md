# Nexora Automation Scripts Documentation

This documentation provides an overview of the automation scripts created for the Nexora repository, including their purpose, usage, and implementation details.

## Overview

After a comprehensive review of the Nexora repository, three high-priority automation opportunities were identified and implemented:

1. **Environment Health Check Script** - Automatically verifies the health of development, testing, and production environments
2. **Deployment Validation Script** - Comprehensively validates deployments and catches issues early
3. **Compliance Report Generator** - Streamlines HIPAA and healthcare regulatory compliance reporting

These scripts address key automation needs in the healthcare technology domain, focusing on reliability, compliance, and operational efficiency.

## Scripts

### 1. Environment Health Check Script

**Purpose**: Monitors and reports on the health of Nexora environments (development, staging, production) by checking system resources, services, databases, API endpoints, and Kubernetes resources.

**Features**:

- Comprehensive environment health monitoring
- Configurable thresholds and checks
- Multiple output formats (JSON, HTML, text)
- Detailed reporting with recommendations
- Support for multiple environments

**Usage**:

```bash
python environment_health_check.py --config /path/to/config.yaml --env [dev|staging|prod] [options]

Options:
  --config PATH           Path to config file (default: config/env_config.yaml)
  --env ENV               Target environment (dev, staging, prod)
  --output PATH           Path to output report (default: stdout)
  --format FORMAT         Output format (text, json, html) (default: text)
  --include-resources     Include detailed resource metrics
  --threshold PATH        Path to threshold config (default: from main config)
  --verbose               Enable verbose output
  --help                  Show this help message
```

**Example**:

```bash
python environment_health_check.py --env prod --format json --output health_report.json
```

### 2. Deployment Validation Script

**Purpose**: Validates Nexora deployments to ensure they are functioning correctly by checking deployed services, API endpoints, database migrations, and configuration settings.

**Features**:

- Comprehensive deployment validation
- Kubernetes resource validation
- Service and API endpoint testing
- Database connection and migration validation
- Configuration validation
- Multiple output formats (JSON, HTML, text)
- Optional automatic rollback for failed deployments

**Usage**:

```bash
python deployment_validation.py --env [dev|staging|prod] [options]

Options:
  --env ENV               Target environment (dev, staging, prod)
  --config PATH           Path to config file (default: config/deployment_config.yaml)
  --output PATH           Path to output report (default: stdout)
  --format FORMAT         Output format (text, json, html) (default: text)
  --notify                Send notifications on validation failures
  --rollback              Automatically rollback failed deployments
  --timeout SECONDS       Timeout for validation checks (default: 300)
  --verbose               Enable verbose output
  --help                  Show this help message
```

**Example**:

```bash
python deployment_validation.py --env staging --format html --output validation_report.html
```

### 3. Compliance Report Generator

**Purpose**: Generates comprehensive compliance reports for healthcare regulatory requirements including HIPAA, GDPR, and other healthcare standards by analyzing system logs, access patterns, data handling practices, and configuration settings.

**Features**:

- Support for multiple compliance standards (HIPAA, GDPR, HITECH)
- Configurable time periods for analysis
- Multiple output formats (PDF, HTML, JSON)
- Evidence collection and anonymization
- Detailed findings and recommendations
- Visual charts and statistics

**Usage**:

```bash
python compliance_report_generator.py [options]

Options:
  --config PATH           Path to config file (default: config/compliance_config.yaml)
  --output-dir PATH       Directory to save reports (default: ./compliance_reports)
  --report-type TYPE      Type of report to generate (hipaa, gdpr, all) (default: all)
  --period PERIOD         Time period to analyze (day, week, month, quarter, year) (default: month)
  --end-date DATE         End date for analysis in YYYY-MM-DD format (default: today)
  --format FORMAT         Output format (pdf, html, json, all) (default: pdf)
  --include-evidence      Include evidence files in report
  --anonymize             Anonymize sensitive data in reports
  --verbose               Enable verbose output
  --help                  Show this help message
```

**Example**:

```bash
python compliance_report_generator.py --report-type hipaa --period month --format all
```

## Test Environment

A test environment setup script (`setup_test_env.sh`) is included to create a testing environment with sample configuration files and logs for validating the scripts. The validation script (`validate_scripts.sh`) can be used to test all three scripts in this environment.

**Usage**:

```bash
# Set up test environment
./setup_test_env.sh

# Validate scripts
./test_env/validate_scripts.sh
```

## Integration with Nexora

These scripts can be integrated into the Nexora workflow in several ways:

1. **CI/CD Pipeline**: Add the deployment validation script to the CI/CD pipeline to validate deployments automatically.
2. **Scheduled Jobs**: Set up scheduled jobs to run the environment health check and compliance report generator scripts regularly.
3. **Manual Execution**: Run the scripts manually as needed for ad-hoc checks and reports.

## Configuration

Each script uses YAML configuration files that can be customized for specific environments and requirements. Sample configuration files are provided in the test environment.

## Requirements

- Python 3.8+
- Required Python packages:
  - PyYAML
  - requests
  - psutil
  - kubernetes (for Kubernetes validation)
  - pymongo (for MongoDB validation)
  - psycopg2 (for PostgreSQL validation)
  - pandas, matplotlib (for report visualization)
  - jinja2, weasyprint (for PDF report generation)

