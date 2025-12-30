# CLI Reference

Complete command-line interface reference for Nexora platform, including Makefile targets, Python scripts, and shell commands.

## Table of Contents

- [Overview](#overview)
- [Makefile Commands](#makefile-commands)
- [Python Scripts](#python-scripts)
- [Shell Scripts](#shell-scripts)
- [Configuration Commands](#configuration-commands)

---

## Overview

Nexora provides multiple CLI interfaces:

- **Makefile**: High-level commands for common tasks
- **Python scripts**: Specialized data processing and reporting
- **Shell scripts**: Environment setup and deployment
- **Direct Python modules**: Low-level API access

---

## Makefile Commands

### Setup & Installation

| Command            | Arguments | Description                              | Example            |
| ------------------ | --------- | ---------------------------------------- | ------------------ |
| `make setup`       | None      | Create venv and install all dependencies | `make setup`       |
| `make venv`        | None      | Create Python virtual environment        | `make venv`        |
| `make install`     | None      | Install production dependencies          | `make install`     |
| `make install-dev` | None      | Install development dependencies         | `make install-dev` |
| `make clean`       | None      | Remove build artifacts and cache         | `make clean`       |

**Examples**:

```bash
# Initial setup
make setup

# Clean and reinstall
make clean && make install

# Development setup
make install-dev
```

---

### Testing Commands

| Command                 | Arguments | Description                                 | Example                 |
| ----------------------- | --------- | ------------------------------------------- | ----------------------- |
| `make test`             | None      | Run all tests (unit, integration, clinical) | `make test`             |
| `make test-unit`        | None      | Run unit tests only                         | `make test-unit`        |
| `make test-integration` | None      | Run integration tests                       | `make test-integration` |
| `make test-clinical`    | None      | Run clinical validation tests               | `make test-clinical`    |
| `make test-model`       | None      | Run model performance tests                 | `make test-model`       |
| `make test-coverage`    | None      | Run tests with coverage report              | `make test-coverage`    |

**Examples**:

```bash
# Run all tests
make test

# Run specific test suite
make test-clinical

# Generate coverage report (output in htmlcov/)
make test-coverage
```

---

### Code Quality Commands

| Command               | Arguments | Description                     | Example               |
| --------------------- | --------- | ------------------------------- | --------------------- |
| `make format`         | None      | Format code with Black          | `make format`         |
| `make lint`           | None      | Run linting with flake8         | `make lint`           |
| `make type-check`     | None      | Run type checking with mypy     | `make type-check`     |
| `make security-check` | None      | Run security checks with bandit | `make security-check` |

**Examples**:

```bash
# Format all Python code
make format

# Run all quality checks
make lint && make type-check && make security-check
```

---

### Build Commands

| Command                            | Arguments | Description                       | Example                            |
| ---------------------------------- | --------- | --------------------------------- | ---------------------------------- |
| `make build`                       | None      | Build Python package distribution | `make build`                       |
| `make docker-build`                | None      | Build all Docker images           | `make docker-build`                |
| `make docker-build-model-server`   | None      | Build model server image          | `make docker-build-model-server`   |
| `make docker-build-feature-server` | None      | Build feature server image        | `make docker-build-feature-server` |
| `make docker-build-api-gateway`    | None      | Build API gateway image           | `make docker-build-api-gateway`    |
| `make docker-build-fhir-connector` | None      | Build FHIR connector image        | `make docker-build-fhir-connector` |

**Examples**:

```bash
# Build all Docker images
make docker-build

# Build specific service
make docker-build-model-server

# Build and tag with version
VERSION=2.0.0 make docker-build
```

---

### Deployment Commands

| Command                 | Arguments | Description                        | Example                 |
| ----------------------- | --------- | ---------------------------------- | ----------------------- |
| `make deploy`           | None      | Deploy all services to Kubernetes  | `make deploy`           |
| `make deploy-namespace` | None      | Create Kubernetes namespace        | `make deploy-namespace` |
| `make deploy-config`    | None      | Deploy configs and secrets         | `make deploy-config`    |
| `make deploy-services`  | None      | Deploy all Kubernetes services     | `make deploy-services`  |
| `make docker-push`      | None      | Push all Docker images to registry | `make docker-push`      |
| `make deploy-fhir`      | None      | Deploy FHIR server                 | `make deploy-fhir`      |

**Examples**:

```bash
# Full deployment
make deploy

# Deploy to custom namespace
NAMESPACE=nexora-prod make deploy

# Push images to registry
DOCKER_REGISTRY=myregistry.io make docker-push
```

---

### Data & Utility Commands

| Command             | Arguments | Description                         | Example             |
| ------------------- | --------- | ----------------------------------- | ------------------- |
| `make batch-score`  | None      | Run batch scoring on patient cohort | `make batch-score`  |
| `make data-lineage` | None      | Run data lineage tracking           | `make data-lineage` |
| `make notebooks`    | None      | Start Jupyter notebook server       | `make notebooks`    |
| `make docs`         | None      | Generate documentation              | `make docs`         |

**Examples**:

```bash
# Run batch scoring
make batch-score

# Start Jupyter for analysis
make notebooks

# Generate docs
make docs
```

---

### Help

| Command     | Arguments | Description                 | Example     |
| ----------- | --------- | --------------------------- | ----------- |
| `make help` | None      | Show all available commands | `make help` |

---

## Python Scripts

### Batch Scoring

**Script**: `scripts/batch_scoring.py`

Process multiple patients and generate predictions in batch mode.

**Arguments**:

| Argument       | Type    | Required | Default                       | Description                             |
| -------------- | ------- | -------: | ----------------------------- | --------------------------------------- |
| `--input`      | path    |       ✅ | N/A                           | Input file with patient data (JSON/CSV) |
| `--output`     | path    |       ✅ | N/A                           | Output file for predictions             |
| `--model`      | string  |       ✅ | N/A                           | Model name to use                       |
| `--config`     | path    |       ❌ | `config/clinical_config.yaml` | Configuration file                      |
| `--batch-size` | integer |       ❌ | `100`                         | Batch size for processing               |
| `--verbose`    | flag    |       ❌ | `False`                       | Enable verbose logging                  |

**Examples**:

```bash
# Basic batch scoring
python scripts/batch_scoring.py \
  --input data/patients.json \
  --output results/predictions.json \
  --model readmission_v1

# With custom config and batch size
python scripts/batch_scoring.py \
  --input data/large_cohort.csv \
  --output results/risk_scores.json \
  --model readmission_v1 \
  --config config/custom_config.yaml \
  --batch-size 500 \
  --verbose

# Process and save to specific location
python scripts/batch_scoring.py \
  --input /mnt/ehr/export/patients_2024.json \
  --output /mnt/results/predictions_2024.json \
  --model readmission_transformer
```

---

### Compliance Report Generator

**Script**: `scripts/compliance_report_generator.py`

Generate HIPAA compliance reports from audit logs.

**Arguments**:

| Argument       | Type   | Required | Default               | Description                    |
| -------------- | ------ | -------: | --------------------- | ------------------------------ |
| `--start-date` | date   |       ✅ | N/A                   | Report start date (YYYY-MM-DD) |
| `--end-date`   | date   |       ✅ | N/A                   | Report end date (YYYY-MM-DD)   |
| `--output`     | path   |       ✅ | N/A                   | Output PDF file path           |
| `--audit-db`   | path   |       ❌ | `audit/phi_access.db` | Audit database path            |
| `--format`     | string |       ❌ | `pdf`                 | Output format (pdf/html/json)  |

**Examples**:

```bash
# Generate monthly compliance report
python scripts/compliance_report_generator.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output compliance_january_2024.pdf

# Generate quarterly report in HTML
python scripts/compliance_report_generator.py \
  --start-date 2024-01-01 \
  --end-date 2024-03-31 \
  --output compliance_q1_2024.html \
  --format html

# Custom audit database location
python scripts/compliance_report_generator.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --output annual_compliance_2024.pdf \
  --audit-db /mnt/secure/audit/phi_access.db
```

---

### Environment Health Check

**Script**: `scripts/environment_health_check.py`

Validate deployment environment and dependencies.

**Arguments**:

| Argument          | Type   | Required | Default | Description                           |
| ----------------- | ------ | -------: | ------- | ------------------------------------- |
| `--components`    | string |       ❌ | `all`   | Components to check (comma-separated) |
| `--output`        | path   |       ❌ | stdout  | Output file (JSON format)             |
| `--fail-on-error` | flag   |       ❌ | `False` | Exit with error code on failure       |

**Examples**:

```bash
# Check all components
python scripts/environment_health_check.py

# Check specific components
python scripts/environment_health_check.py --components api,database,fhir

# Output to JSON file
python scripts/environment_health_check.py --output health_status.json

# CI/CD integration (exit with error on failure)
python scripts/environment_health_check.py --fail-on-error
```

---

### Data Lineage

**Script**: `scripts/data_lineage.py`

Track data transformations and provenance.

**Arguments**:

| Argument            | Type   | Required | Default               | Description               |
| ------------------- | ------ | -------: | --------------------- | ------------------------- |
| `--input`           | path   |       ✅ | N/A                   | Input data file           |
| `--output`          | path   |       ❌ | `lineage_report.html` | Output report file        |
| `--openlineage-url` | url    |       ❌ | None                  | OpenLineage server URL    |
| `--format`          | string |       ❌ | `html`                | Output format (html/json) |

**Examples**:

```bash
# Generate lineage report
python scripts/data_lineage.py \
  --input data/processed_patients.json \
  --output lineage_report.html

# With OpenLineage integration
python scripts/data_lineage.py \
  --input data/processed_patients.json \
  --openlineage-url http://marquez:5000 \
  --output lineage_report.json \
  --format json
```

---

### Deployment Validation

**Script**: `scripts/deployment_validation.py`

Validate deployed services and configurations.

**Arguments**:

| Argument        | Type   | Required | Default  | Description                                |
| --------------- | ------ | -------: | -------- | ------------------------------------------ |
| `--environment` | string |       ✅ | N/A      | Environment to validate (dev/staging/prod) |
| `--namespace`   | string |       ❌ | `nexora` | Kubernetes namespace                       |
| `--output`      | path   |       ❌ | stdout   | Validation report output                   |

**Examples**:

```bash
# Validate production deployment
python scripts/deployment_validation.py --environment prod

# Validate custom namespace
python scripts/deployment_validation.py \
  --environment staging \
  --namespace nexora-staging \
  --output validation_report.json
```

---

## Shell Scripts

### Setup Script

**Script**: `scripts/setup.sh`

Automated environment setup.

**Usage**:

```bash
# Basic setup
bash scripts/setup.sh

# Skip dependency check
bash scripts/setup.sh --skip-deps

# Install specific components
bash scripts/setup.sh --components api,frontend
```

---

### Build Script

**Script**: `scripts/build.sh`

Build all project components.

**Usage**:

```bash
# Build everything
bash scripts/build.sh

# Build specific service
bash scripts/build.sh --service model-server

# Build with custom tag
bash scripts/build.sh --tag v2.0.0
```

---

### Run Nexora

**Script**: `scripts/run_nexora.sh`

Start Nexora services locally.

**Usage**:

```bash
# Start all services
bash scripts/run_nexora.sh

# Start specific service
bash scripts/run_nexora.sh --service api

# Start with custom port
bash scripts/run_nexora.sh --port 8080
```

---

### FHIR Deployment

**Script**: `scripts/deploy_fhir.sh`

Deploy FHIR server for testing.

**Usage**:

```bash
# Deploy FHIR server
bash scripts/deploy_fhir.sh

# Deploy with custom config
bash scripts/deploy_fhir.sh --config config/fhir_server.yaml
```

---

### Lint All

**Script**: `scripts/lint-all.sh`

Run all linting tools across the project.

**Usage**:

```bash
# Lint all files
bash scripts/lint-all.sh

# Lint and fix automatically
bash scripts/lint-all.sh --fix

# Lint specific directories
bash scripts/lint-all.sh --dirs code,scripts
```

---

## Configuration Commands

### Validate Configuration

```bash
# Validate clinical configuration
python -m code.validation.pipeline_validator \
  --config config/clinical_config.yaml

# Validate model configuration
python -m code.validation.model_validator \
  --config config/model_configs/deepfm_params.yaml
```

---

### Generate Configuration Template

```bash
# Generate default config
python -c "from code.utils.config import generate_template; generate_template()" \
  > config/my_config.yaml
```

---

### Test Configuration

```bash
# Test configuration loading
python -c "
from code.utils.config import load_config
config = load_config('config/clinical_config.yaml')
print('Configuration loaded successfully')
print(f'Model: {config.get(\"model\", {}).get(\"name\")}')
"
```

---

## Direct Python Module Usage

### Start REST API

```bash
# Start with default settings
python code/run_rest_api.py

# Start with custom host and port
HOST=0.0.0.0 PORT=8080 python code/run_rest_api.py

# Start gRPC server
python -m code.serving.grpc_server --port 50051
```

---

### Start Clinical UI

```bash
# Start Streamlit interface
streamlit run code/interfaces/clinician_ui.py

# With custom port
streamlit run code/interfaces/clinician_ui.py --server.port 8501
```

---

### Generate Synthetic Data

```bash
# Generate 1000 synthetic patients
python -m code.data.synthetic_clinical_data \
  --count 1000 \
  --output data/synthetic_patients.json \
  --seed 42

# Generate with specific characteristics
python -m code.data.synthetic_clinical_data \
  --count 500 \
  --output data/high_risk_cohort.json \
  --risk-profile high \
  --age-range 65-85
```

---

### Run Validation Tests

```bash
# Run all validation tests
python -m code.validation.run_tests

# Run specific validation
python -m code.validation.run_tests --test hipaa_compliance

# Run with verbose output
python -m code.validation.run_tests --verbose
```

---

## Common Workflows

### Development Workflow

```bash
# 1. Setup environment
make setup

# 2. Run tests
make test

# 3. Format and lint code
make format && make lint

# 4. Start services
python code/run_rest_api.py
```

---

### Deployment Workflow

```bash
# 1. Build Docker images
make docker-build

# 2. Run tests
make test

# 3. Push images
make docker-push

# 4. Deploy to Kubernetes
make deploy

# 5. Validate deployment
python scripts/deployment_validation.py --environment prod
```

---

### Clinical Validation Workflow

```bash
# 1. Generate synthetic test data
python -m code.data.synthetic_clinical_data --count 1000 --output test_data.json

# 2. Run batch predictions
python scripts/batch_scoring.py --input test_data.json --output predictions.json --model readmission_v1

# 3. Run clinical validation tests
make test-clinical

# 4. Generate compliance report
python scripts/compliance_report_generator.py --start-date 2024-01-01 --end-date 2024-01-31 --output report.pdf
```

---

## Quick Reference

### Most Common Commands

```bash
# Setup
make setup

# Test
make test

# Run API
python code/run_rest_api.py

# Batch scoring
python scripts/batch_scoring.py --input data.json --output results.json --model readmission_v1

# Build Docker
make docker-build

# Deploy
make deploy

# Compliance report
python scripts/compliance_report_generator.py --start-date 2024-01-01 --end-date 2024-01-31 --output report.pdf
```

---

## Next Steps

- Review [Usage Guide](USAGE.md) for detailed usage patterns
- Check [Configuration](CONFIGURATION.md) for configuration options
- Explore [Examples](examples/) for complete workflows
- See [Troubleshooting](TROUBLESHOOTING.md) for common issues
