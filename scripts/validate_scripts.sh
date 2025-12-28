#!/bin/bash
set -e

echo "===== Validating Nexora Automation Scripts ====="
echo

# Set up environment variables for testing
export NEXORA_ENV=dev
export NEXORA_CONFIG_DIR=/test_env/config
export NEXORA_LOGS_DIR=/test_env/logs
export NEXORA_OUTPUT_DIR=/test_env/output

echo "1. Testing Environment Health Check Script"
python3 /scripts/environment_health_check.py \
  --config /test_env/config/env_config.yaml \
  --env dev \
  --output /test_env/output/env_health_report.json \
  --format json

if [ -f "/test_env/output/env_health_report.json" ]; then
  echo "✓ Environment Health Check Script executed successfully"
  echo "  Report generated at: /test_env/output/env_health_report.json"
else
  echo "✗ Environment Health Check Script failed"
  exit 1
fi

echo

echo "2. Testing Deployment Validation Script"
python3 /scripts/deployment_validation.py \
  --env dev \
  --config /test_env/config/deployment_config.yaml \
  --output /test_env/output/deployment_validation_report.json \
  --format json

if [ -f "/test_env/output/deployment_validation_report.json" ]; then
  echo "✓ Deployment Validation Script executed successfully"
  echo "  Report generated at: /test_env/output/deployment_validation_report.json"
else
  echo "✗ Deployment Validation Script failed"
  exit 1
fi

echo

echo "3. Testing Compliance Report Generator Script"
python3 /scripts/compliance_report_generator.py \
  --config /test_env/config/compliance_config.yaml \
  --output-dir /test_env/output \
  --report-type all \
  --period month \
  --format json

if ls /test_env/output/compliance_report_*.json 1> /dev/null 2>&1; then
  echo "✓ Compliance Report Generator Script executed successfully"
  echo "  Report generated at: $(ls /test_env/output/compliance_report_*.json)"
else
  echo "✗ Compliance Report Generator Script failed"
  exit 1
fi

echo
echo "===== All scripts validated successfully! ====="
