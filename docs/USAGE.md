# Usage Guide

Comprehensive guide for using Nexora in various scenarios, from basic API calls to advanced clinical workflows.

## Table of Contents

- [Quick Start](#quick-start)
- [CLI Usage](#cli-usage)
- [Library Usage](#library-usage)
- [API Usage](#api-usage)
- [Common Workflows](#common-workflows)
- [Advanced Usage](#advanced-usage)

---

## Quick Start

### Starting the API Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start the REST API server
python code/run_rest_api.py

# Server starts on http://localhost:8000
# API documentation: http://localhost:8000/docs
```

### Making Your First Prediction

```bash
# Using curl
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "readmission_v1",
    "patient_data": {
      "patient_id": "12345",
      "demographics": {"age": 65, "gender": "M"},
      "clinical_events": [
        {"type": "diagnosis", "code": "I50.9", "description": "Heart failure"}
      ]
    }
  }'
```

---

## CLI Usage

### Using Make Commands

Nexora provides a comprehensive Makefile for common tasks:

#### Setup & Installation

```bash
# Setup development environment (create venv, install deps)
make setup

# Install production dependencies only
make install

# Install with development tools
make install-dev

# Create virtual environment
make venv
```

#### Testing

```bash
# Run all tests (unit + integration + clinical)
make test

# Run specific test suites
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-clinical     # Clinical validation tests
make test-model        # Model performance tests

# Run tests with coverage report
make test-coverage     # Generates HTML coverage report
```

#### Code Quality

```bash
# Format code with Black
make format

# Run linting with flake8
make lint

# Run type checking with mypy
make type-check

# Run security checks with bandit
make security-check
```

#### Building & Deployment

```bash
# Build Python package
make build

# Build all Docker images
make docker-build

# Build specific service images
make docker-build-model-server
make docker-build-feature-server
make docker-build-api-gateway
make docker-build-fhir-connector

# Push Docker images to registry
make docker-push
```

#### Kubernetes Deployment

```bash
# Deploy everything to Kubernetes
make deploy

# Deploy individual components
make deploy-namespace  # Create namespace
make deploy-config     # Deploy configs and secrets
make deploy-services   # Deploy all services
```

#### Data & Scripts

```bash
# Run batch scoring on patient cohort
make batch-score

# Generate compliance report
python scripts/compliance_report_generator.py --output report.pdf

# Run data lineage tracking
make data-lineage

# Deploy FHIR server
make deploy-fhir
```

#### Documentation & Notebooks

```bash
# Generate documentation
make docs

# Start Jupyter notebook server
make notebooks
```

#### Maintenance

```bash
# Clean build artifacts and cache
make clean

# Show all available make targets
make help
```

### Script Usage

#### Batch Scoring

Process multiple patients at once:

```bash
# Basic batch scoring
python scripts/batch_scoring.py \
  --input data/patients.json \
  --output results/predictions.json \
  --model readmission_v1

# With configuration
python scripts/batch_scoring.py \
  --input data/patients.json \
  --output results/predictions.json \
  --model readmission_v1 \
  --config config/clinical_config.yaml \
  --batch-size 100
```

#### Compliance Reporting

Generate HIPAA compliance reports:

```bash
# Generate monthly compliance report
python scripts/compliance_report_generator.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --output compliance_january_2024.pdf

# With specific audit database
python scripts/compliance_report_generator.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --audit-db audit/phi_access.db \
  --output compliance_report.pdf
```

#### Environment Health Check

Validate deployment environment:

```bash
# Check all system components
python scripts/environment_health_check.py

# Check specific components
python scripts/environment_health_check.py --components api,database,fhir

# Output to JSON
python scripts/environment_health_check.py --output health_status.json
```

#### Data Lineage

Track data transformations and provenance:

```bash
# Run data lineage analysis
python scripts/data_lineage.py \
  --input data/raw_patients.json \
  --output lineage_report.html

# With OpenLineage integration
python scripts/data_lineage.py \
  --input data/raw_patients.json \
  --openlineage-url http://marquez:5000
```

---

## Library Usage

### Python API Integration

#### Basic Prediction

```python
from code.serving.rest_api import app
from code.model_factory.model_registry import ModelRegistry
from code.data.synthetic_clinical_data import ClinicalDataGenerator

# Load model
registry = ModelRegistry()
model = registry.get_model("readmission_v1")

# Prepare patient data
patient_data = {
    "patient_id": "12345",
    "demographics": {
        "age": 68,
        "gender": "M",
        "race": "Caucasian"
    },
    "clinical_events": [
        {
            "type": "diagnosis",
            "code": "I50.9",
            "description": "Heart failure, unspecified"
        },
        {
            "type": "diagnosis",
            "code": "E11.9",
            "description": "Type 2 diabetes mellitus"
        }
    ],
    "lab_results": [
        {"name": "HbA1c", "value": 8.2, "unit": "%"},
        {"name": "eGFR", "value": 45, "unit": "mL/min/1.73m²"}
    ],
    "medications": [
        {"name": "Metformin", "dose": "1000mg", "frequency": "BID"},
        {"name": "Lisinopril", "dose": "10mg", "frequency": "QD"}
    ]
}

# Make prediction
prediction = model.predict(patient_data)
print(f"Readmission Risk: {prediction['risk']:.2%}")
print(f"Risk Level: {prediction['risk_level']}")

# Get explanation
explanation = model.explain(patient_data)
print(f"Top Risk Factors: {explanation['top_features']}")
```

#### FHIR Integration

```python
from code.utils.fhir_connector import FHIRConnector

# Initialize FHIR connector
fhir_client = FHIRConnector(base_url="https://fhir-server.example.org/R4")

# Fetch patient data from FHIR server
patient_id = "example-patient-123"
patient_bundle = fhir_client.get_patient_data(patient_id)

# Convert FHIR bundle to model input format
from code.utils.fhir_ops import FHIRClinicalConnector

connector = FHIRClinicalConnector()
model_input = connector.transform_fhir_to_model_input(patient_bundle)

# Make prediction
prediction = model.predict(model_input)
```

#### Data Pipeline Processing

```python
from code.data_pipeline.clinical_etl import ClinicalETL
from code.data_pipeline.hipaa_compliance.deidentifier import Deidentifier

# Initialize ETL pipeline
etl = ClinicalETL(config_path="config/clinical_config.yaml")

# Load and process raw clinical data
raw_data = etl.load_from_source("data/raw_ehr_export.csv")

# Apply de-identification
deidentifier = Deidentifier(rules_path="config/deid_rules.yaml")
clean_data = deidentifier.process(raw_data)

# Extract features
features = etl.extract_features(clean_data)

# Transform to model-ready format
model_ready_data = etl.transform(features)
```

#### Model Training

```python
from code.model_factory.deep_fm import DeepFMModel
from code.model_factory.model_registry import ModelRegistry

# Initialize model
model = DeepFMModel(config={
    "embedding_dim": 128,
    "hidden_layers": [256, 128, 64],
    "dropout": 0.3,
    "learning_rate": 0.001
})

# Train model
train_data, val_data = load_training_data()
model.train(
    train_data=train_data,
    validation_data=val_data,
    epochs=50,
    batch_size=256
)

# Evaluate model
metrics = model.evaluate(val_data)
print(f"AUROC: {metrics['auroc']:.3f}")
print(f"AUPRC: {metrics['auprc']:.3f}")

# Register model
registry = ModelRegistry()
registry.register_model(
    model=model,
    name="readmission_deepfm_v2",
    version="2.0.0",
    metadata={
        "training_date": "2024-01-15",
        "performance": metrics
    }
)
```

#### Compliance & Auditing

```python
from code.compliance.phi_audit_logger import PHIAuditLogger

# Initialize audit logger
audit_logger = PHIAuditLogger(db_path="audit/phi_access.db")

# Log prediction request
audit_logger.log_prediction_request(
    patient_id="12345",
    user_id="dr.smith@hospital.org",
    model_used="readmission_v1",
    context="Discharge planning",
    timestamp=None  # Auto-generated
)

# Query audit logs
logs = audit_logger.query_logs(
    start_date="2024-01-01",
    end_date="2024-01-31",
    user_id="dr.smith@hospital.org"
)

for log in logs:
    print(f"{log.timestamp} - {log.action} - {log.patient_id}")
```

#### Monitoring & Metrics

```python
from code.monitoring.clinical_metrics import ClinicalMetricsCalculator
from code.monitoring.fairness_metrics import FairnessEvaluator

# Calculate clinical metrics
metrics_calc = ClinicalMetricsCalculator()
predictions = [...] # Your predictions
ground_truth = [...] # Actual outcomes

metrics = metrics_calc.calculate_all(predictions, ground_truth)
print(f"Sensitivity: {metrics['sensitivity']:.3f}")
print(f"Specificity: {metrics['specificity']:.3f}")
print(f"PPV: {metrics['ppv']:.3f}")
print(f"NPV: {metrics['npv']:.3f}")

# Evaluate fairness
fairness = FairnessEvaluator()
fairness_metrics = fairness.evaluate(
    predictions=predictions,
    ground_truth=ground_truth,
    protected_attributes=patient_demographics
)
print(f"Equal Opportunity Diff: {fairness_metrics['equal_opportunity_diff']:.3f}")
print(f"Demographic Parity: {fairness_metrics['demographic_parity']:.3f}")
```

---

## API Usage

### REST API Endpoints

#### Health Check

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### List Available Models

```bash
curl http://localhost:8000/models
```

Response:

```json
{
  "models": [
    {
      "name": "readmission_v1",
      "version": "1.0.0",
      "type": "DeepFM",
      "status": "active"
    }
  ]
}
```

#### Make Prediction

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "model_name": "readmission_v1",
    "patient_data": {
      "patient_id": "12345",
      "demographics": {"age": 65, "gender": "M"},
      "clinical_events": [
        {"type": "diagnosis", "code": "I50.9"}
      ]
    }
  }'
```

Response:

```json
{
  "request_id": "req_20240115103000",
  "model_name": "readmission_v1",
  "model_version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "predictions": {
    "risk": 0.75,
    "risk_level": "high",
    "top_features": ["previous_admissions", "heart_failure", "age"]
  },
  "explanations": {
    "method": "SHAP",
    "feature_contributions": {
      "previous_admissions": 0.25,
      "heart_failure": 0.2,
      "age": 0.15
    }
  },
  "uncertainty": {
    "confidence_interval": [0.65, 0.85]
  }
}
```

#### FHIR-based Prediction

```bash
curl -X POST "http://localhost:8000/fhir/patient/12345/predict?model_name=readmission_v1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Common Workflows

### Workflow 1: Discharge Planning

```python
# 1. Retrieve patient data from EHR
from code.utils.fhir_connector import FHIRConnector

fhir = FHIRConnector(base_url=FHIR_SERVER_URL)
patient_data = fhir.get_patient_data("patient-123")

# 2. Generate risk prediction
from code.model_factory.model_registry import ModelRegistry

model = ModelRegistry().get_model("readmission_v1")
prediction = model.predict(patient_data)

# 3. Log for audit trail
from code.compliance.phi_audit_logger import PHIAuditLogger

audit = PHIAuditLogger()
audit.log_prediction_request(
    patient_id="patient-123",
    user_id="dr.smith",
    model_used="readmission_v1",
    context="Discharge planning"
)

# 4. Generate intervention recommendations
if prediction['risk'] > 0.6:
    print("HIGH RISK - Recommend:")
    print("- Post-discharge follow-up within 7 days")
    print("- Home health services")
    print("- Medication reconciliation")
```

### Workflow 2: Batch Risk Stratification

```bash
# Process entire patient cohort
python scripts/batch_scoring.py \
  --input data/patients_cohort.json \
  --output results/risk_stratification.json \
  --model readmission_v1

# Generate summary report
python scripts/generate_cohort_report.py \
  --predictions results/risk_stratification.json \
  --output reports/cohort_analysis.pdf
```

### Workflow 3: Model Validation

```python
from code.monitoring.clinical_metrics import ClinicalMetricsCalculator
from code.monitoring.fairness_metrics import FairnessEvaluator

# Load test dataset
test_data = load_test_data("data/test_cohort.json")

# Generate predictions
predictions = model.predict_batch(test_data)

# Calculate clinical metrics
metrics = ClinicalMetricsCalculator().calculate_all(
    predictions=predictions,
    ground_truth=test_data['outcomes']
)

# Evaluate fairness across demographics
fairness = FairnessEvaluator().evaluate(
    predictions=predictions,
    ground_truth=test_data['outcomes'],
    protected_attributes=test_data['demographics']
)

# Generate validation report
print(f"AUROC: {metrics['auroc']:.3f}")
print(f"Equal Opportunity Difference: {fairness['equal_opportunity_diff']:.3f}")
```

---

## Advanced Usage

### Custom Model Development

```python
from code.model_factory.base_model import BaseModel
import torch.nn as nn

class CustomRiskModel(BaseModel):
    def __init__(self, config):
        super().__init__(config)
        self.network = self._build_network()

    def _build_network(self):
        # Define your custom architecture
        return nn.Sequential(
            nn.Linear(self.config['input_dim'], 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def predict(self, patient_data):
        # Implement prediction logic
        features = self.preprocess(patient_data)
        risk_score = self.network(features)
        return {"risk": risk_score.item()}

    def explain(self, patient_data):
        # Implement explanation logic (SHAP, LIME, etc.)
        return {"method": "custom", "features": [...]}
```

### Federated Learning Setup

```python
# Configure federated learning across multiple hospitals
from code.federated_learning.coordinator import FederatedCoordinator

coordinator = FederatedCoordinator(
    hospitals=["hospital_A", "hospital_B", "hospital_C"],
    aggregation_method="federated_averaging",
    rounds=10
)

# Train model across sites without sharing patient data
global_model = coordinator.train_federated_model(
    model_class=DeepFMModel,
    config=model_config
)
```

### Real-time Monitoring Dashboard

```bash
# Start Streamlit clinical dashboard
streamlit run code/interfaces/clinician_ui.py

# Access dashboard at http://localhost:8501
```

---

## Next Steps

- Explore detailed [API Reference](API.md)
- Review [Examples](examples/) for specific use cases
- Check [Configuration](CONFIGURATION.md) for customization
- Read [Architecture](ARCHITECTURE.md) to understand system design
