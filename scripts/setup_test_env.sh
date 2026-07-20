#!/bin/bash
# Script to create a test environment for validating the automation scripts
set -e

# SCRIPT_DIR is where this script (and environment_health_check.py,
# deployment_validation.py, compliance_report_generator.py) actually live.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default to a location under /tmp so this doesn't require root privileges
# to create (unlike a hardcoded /test_env at the filesystem root); override
# with NEXORA_TEST_ENV_DIR if you want it elsewhere.
TEST_ENV_DIR="${NEXORA_TEST_ENV_DIR:-/tmp/nexora_test_env}"

echo "Using script directory: $SCRIPT_DIR"
echo "Using test environment directory: $TEST_ENV_DIR"

# Create necessary directories
mkdir -p "$TEST_ENV_DIR/config"
mkdir -p "$TEST_ENV_DIR/logs"
mkdir -p "$TEST_ENV_DIR/output"

# Create sample configuration files for testing
cat > "$TEST_ENV_DIR/config/deployment_config.yaml" << 'EOF'
environments:
  dev:
    deployment:
      name: nexora-dev
      version: 1.0.0
      namespace: nexora
      rollback_enabled: true
      rollback_command: "echo 'Rolling back deployment'"
    kubernetes:
      enabled: true
      in_cluster: false
      namespace: nexora
      # Matches infrastructure/kubernetes/base/{backend,frontend}-{deployment,service}.yaml
      # ("{{ .Values.appName }}-backend" / "-frontend"; no separate database
      # resource, since the app persists to SQLite, not a client-server DB).
      expected_deployments:
        - nexora-backend
        - nexora-frontend
      expected_services:
        - nexora-backend
        - nexora-frontend
    services:
      - name: nexora-backend
        type: http
        url: http://localhost:8080/api/health
        method: GET
        expected_status: 200
        timeout: 5
        content_check: "healthy"
    api_endpoints:
      # /health is public; most other routes (e.g. /patients) require a
      # Bearer token (see code/backend/app/core/security.py), so they're
      # not suitable for an unauthenticated sample check like this one.
      - name: health-check
        url: http://localhost:8080/api/health
        method: GET
        expected_status: 200
        timeout: 5
        schema_validation:
          required_fields:
            - status
            - timestamp
            - version
          field_types:
            status: string
            timestamp: string
            version: string
    config_validations:
      - name: api-config
        type: file
        file_path: __TEST_ENV_DIR__/config/api-config.yaml
        required_settings:
          - path: api.timeout
            value: 30
          - path: api.max_connections
            value: 100
      - name: env-vars
        type: env
        required_vars:
          - name: NEXORA_ENV
            value: dev
EOF

cat > "$TEST_ENV_DIR/config/compliance_config.yaml" << 'EOF'
organization:
  name: Nexora Healthcare
  domain: nexora.health
  contact_email: compliance@nexora.health

compliance:
  hipaa:
    enabled: true
    requirements:
      - id: hipaa-164-308
        title: Administrative Safeguards
        description: Implement policies and procedures to prevent, detect, contain, and correct security violations.
        controls:
          - id: hipaa-164-308-a-1
            title: Security Management Process
            description: Implement policies and procedures to prevent, detect, contain, and correct security violations.
            check_type: config
            check_paths: ["__TEST_ENV_DIR__/config/security.yaml"]
            check_pattern: "security_management_process:\\s*enabled:\\s*true"
  gdpr:
    enabled: true
    requirements:
      - id: gdpr-article-5
        title: Principles relating to processing of personal data
        description: Personal data shall be processed lawfully, fairly and in a transparent manner.
        controls:
          - id: gdpr-article-5-1-a
            title: Lawfulness, fairness and transparency
            description: Personal data must be processed lawfully, fairly, and in a transparent manner.
            check_type: config
            check_paths: ["__TEST_ENV_DIR__/config/privacy.yaml"]
            check_pattern: "data_processing_principles:\\s*lawfulness:\\s*true"

analysis:
  log_patterns:
    authentication: "authentication|login|logout|access"
    authorization: "authorization|permission|access denied"
    data_access: "data access|record access|patient data"
    data_modification: "data modified|record updated|changed"
    security_event: "security|breach|attack|intrusion|malware"
    system_event: "system|startup|shutdown|restart|update"
  thresholds:
    failed_login_attempts: 5
    unauthorized_access_attempts: 3
    suspicious_activity_threshold: 10

reporting:
  report_title_format: "{report_type} Compliance Report - {period_end}"
  include_executive_summary: true
  include_technical_details: true
  include_remediation_plan: true
  include_evidence: false
  evidence_directory: "__TEST_ENV_DIR__/evidence"
EOF

cat > "$TEST_ENV_DIR/config/env_config.yaml" << 'EOF'
environments:
  dev:
    api:
      url: http://localhost:8080
      timeout: 30
      max_retries: 3
    database:
      host: localhost
      port: 5432
      name: nexora_dev
      user: nexora
      password: nexora123
    storage:
      type: local
      path: /data/nexora/dev
    logging:
      level: debug
      path: /var/log/nexora/dev
    features:
      feature_a: true
      feature_b: false
  staging:
    api:
      url: https://staging-api.nexora.health
      timeout: 30
      max_retries: 3
    database:
      host: staging-db.nexora.internal
      port: 5432
      name: nexora_staging
      user: nexora
      password: nexora456
    storage:
      type: s3
      bucket: nexora-staging
    logging:
      level: info
      path: /var/log/nexora/staging
    features:
      feature_a: true
      feature_b: true
  prod:
    api:
      url: https://api.nexora.health
      timeout: 60
      max_retries: 5
    database:
      host: prod-db.nexora.internal
      port: 5432
      name: nexora_prod
      user: nexora
      password: nexora789
    storage:
      type: s3
      bucket: nexora-prod
    logging:
      level: warn
      path: /var/log/nexora/prod
    features:
      feature_a: true
      feature_b: true
EOF

# Create sample configuration files for compliance checks
cat > "$TEST_ENV_DIR/config/security.yaml" << 'EOF'
security_management_process:
  enabled: true
  last_updated: 2025-01-15
  reviewed_by: Security Officer

security_officer:
  name: John Smith
  email: security@nexora.health
  phone: 555-123-4567

workforce_security:
  enabled: true
  access_control:
    role_based: true
    least_privilege: true
  termination_procedures:
    enabled: true
    system_access_removal: true

data_security:
  integrity: true
  encryption: true
  at_rest: true
  in_transit: true
EOF

cat > "$TEST_ENV_DIR/config/privacy.yaml" << 'EOF'
data_processing_principles:
  lawfulness: true
  fairness: true
  transparency: true
  purpose_limitation: true
  data_minimization: true
  accuracy: true
  storage_limitation: true

privacy_by_design:
  enabled: true
  impact_assessments: true
  documentation: true

privacy_by_default:
  enabled: true
  minimal_collection: true
  limited_retention: true
EOF

cat > "$TEST_ENV_DIR/config/api-config.yaml" << 'EOF'
api:
  timeout: 30
  max_connections: 100
  rate_limit: 1000
  version: 1.0.0

endpoints:
  - path: /patients
    methods: [GET, POST, PUT]
    auth_required: true
  - path: /appointments
    methods: [GET, POST, DELETE]
    auth_required: true
  - path: /health
    methods: [GET]
    auth_required: false

security:
  cors:
    enabled: true
    allowed_origins: ["https://nexora.health"]
  rate_limiting:
    enabled: true
    limit: 100
    period: 60
EOF

# Create sample log files
cat > "$TEST_ENV_DIR/logs/access.log" << 'EOF'
2025-05-20 08:12:34 INFO [Authentication] User john.doe successfully logged in from 192.168.1.100
2025-05-20 08:15:22 INFO [Authorization] User john.doe accessed patient record #12345
2025-05-20 09:30:45 INFO [Data Access] User jane.smith accessed patient data for ID #54321
2025-05-20 10:45:12 WARNING [Authorization] User guest attempted to access restricted area
2025-05-20 11:22:33 INFO [Authentication] User admin logged in from 10.0.0.5
2025-05-20 12:01:15 INFO [Data Modification] User admin updated system configuration
2025-05-20 13:45:22 ERROR [Authentication] Failed login attempt for user unknown from 203.0.113.42
2025-05-20 14:30:11 INFO [System] Database backup completed successfully
2025-05-20 15:20:45 INFO [Authentication] User john.doe logged out
2025-05-21 08:05:12 INFO [Authentication] User jane.smith logged in from 192.168.1.105
2025-05-21 09:12:34 INFO [Data Access] User jane.smith accessed patient records #12345, #12346, #12347
2025-05-21 10:30:45 WARNING [Security] Multiple failed login attempts detected from 203.0.113.100
2025-05-21 11:45:22 INFO [System] System update initiated by admin
2025-05-21 12:22:33 INFO [Data Modification] User jane.smith updated patient record #12345
2025-05-21 13:01:15 INFO [Authentication] User admin logged in from 10.0.0.5
2025-05-21 14:45:22 INFO [Authorization] User admin accessed audit logs
2025-05-21 15:30:11 INFO [System] Daily integrity check completed successfully
2025-05-21 16:20:45 INFO [Authentication] User jane.smith logged out
2025-05-22 08:10:12 INFO [Authentication] User john.doe logged in from 192.168.1.100
EOF

cat > "$TEST_ENV_DIR/logs/audit.log" << 'EOF'
2025-05-20 08:15:30 AUDIT [Access] User john.doe accessed PHI for patient #12345
2025-05-20 09:31:00 AUDIT [Access] User jane.smith accessed PHI for patient #54321
2025-05-20 10:45:30 AUDIT [Access Denied] User guest attempted to access PHI without authorization
2025-05-20 11:23:00 AUDIT [Admin] User admin accessed system configuration
2025-05-20 12:01:30 AUDIT [Modification] User admin modified security settings
2025-05-20 14:30:30 AUDIT [System] Automated database backup executed
2025-05-21 09:13:00 AUDIT [Bulk Access] User jane.smith accessed PHI for multiple patients
2025-05-21 11:45:30 AUDIT [System] System update applied
2025-05-21 12:23:00 AUDIT [Modification] User jane.smith modified patient #12345 medical record
2025-05-21 14:45:30 AUDIT [Admin] User admin accessed audit log system
2025-05-21 15:30:30 AUDIT [System] Integrity verification completed
2025-05-22 08:10:30 AUDIT [Access] User john.doe accessed PHI for patient #12345
EOF

# Resolve the __TEST_ENV_DIR__ placeholder left in deployment_config.yaml /
# compliance_config.yaml (written above via quoted heredocs, so $TEST_ENV_DIR
# couldn't be substituted at write time without also corrupting the \s*
# regex-escape sequences those files contain).
sed -i "s|__TEST_ENV_DIR__|$TEST_ENV_DIR|g" \
  "$TEST_ENV_DIR/config/deployment_config.yaml" \
  "$TEST_ENV_DIR/config/compliance_config.yaml"

# Create a test script to validate all three automation scripts.
# Written in two parts: first an unquoted heredoc so $SCRIPT_DIR (the real
# location of the .py scripts, computed above) gets baked in as a literal
# path; then a quoted heredoc appended to it so the rest of the script's
# $TEST_ENV_DIR/$SCRIPTS_DIR references and $(...) commands stay literal
# and are only evaluated when the generated script itself runs.
cat > "$TEST_ENV_DIR/validate_scripts.sh" << EOF_HEADER
#!/bin/bash
set -e

# Location of the real Nexora automation scripts (baked in by setup_test_env.sh).
SCRIPTS_DIR="$SCRIPT_DIR"
# This script lives inside the test environment directory itself, so we can
# always find it relative to our own location - no hardcoded path needed.
TEST_ENV_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
EOF_HEADER

cat >> "$TEST_ENV_DIR/validate_scripts.sh" << 'EOF'

echo "===== Validating Nexora Automation Scripts ====="
echo

# Set up environment variables for testing
export NEXORA_ENV=dev
export NEXORA_CONFIG_DIR="$TEST_ENV_DIR/config"
export NEXORA_LOGS_DIR="$TEST_ENV_DIR/logs"
export NEXORA_OUTPUT_DIR="$TEST_ENV_DIR/output"

echo "1. Testing Environment Health Check Script"
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
EOF

# Make the validation script executable
chmod +x "$TEST_ENV_DIR/validate_scripts.sh"

echo "Test environment setup completed successfully."
