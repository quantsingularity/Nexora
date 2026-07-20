#!/bin/bash
set -e

# SCRIPTS_DIR is where this script (and environment_health_check.py,
# deployment_validation.py, compliance_report_generator.py) actually live -
# computed dynamically so this works from any checkout location.
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Must match the default used by setup_test_env.sh; override both with the
# same NEXORA_TEST_ENV_DIR value if you customized it there.
TEST_ENV_DIR="${NEXORA_TEST_ENV_DIR:-/tmp/nexora_test_env}"

if [ ! -d "$TEST_ENV_DIR/config" ]; then
  echo "[FAIL] Test environment not found at $TEST_ENV_DIR"
  echo "  Run setup_test_env.sh first (optionally with NEXORA_TEST_ENV_DIR set)."
  exit 1
fi

echo "===== Validating Nexora Automation Scripts ====="
echo

# Set up environment variables for testing
export NEXORA_ENV=dev
export NEXORA_CONFIG_DIR="$TEST_ENV_DIR/config"
export NEXORA_LOGS_DIR="$TEST_ENV_DIR/logs"
export NEXORA_OUTPUT_DIR="$TEST_ENV_DIR/output"

echo "1. Testing Environment Health Check Script"
# `|| true`: a FAIL/ERROR health status is a legitimate, informative result
# (e.g. no real services running in this test env), not a script failure -
# only the presence of the report file below determines success here.
python3 "$SCRIPTS_DIR/environment_health_check.py" \
  --config "$TEST_ENV_DIR/config/env_config.yaml" \
  --env dev \
  --output "$TEST_ENV_DIR/output/env_health_report.json" \
  --format json || true

if [ -f "$TEST_ENV_DIR/output/env_health_report.json" ]; then
  echo "[OK] Environment Health Check Script executed successfully"
  echo "  Report generated at: $TEST_ENV_DIR/output/env_health_report.json"
else
  echo "[FAIL] Environment Health Check Script failed"
  exit 1
fi

echo

echo "2. Testing Deployment Validation Script"
python3 "$SCRIPTS_DIR/deployment_validation.py" \
  --env dev \
  --config "$TEST_ENV_DIR/config/deployment_config.yaml" \
  --output "$TEST_ENV_DIR/output/deployment_validation_report.json" \
  --format json || true

if [ -f "$TEST_ENV_DIR/output/deployment_validation_report.json" ]; then
  echo "[OK] Deployment Validation Script executed successfully"
  echo "  Report generated at: $TEST_ENV_DIR/output/deployment_validation_report.json"
else
  echo "[FAIL] Deployment Validation Script failed"
  exit 1
fi

echo

echo "3. Testing Compliance Report Generator Script"
python3 "$SCRIPTS_DIR/compliance_report_generator.py" \
  --config "$TEST_ENV_DIR/config/compliance_config.yaml" \
  --output-dir "$TEST_ENV_DIR/output" \
  --report-type all \
  --period month \
  --format json || true

if ls "$TEST_ENV_DIR"/output/compliance_report_*.json 1> /dev/null 2>&1; then
  echo "[OK] Compliance Report Generator Script executed successfully"
  echo "  Report generated at: $(ls "$TEST_ENV_DIR"/output/compliance_report_*.json)"
else
  echo "[FAIL] Compliance Report Generator Script failed"
  exit 1
fi

echo
echo "===== All scripts validated successfully! ====="
