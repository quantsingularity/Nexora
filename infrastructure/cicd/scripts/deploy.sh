#!/bin/bash

# Infrastructure Deployment Script
# This script provides a comprehensive deployment workflow for the infrastructure
# with security checks, validation, and compliance verification

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"
LOG_FILE="/tmp/infrastructure-deploy-$(date +%Y%m%d-%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        INFO)
            echo -e "${BLUE}[INFO]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} ${message}" | tee -a "$LOG_FILE"
            ;;
    esac
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy infrastructure with comprehensive security and compliance checks.

OPTIONS:
    -e, --environment ENVIRONMENT    Target environment (dev, staging, prod)
    -a, --action ACTION             Action to perform (plan, apply, destroy)
    -r, --region REGION             AWS region (default: us-east-1)
    -v, --validate                  Run validation only
    -s, --security-scan             Run security scan only
    -c, --compliance-check          Run compliance check only
    -f, --force                     Skip confirmation prompts
    -d, --dry-run                   Perform dry run without making changes
    -h, --help                      Show this help message

EXAMPLES:
    $0 -e dev -a plan               # Plan deployment for dev environment
    $0 -e prod -a apply             # Apply changes to prod environment
    $0 -e staging -a destroy -f     # Destroy staging environment without confirmation
    $0 -v                           # Run validation checks only
    $0 -s                           # Run security scan only

EOF
}

# Parse command line arguments
parse_args() {
    ENVIRONMENT=""
    ACTION=""
    REGION="us-east-1"
    VALIDATE_ONLY=false
    SECURITY_SCAN_ONLY=false
    COMPLIANCE_CHECK_ONLY=false
    FORCE=false
    DRY_RUN=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -a|--action)
                ACTION="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -v|--validate)
                VALIDATE_ONLY=true
                shift
                ;;
            -s|--security-scan)
                SECURITY_SCAN_ONLY=true
                shift
                ;;
            -c|--compliance-check)
                COMPLIANCE_CHECK_ONLY=true
                shift
                ;;
            -f|--force)
                FORCE=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log ERROR "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done

    # Validate required parameters
    if [[ "$VALIDATE_ONLY" == false && "$SECURITY_SCAN_ONLY" == false && "$COMPLIANCE_CHECK_ONLY" == false ]]; then
        if [[ -z "$ENVIRONMENT" ]]; then
            log ERROR "Environment is required"
            usage
            exit 1
        fi

        if [[ -z "$ACTION" ]]; then
            log ERROR "Action is required"
            usage
            exit 1
        fi

        if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
            log ERROR "Environment must be one of: dev, staging, prod"
            exit 1
        fi

        if [[ ! "$ACTION" =~ ^(plan|apply|destroy)$ ]]; then
            log ERROR "Action must be one of: plan, apply, destroy"
            exit 1
        fi
    fi
}

# Check prerequisites
check_prerequisites() {
    log INFO "Checking prerequisites..."

    # Check required tools
    local required_tools=("terraform" "aws" "jq" "curl")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log ERROR "$tool is not installed or not in PATH"
            exit 1
        fi
    done

    # Check Terraform version
    local tf_version=$(terraform version -json | jq -r '.terraform_version')
    log INFO "Terraform version: $tf_version"

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log ERROR "AWS credentials not configured or invalid"
        exit 1
    fi

    local aws_identity=$(aws sts get-caller-identity)
    local account_id=$(echo "$aws_identity" | jq -r '.Account')
    local user_arn=$(echo "$aws_identity" | jq -r '.Arn')
    log INFO "AWS Account: $account_id"
    log INFO "AWS User/Role: $user_arn"

    # Check if we're in the right directory
    if [[ ! -f "$TERRAFORM_DIR/main.tf" ]]; then
        log ERROR "Terraform configuration not found in $TERRAFORM_DIR"
        exit 1
    fi

    log SUCCESS "Prerequisites check completed"
}

# Run security scan
run_security_scan() {
    log INFO "Running security scan..."

    # Check if security tools are available
    local security_tools=("checkov" "tfsec" "trivy")
    local available_tools=()

    for tool in "${security_tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            available_tools+=("$tool")
        else
            log WARN "$tool not found, skipping"
        fi
    done

    if [[ ${#available_tools[@]} -eq 0 ]]; then
        log WARN "No security scanning tools found. Installing checkov..."
        pip3 install checkov || {
            log ERROR "Failed to install checkov"
            return 1
        }
        available_tools+=("checkov")
    fi

    # Run available security tools
    local scan_failed=false

    for tool in "${available_tools[@]}"; do
        log INFO "Running $tool security scan..."
        case $tool in
            checkov)
                if ! checkov -d "$TERRAFORM_DIR" --framework terraform --output cli; then
                    log ERROR "Checkov scan failed"
                    scan_failed=true
                fi
                ;;
            tfsec)
                if ! tfsec "$TERRAFORM_DIR"; then
                    log ERROR "tfsec scan failed"
                    scan_failed=true
                fi
                ;;
            trivy)
                if ! trivy fs --security-checks config "$TERRAFORM_DIR"; then
                    log ERROR "Trivy scan failed"
                    scan_failed=true
                fi
                ;;
        esac
    done

    if [[ "$scan_failed" == true ]]; then
        log ERROR "Security scan failed"
        return 1
    fi

    log SUCCESS "Security scan completed successfully"
}

# Validate Terraform configuration
validate_terraform() {
    log INFO "Validating Terraform configuration..."

    cd "$TERRAFORM_DIR"

    # Format check
    log INFO "Checking Terraform formatting..."
    if ! terraform fmt -check -recursive; then
        log ERROR "Terraform files are not properly formatted"
        log INFO "Run 'terraform fmt -recursive' to fix formatting"
        return 1
    fi

    # Initialize Terraform
    log INFO "Initializing Terraform..."
    if [[ -n "$ENVIRONMENT" ]]; then
        terraform init \
            -code-config="key=${ENVIRONMENT}/terraform.tfstate" \
            -reconfigure
    else
        terraform init -reconfigure
    fi

    # Validate configuration
    log INFO "Validating Terraform configuration..."
    if ! terraform validate; then
        log ERROR "Terraform validation failed"
        return 1
    fi

    log SUCCESS "Terraform validation completed successfully"
}

# Run Terraform plan
run_terraform_plan() {
    log INFO "Running Terraform plan for environment: $ENVIRONMENT"

    cd "$TERRAFORM_DIR"

    local plan_file="${ENVIRONMENT}.tfplan"
    local var_file="environments/${ENVIRONMENT}.tfvars"

    if [[ ! -f "$var_file" ]]; then
        log ERROR "Variable file not found: $var_file"
        return 1
    fi

    # Run terraform plan
    log INFO "Generating Terraform plan..."
    if terraform plan \
        -var-file="$var_file" \
        -out="$plan_file" \
        -detailed-exitcode; then
        log SUCCESS "Terraform plan completed successfully"
        log INFO "Plan saved to: $plan_file"
    else
        local exit_code=$?
        if [[ $exit_code -eq 2 ]]; then
            log INFO "Terraform plan completed with changes"
        else
            log ERROR "Terraform plan failed"
            return 1
        fi
    fi

    # Show plan summary
    log INFO "Plan summary:"
    terraform show -no-color "$plan_file" | grep -E "^(Plan:|No changes)"
}

# Apply Terraform changes
apply_terraform() {
    log INFO "Applying Terraform changes for environment: $ENVIRONMENT"

    cd "$TERRAFORM_DIR"

    local plan_file="${ENVIRONMENT}.tfplan"

    if [[ ! -f "$plan_file" ]]; then
        log ERROR "Plan file not found: $plan_file"
        log INFO "Run plan first before applying"
        return 1
    fi

    # Confirmation for production
    if [[ "$ENVIRONMENT" == "prod" && "$FORCE" == false ]]; then
        echo -n "Are you sure you want to apply changes to PRODUCTION? (yes/no): "
        read -r confirmation
        if [[ "$confirmation" != "yes" ]]; then
            log INFO "Deployment cancelled by user"
            return 1
        fi
    fi

    # Apply changes
    if [[ "$DRY_RUN" == true ]]; then
        log INFO "DRY RUN: Would apply Terraform plan"
        terraform show "$plan_file"
    else
        log INFO "Applying Terraform plan..."
        if terraform apply -auto-approve "$plan_file"; then
            log SUCCESS "Terraform apply completed successfully"
        else
            log ERROR "Terraform apply failed"
            return 1
        fi
    fi
}

# Destroy infrastructure
destroy_terraform() {
    log INFO "Destroying infrastructure for environment: $ENVIRONMENT"

    cd "$TERRAFORM_DIR"

    local var_file="environments/${ENVIRONMENT}.tfvars"

    if [[ ! -f "$var_file" ]]; then
        log ERROR "Variable file not found: $var_file"
        return 1
    fi

    # Confirmation
    if [[ "$FORCE" == false ]]; then
        echo -n "Are you sure you want to DESTROY infrastructure for $ENVIRONMENT? (yes/no): "
        read -r confirmation
        if [[ "$confirmation" != "yes" ]]; then
            log INFO "Destroy cancelled by user"
            return 1
        fi
    fi

    # Destroy infrastructure
    if [[ "$DRY_RUN" == true ]]; then
        log INFO "DRY RUN: Would destroy infrastructure"
        terraform plan -destroy -var-file="$var_file"
    else
        log INFO "Destroying infrastructure..."
        if terraform destroy -var-file="$var_file" -auto-approve; then
            log SUCCESS "Infrastructure destroyed successfully"
        else
            log ERROR "Infrastructure destroy failed"
            return 1
        fi
    fi
}

# Run compliance check
run_compliance_check() {
    log INFO "Running compliance check..."

    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &> /dev/null; then
        log ERROR "AWS credentials not configured"
        return 1
    fi

    # AWS Config compliance check
    log INFO "Checking AWS Config compliance..."
    if aws configservice get-compliance-summary-by-config-rule --region "$REGION" &> /dev/null; then
        aws configservice get-compliance-summary-by-config-rule --region "$REGION" --output table
    else
        log WARN "AWS Config not available or not configured"
    fi

    # Security Hub findings
    log INFO "Checking Security Hub findings..."
    if aws securityhub get-findings \
        --region "$REGION" \
        --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}]}' \
        --max-items 10 \
        --output table &> /dev/null; then
        aws securityhub get-findings \
            --region "$REGION" \
            --filters '{"ComplianceStatus":[{"Value":"FAILED","Comparison":"EQUALS"}]}' \
            --max-items 10 \
            --output table
    else
        log WARN "Security Hub not available or not configured"
    fi

    log SUCCESS "Compliance check completed"
}

# Generate deployment report
generate_report() {
    log INFO "Generating deployment report..."

    local report_file="/tmp/deployment-report-${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S).md"

    cat > "$report_file" << EOF
# Infrastructure Deployment Report

**Environment:** $ENVIRONMENT
**Action:** $ACTION
**Date:** $(date)
**User:** $(whoami)
**AWS Account:** $(aws sts get-caller-identity --query Account --output text)

## Deployment Summary

EOF

    if [[ -f "$TERRAFORM_DIR/${ENVIRONMENT}.tfplan" ]]; then
        echo "## Terraform Plan Summary" >> "$report_file"
        echo '```' >> "$report_file"
        terraform -chdir="$TERRAFORM_DIR" show -no-color "${ENVIRONMENT}.tfplan" | head -50 >> "$report_file"
        echo '```' >> "$report_file"
        echo "" >> "$report_file"
    fi

    if [[ "$ACTION" == "apply" ]]; then
        echo "## Infrastructure Outputs" >> "$report_file"
        echo '```json' >> "$report_file"
        terraform -chdir="$TERRAFORM_DIR" output -json >> "$report_file" 2>/dev/null || echo "No outputs available" >> "$report_file"
        echo '```' >> "$report_file"
        echo "" >> "$report_file"
    fi

    echo "## Log File" >> "$report_file"
    echo "Full deployment log: $LOG_FILE" >> "$report_file"

    log SUCCESS "Deployment report generated: $report_file"
}

# Cleanup function
cleanup() {
    log INFO "Cleaning up temporary files..."
    # Add cleanup logic here if needed
}

# Main function
main() {
    log INFO "Starting infrastructure deployment script"
    log INFO "Log file: $LOG_FILE"

    # Set trap for cleanup
    trap cleanup EXIT

    # Parse arguments
    parse_args "$@"

    # Check prerequisites
    check_prerequisites

    # Handle specific actions
    if [[ "$SECURITY_SCAN_ONLY" == true ]]; then
        run_security_scan
        exit $?
    fi

    if [[ "$VALIDATE_ONLY" == true ]]; then
        validate_terraform
        exit $?
    fi

    if [[ "$COMPLIANCE_CHECK_ONLY" == true ]]; then
        run_compliance_check
        exit $?
    fi

    # Full deployment workflow
    log INFO "Starting deployment workflow for environment: $ENVIRONMENT"

    # Run security scan
    if ! run_security_scan; then
        log ERROR "Security scan failed, aborting deployment"
        exit 1
    fi

    # Validate Terraform
    if ! validate_terraform; then
        log ERROR "Terraform validation failed, aborting deployment"
        exit 1
    fi

    # Execute action
    case $ACTION in
        plan)
            run_terraform_plan
            ;;
        apply)
            run_terraform_plan
            apply_terraform
            run_compliance_check
            ;;
        destroy)
            destroy_terraform
            ;;
    esac

    # Generate report
    generate_report

    log SUCCESS "Deployment workflow completed successfully"
}

# Run main function with all arguments
main "$@"
