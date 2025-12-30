# Configuration Guide

Complete reference for configuring Nexora platform, including all configuration files, environment variables, and customization options.

## Table of Contents

- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Model Configuration](#model-configuration)
- [Data Pipeline Configuration](#data-pipeline-configuration)
- [Security & Compliance Configuration](#security--compliance-configuration)
- [Deployment Configuration](#deployment-configuration)

---

## Configuration Files

### Configuration File Locations

| File                        | Path                            | Purpose                        |
| --------------------------- | ------------------------------- | ------------------------------ |
| **Clinical Config**         | `config/clinical_config.yaml`   | Main application configuration |
| **De-identification Rules** | `config/deid_rules.yaml`        | PHI protection rules           |
| **Model Parameters**        | `config/model_configs/*.yaml`   | Model-specific settings        |
| **Feature Configs**         | `config/feature_configs/*.json` | Feature engineering rules      |
| **Environment**             | `.env`                          | Environment variables          |

---

## Environment Variables

### API Configuration

| Variable      | Type    | Default   | Description                              | Where to Set |
| ------------- | ------- | --------- | ---------------------------------------- | ------------ |
| `HOST`        | string  | `0.0.0.0` | API server host                          | env/file     |
| `PORT`        | integer | `8000`    | API server port                          | env/file     |
| `LOG_LEVEL`   | string  | `INFO`    | Logging level (DEBUG/INFO/WARNING/ERROR) | env/file     |
| `ENABLE_DOCS` | boolean | `true`    | Enable API documentation endpoints       | env/file     |

**Example `.env` file**:

```bash
# API Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
ENABLE_DOCS=true
```

---

### FHIR Integration

| Variable          | Type    | Default                    | Description                             | Where to Set |
| ----------------- | ------- | -------------------------- | --------------------------------------- | ------------ |
| `FHIR_SERVER_URL` | url     | `http://localhost:8080/R4` | FHIR server base URL                    | env/file     |
| `FHIR_AUTH_TYPE`  | string  | `none`                     | Authentication type (none/basic/oauth2) | env/file     |
| `FHIR_USERNAME`   | string  | None                       | FHIR server username (if basic auth)    | env          |
| `FHIR_PASSWORD`   | string  | None                       | FHIR server password (if basic auth)    | env          |
| `FHIR_TOKEN`      | string  | None                       | OAuth2 bearer token (if oauth2)         | env          |
| `FHIR_PAGE_SIZE`  | integer | `1000`                     | Results per page for FHIR queries       | env/file     |

**Example**:

```bash
# FHIR Configuration
FHIR_SERVER_URL=https://fhir-server.hospital.org/R4
FHIR_AUTH_TYPE=oauth2
FHIR_TOKEN=your-oauth2-token-here
FHIR_PAGE_SIZE=500
```

---

### Database Configuration

| Variable          | Type    | Default               | Description                   | Where to Set |
| ----------------- | ------- | --------------------- | ----------------------------- | ------------ |
| `DATABASE_URL`    | url     | None                  | Database connection string    | env          |
| `AUDIT_DB_PATH`   | path    | `audit/phi_access.db` | Audit log database path       | env/file     |
| `DB_POOL_SIZE`    | integer | `10`                  | Database connection pool size | env/file     |
| `DB_MAX_OVERFLOW` | integer | `20`                  | Maximum overflow connections  | env/file     |

**Example**:

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/nexora
AUDIT_DB_PATH=./audit/phi_access.db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

---

### Model Configuration

| Variable              | Type    | Default             | Description                        | Where to Set |
| --------------------- | ------- | ------------------- | ---------------------------------- | ------------ |
| `MODEL_REGISTRY_PATH` | path    | `./models/registry` | Model storage directory            | env/file     |
| `DEFAULT_MODEL`       | string  | `readmission_v1`    | Default model name                 | env/file     |
| `MODEL_CACHE_SIZE`    | integer | `5`                 | Number of models to keep in memory | env/file     |
| `ENABLE_GPU`          | boolean | `false`             | Enable GPU acceleration            | env/file     |
| `GPU_DEVICE`          | string  | `cuda:0`            | GPU device identifier              | env/file     |

**Example**:

```bash
# Model Configuration
MODEL_REGISTRY_PATH=/mnt/models/registry
DEFAULT_MODEL=readmission_transformer
MODEL_CACHE_SIZE=3
ENABLE_GPU=true
GPU_DEVICE=cuda:0
```

---

### Security Configuration

| Variable                | Type    | Default | Description                            | Where to Set   |
| ----------------------- | ------- | ------- | -------------------------------------- | -------------- |
| `SECRET_KEY`            | string  | None    | Application secret key for JWT         | env (required) |
| `JWT_ALGORITHM`         | string  | `HS256` | JWT signing algorithm                  | env/file       |
| `JWT_EXPIRATION_HOURS`  | integer | `24`    | JWT token expiration time              | env/file       |
| `ENABLE_RATE_LIMITING`  | boolean | `true`  | Enable API rate limiting               | env/file       |
| `RATE_LIMIT_PER_MINUTE` | integer | `60`    | Max requests per minute                | env/file       |
| `CORS_ORIGINS`          | string  | `*`     | Allowed CORS origins (comma-separated) | env/file       |

**Example**:

```bash
# Security Configuration
SECRET_KEY=your-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ENABLE_RATE_LIMITING=true
RATE_LIMIT_PER_MINUTE=300
CORS_ORIGINS=https://app.hospital.org,https://admin.hospital.org
```

---

### Monitoring Configuration

| Variable            | Type    | Default     | Description                | Where to Set |
| ------------------- | ------- | ----------- | -------------------------- | ------------ |
| `ENABLE_METRICS`    | boolean | `true`      | Enable Prometheus metrics  | env/file     |
| `METRICS_PORT`      | integer | `9090`      | Metrics endpoint port      | env/file     |
| `ENABLE_TRACING`    | boolean | `false`     | Enable distributed tracing | env/file     |
| `JAEGER_AGENT_HOST` | string  | `localhost` | Jaeger agent host          | env/file     |
| `JAEGER_AGENT_PORT` | integer | `6831`      | Jaeger agent port          | env/file     |

**Example**:

```bash
# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
ENABLE_TRACING=true
JAEGER_AGENT_HOST=jaeger-agent.monitoring
JAEGER_AGENT_PORT=6831
```

---

### Compliance Configuration

| Variable                   | Type    | Default | Description                               | Where to Set |
| -------------------------- | ------- | ------- | ----------------------------------------- | ------------ |
| `ENABLE_AUDIT_LOGGING`     | boolean | `true`  | Enable PHI access audit logging           | env/file     |
| `PHI_DETECTION_ENABLED`    | boolean | `true`  | Enable automatic PHI detection            | env/file     |
| `AUDIT_LOG_RETENTION_DAYS` | integer | `365`   | Audit log retention period                | env/file     |
| `ENABLE_DE_IDENTIFICATION` | boolean | `true`  | Enable automatic de-identification        | env/file     |
| `DATE_SHIFT_RANGE_DAYS`    | integer | `365`   | Date shifting range for de-identification | env/file     |

**Example**:

```bash
# Compliance Configuration
ENABLE_AUDIT_LOGGING=true
PHI_DETECTION_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=730
ENABLE_DE_IDENTIFICATION=true
DATE_SHIFT_RANGE_DAYS=365
```

---

## Model Configuration

### Model Parameters File

**Location**: `config/model_configs/deepfm_params.yaml`

```yaml
# DeepFM Model Configuration

model:
  name: readmission_deepfm_v1
  type: DeepFM
  version: 1.0.0

architecture:
  embedding_dim: 128
  hidden_layers: [256, 128, 64]
  dropout: 0.3
  activation: relu
  use_batch_norm: true

training:
  learning_rate: 0.001
  batch_size: 256
  epochs: 50
  optimizer: adam
  loss_function: binary_crossentropy
  early_stopping:
    enabled: true
    patience: 5
    min_delta: 0.001

validation:
  split: 0.2
  stratified: true
  random_seed: 42

performance_thresholds:
  min_auroc: 0.75
  min_auprc: 0.70
  max_false_positive_rate: 0.20

fairness_constraints:
  max_equal_opportunity_diff: 0.10
  min_demographic_parity_ratio: 0.80
  protected_attributes:
    - race
    - gender
    - age_group

calibration:
  method: isotonic
  bins: 10
  target_slope: 1.0
```

### XGBoost Parameters

**Location**: `config/model_configs/xgb_hyperparameters.json`

```json
{
  "model": {
    "name": "readmission_xgb_v1",
    "type": "XGBoost",
    "version": "1.0.0"
  },
  "hyperparameters": {
    "max_depth": 6,
    "learning_rate": 0.1,
    "n_estimators": 100,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "min_child_weight": 1,
    "gamma": 0,
    "reg_alpha": 0,
    "reg_lambda": 1,
    "objective": "binary:logistic",
    "eval_metric": "auc"
  },
  "training": {
    "early_stopping_rounds": 10,
    "verbose": false
  }
}
```

---

## Data Pipeline Configuration

### Clinical Configuration

**Location**: `config/clinical_config.yaml`

```yaml
# Nexora Clinical Configuration

data:
  # FHIR Data Source
  fhir:
    base_url: https://fhir.healthsystem.org/R4
    page_count: 1000
    timeout_seconds: 30
    retry_attempts: 3

  # De-identification Settings
  deidentification:
    enabled: true
    date_shift_days: 365
    preserve_day_of_week: true
    phi_patterns:
      - name: mrn
        regex: '\b\d{3}-\d{2}-\d{4}\b'
        replacement: "[MEDICAL_RECORD]"
      - name: ssn
        regex: '\b\d{3}-\d{2}-\d{4}\b'
        replacement: "[SSN]"
      - name: phone
        regex: '\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        replacement: "[PHONE]"
      - name: email
        regex: '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        replacement: "[EMAIL]"

  # Data Quality
  quality_checks:
    - check_missing_values
    - check_data_types
    - check_value_ranges
    - check_temporal_consistency

  min_data_completeness: 0.80

# Model Configuration
model:
  # Default Model
  default_model: readmission_v1
  model_version: 1.0.0

  # Risk Thresholds
  clinical_thresholds:
    high_risk: 0.75
    medium_risk: 0.40
    low_risk: 0.10

  # Fairness Constraints
  fairness_constraints:
    max_disparity: 0.1
    protected_attributes:
      - race
      - gender
      - age_group

  # Model Calibration
  calibration:
    method: isotonic
    bins: 10
    recalibrate_interval_days: 30

  # Feature Configuration
  features:
    demographics:
      - age
      - gender
      - race
      - ethnicity

    clinical_events:
      - diagnosis_codes
      - procedure_codes
      - encounter_types

    lab_results:
      - hemoglobin_a1c
      - creatinine
      - egfr
      - bnp

    medications:
      - medication_classes
      - polypharmacy_count

    temporal_features:
      - days_since_admission
      - previous_admissions_count
      - length_of_stay

# Clinical Integration
clinical:
  # Alert Thresholds
  alerts:
    high_risk_threshold: 0.75
    alert_recipients:
      - discharge_planning_team
      - case_management

  # Intervention Recommendations
  interventions:
    high_risk:
      - post_discharge_follow_up_7_days
      - home_health_services
      - medication_reconciliation
      - care_transition_coach
    medium_risk:
      - post_discharge_follow_up_14_days
      - medication_review
    low_risk:
      - standard_discharge_instructions

  # EHR Integration
  ehr:
    integration_type: hl7_v2
    message_types:
      - ADT_A01 # Admit
      - ADT_A03 # Discharge
      - ADT_A08 # Update
    push_predictions_to_ehr: true
    prediction_observation_code: READMIT_RISK

# Monitoring
monitoring:
  # Performance Monitoring
  metrics:
    - auroc
    - auprc
    - sensitivity
    - specificity
    - ppv
    - npv
    - brier_score

  # Drift Detection
  drift_detection:
    enabled: true
    window_size: 1000
    threshold: 0.05
    features_to_monitor: all

  # Fairness Monitoring
  fairness_monitoring:
    enabled: true
    metrics:
      - equal_opportunity
      - demographic_parity
      - calibration_by_group
    protected_groups:
      - race
      - gender
      - age_group

# Compliance
compliance:
  # HIPAA Settings
  hipaa:
    audit_all_access: true
    log_retention_days: 365
    encrypt_at_rest: true
    encrypt_in_transit: true

  # PHI Protection
  phi:
    auto_detect: true
    auto_deidentify: true
    mask_in_logs: true

  # Regulatory
  regulatory:
    require_model_card: true
    require_irb_approval: false
    document_bias_mitigation: true
```

---

## Security & Compliance Configuration

### De-identification Rules

**Location**: `config/deid_rules.yaml`

```yaml
# PHI Elements to Remove
phi_elements:
  - patient_name
  - medical_record_number
  - address
  - phone_number
  - email
  - social_security_number
  - account_number
  - health_plan_beneficiary_number
  - device_identifiers
  - biometric_identifiers
  - full_face_photos
  - any_other_unique_identifying_number

# Date Shifting
date_shifting:
  enabled: true
  shift_range_days: [-365, 365]
  consistent_per_patient: true
  preserve_day_of_week: true

# Age Handling
age_handling:
  truncate_ages_over_89: true
  bin_size_for_elderly: 5

# Geographic Data
geographic_data:
  minimum_granularity: state
  zip_code_handling: first_3_digits

# Quasi-identifiers
quasi_identifiers:
  - race
  - ethnicity
  - gender
  - rare_disease_codes
  - occupation

# Audit Logging
audit:
  log_all_access: true
  log_all_transformations: true
  retention_period_days: 365
```

---

## Deployment Configuration

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nexora-config
  namespace: nexora
data:
  clinical_config.yaml: |
    # Include clinical configuration here
    data:
      fhir:
        base_url: https://fhir-server.svc.cluster.local/R4
    # ... (rest of config)

  application.properties: |
    HOST=0.0.0.0
    PORT=8000
    LOG_LEVEL=INFO
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: nexora-secrets
  namespace: nexora
type: Opaque
stringData:
  SECRET_KEY: "your-secret-key-base64-encoded"
  FHIR_TOKEN: "oauth2-token"
  DATABASE_URL: "postgresql://user:password@db:5432/nexora"
```

---

## Configuration Validation

### Validate Configuration

```bash
# Validate clinical configuration
python -c "
from code.utils.config import load_config
config = load_config('config/clinical_config.yaml')
print('Configuration valid!')
"

# Validate model configuration
python -c "
import yaml
with open('config/model_configs/deepfm_params.yaml') as f:
    config = yaml.safe_load(f)
    assert 'model' in config
    assert 'architecture' in config
    print('Model configuration valid!')
"
```

---

## Configuration Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for sensitive data
3. **Validate configurations** before deployment
4. **Document custom configurations**
5. **Use separate configs** for dev/staging/prod
6. **Version control** configuration files (except secrets)
7. **Test configuration changes** in staging first

---

## Next Steps

- Review [Installation Guide](INSTALLATION.md) for setup
- Check [Usage Guide](USAGE.md) for applying configurations
- Explore [Examples](examples/) for configuration scenarios
- See [Troubleshooting](TROUBLESHOOTING.md) for config issues
