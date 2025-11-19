# Tutorials

This section provides step-by-step tutorials for common tasks and workflows in the Hospital Readmission Risk Prediction System.

## Table of Contents

1. [Setting Up a Development Environment](#setting-up-a-development-environment)
2. [Running the Data Pipeline](#running-the-data-pipeline)
3. [Training a Custom Model](#training-a-custom-model)
4. [Deploying a Model](#deploying-a-model)
5. [Integrating with EHR Systems](#integrating-with-ehr-systems)
6. [Using the Clinician Dashboard](#using-the-clinician-dashboard)
7. [Monitoring Model Performance](#monitoring-model-performance)
8. [Implementing Custom Interventions](#implementing-custom-interventions)

## Setting Up a Development Environment

This tutorial guides you through setting up a complete development environment for the Hospital Readmission Risk Prediction System.

### Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Git
- NVIDIA GPU (optional, but recommended for model training)

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/abrar2030/Nexora.git
cd Nexora
```

### Step 2: Set Up Python Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
```

### Step 3: Set Up Data Version Control

```bash
# Initialize DVC
dvc init

# Pull data files
dvc pull
```

### Step 4: Configure Local Settings

```bash
# Copy example configuration
cp config/config.example.yaml config/config.local.yaml

# Edit the configuration file with your local settings
# Use your favorite text editor
nano config/config.local.yaml
```

Example configuration:

```yaml
environment: development

data:
  fhir:
    base_url: http://localhost:8080/fhir
    page_count: 100
  synthetic:
    enabled: true
    patient_count: 1000

model:
  training:
    epochs: 10
    batch_size: 32
    validation_split: 0.2
  fairness_constraints:
    enabled: true
    max_disparity: 0.1

monitoring:
  enabled: true
  log_level: DEBUG
```

### Step 5: Start Local Services

```bash
# Start the development environment
docker-compose up -d
```

### Step 6: Verify Setup

```bash
# Check if services are running
docker-compose ps

# Run tests to verify setup
pytest tests/unit
```

## Running the Data Pipeline

This tutorial guides you through running the clinical data pipeline to process patient data for model training and inference.

### Prerequisites

- Completed development environment setup
- Access to FHIR server or synthetic data generator

### Step 1: Configure Data Sources

Edit `config/data_pipeline.yaml`:

```yaml
sources:
  fhir:
    enabled: true
    server_url: http://localhost:8080/fhir
    resources:
      - Patient
      - Encounter
      - Condition
      - Procedure
      - MedicationRequest
      - Observation
  synthetic:
    enabled: true
    patient_count: 1000
    seed: 42
    demographics:
      age_mean: 65
      age_std: 15
      gender_distribution:
        male: 0.48
        female: 0.51
        other: 0.01
```

### Step 2: Run the ETL Pipeline

```bash
# Run the full pipeline
python -m src.data_pipeline.clinical_etl --config config/data_pipeline.yaml

# Alternatively, use the make command
make clinical-pipeline FHIR_SERVER=http://localhost:8080/fhir
```

### Step 3: Verify Data Processing

```bash
# Check the processed data
python -m src.data.data_explorer --dataset processed_data.parquet

# Output should show dataset statistics
# Example output:
# Dataset: processed_data.parquet
# Number of patients: 1000
# Number of features: 256
# Missing values: 2.3%
# Class distribution:
#   - Readmitted: 15.2%
#   - Not readmitted: 84.8%
```

### Step 4: Generate Temporal Features

```bash
# Generate temporal features
python -m src.data_pipeline.temporal_features --input processed_data.parquet --output temporal_features.parquet

# Verify temporal features
python -m src.data.data_explorer --dataset temporal_features.parquet
```

### Step 5: Encode Categorical Features

```bash
# Encode ICD-10 codes
python -m src.data_pipeline.icd10_encoder --input temporal_features.parquet --output encoded_data.parquet

# Verify encoded data
python -m src.data.data_explorer --dataset encoded_data.parquet
```

## Training a Custom Model

This tutorial guides you through training a custom readmission risk prediction model.

### Prerequisites

- Completed data pipeline tutorial
- GPU environment recommended for training

### Step 1: Configure Model Training

Create a training configuration file `config/model_training.yaml`:

```yaml
model:
  type: deep_survival_transformer
  parameters:
    embedding_dim: 128
    num_heads: 8
    num_layers: 4
    dropout_rate: 0.2
    learning_rate: 0.0001

training:
  batch_size: 64
  epochs: 50
  early_stopping:
    patience: 5
    monitor: val_auc
  class_weights:
    enabled: true
  data_augmentation:
    enabled: false

evaluation:
  metrics:
    - auc_roc
    - sensitivity
    - specificity
    - ppv
    - npv
    - brier_score
    - calibration_slope
  fairness:
    protected_attributes:
      - gender
      - race
      - age_group
    metrics:
      - equal_opportunity_diff
      - demographic_parity_ratio

output:
  model_dir: models/custom_model
  tensorboard_dir: logs/custom_model
  save_best_only: true
```

### Step 2: Prepare Training Data

```bash
# Split data into train, validation, and test sets
python -m src.model_factory.data_splitter \
  --input encoded_data.parquet \
  --output-dir data/split \
  --train-ratio 0.7 \
  --val-ratio 0.15 \
  --test-ratio 0.15 \
  --stratify readmission_30d
```

### Step 3: Train the Model

```bash
# Train the model
python -m src.model_factory.train \
  --config config/model_training.yaml \
  --train-data data/split/train.parquet \
  --val-data data/split/val.parquet \
  --test-data data/split/test.parquet
```

### Step 4: Monitor Training Progress

```bash
# Start TensorBoard to monitor training
tensorboard --logdir logs/custom_model
```

Access TensorBoard at http://localhost:6006

### Step 5: Evaluate the Model

```bash
# Evaluate the model on test data
python -m src.model_factory.evaluate \
  --model-dir models/custom_model \
  --test-data data/split/test.parquet \
  --output-dir evaluation/custom_model
```

### Step 6: Analyze Fairness

```bash
# Analyze model fairness
python -m src.monitoring.fairness_metrics \
  --model-dir models/custom_model \
  --test-data data/split/test.parquet \
  --protected-attributes gender,race,age_group \
  --output-dir evaluation/custom_model/fairness
```

## Deploying a Model

This tutorial guides you through deploying a trained model for inference.

### Prerequisites

- Completed model training tutorial
- Kubernetes cluster for production deployment

### Step 1: Package the Model

```bash
# Package the model for deployment
python -m src.serving.model_packager \
  --model-dir models/custom_model \
  --output-dir deployment/models/custom_model \
  --version 1.0.0
```

### Step 2: Build Docker Image

```bash
# Build Docker image for model serving
docker build -t readmission-model:1.0.0 -f deployments/docker/model-serving.Dockerfile .
```

### Step 3: Test Locally

```bash
# Run the model server locally
docker run -p 8001:8001 readmission-model:1.0.0

# Test with sample data
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d @tests/fixtures/sample_patient.json
```

### Step 4: Push to Container Registry

```bash
# Tag the image
docker tag readmission-model:1.0.0 ghcr.io/health-ai/readmission-model:1.0.0

# Push to registry
docker push ghcr.io/health-ai/readmission-model:1.0.0
```

### Step 5: Deploy to Kubernetes

```bash
# Update Helm values
cat > values-custom.yaml << EOF
modelServing:
  image: ghcr.io/health-ai/readmission-model:1.0.0
  replicas: 2
  resources:
    requests:
      memory: "4Gi"
      cpu: "1000m"
    limits:
      memory: "8Gi"
      cpu: "2000m"
  gpu:
    enabled: true
    count: 1
EOF

# Deploy using Helm
helm upgrade --install readmission ./deployments/helm \
  --namespace readmission-system \
  --values values-custom.yaml
```

### Step 6: Verify Deployment

```bash
# Check if pods are running
kubectl get pods -n readmission-system

# Test the deployed API
kubectl port-forward svc/readmission-api 8000:8000 -n readmission-system

# In another terminal
curl -X POST http://localhost:8000/api/v1/predict/readmission \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @tests/fixtures/sample_patient.json
```

## Integrating with EHR Systems

This tutorial guides you through integrating the Hospital Readmission Risk Prediction System with Electronic Health Record (EHR) systems.

### Prerequisites

- Deployed model
- Access to EHR system with FHIR API

### Step 1: Configure FHIR Connector

Edit `config/fhir_connector.yaml`:

```yaml
fhir:
  server_url: https://fhir.hospital.org/R4
  client_id: your_client_id
  client_secret: your_client_secret
  version: R4
  resources:
    - Patient
    - Encounter
    - Condition
    - Procedure
    - MedicationRequest
    - Observation
  batch_size: 100
```

### Step 2: Test FHIR Connection

```bash
# Test FHIR connection
python -m src.utils.fhir_connector --test --config config/fhir_connector.yaml
```

### Step 3: Implement SMART on FHIR Launch

Create a SMART on FHIR launch file:

```html
<!-- public/launch.html -->
<!DOCTYPE html>
<html>
<head>
  <title>Readmission Risk SMART Launch</title>
  <script src="https://cdn.jsdelivr.net/npm/fhirclient/build/fhir-client.js"></script>
  <script>
    FHIR.oauth2.authorize({
      clientId: 'readmission_risk_app',
      scope: 'patient/*.read launch',
      redirectUri: 'https://app.readmission-risk.org/app',
      completeInTarget: true
    });
  </script>
</head>
<body>
  <h1>Launching Readmission Risk Prediction App...</h1>
</body>
</html>
```

### Step 4: Implement EHR Integration

Create an integration script:

```python
# src/utils/ehr_integration.py
import os
import json
import requests
from fhirclient import client
from src.utils.fhir_connector import FHIRConnector
from src.model_factory.predictor import Predictor

class EHRIntegration:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.fhir_connector = FHIRConnector(self.config['fhir'])
        self.predictor = Predictor(self.config['model']['path'])

    def get_patient_data(self, patient_id):
        """Retrieve patient data from EHR system."""
        return self.fhir_connector.get_patient_bundle(patient_id)

    def predict_readmission_risk(self, patient_id):
        """Predict readmission risk for a patient."""
        patient_data = self.get_patient_data(patient_id)
        processed_data = self.fhir_connector.process_patient_bundle(patient_data)
        prediction = self.predictor.predict(processed_data)
        return prediction

    def send_alert(self, patient_id, prediction):
        """Send alert to EHR system."""
        if prediction['readmission_risk'] >= self.config['alert_threshold']:
            alert_data = {
                'resourceType': 'Communication',
                'status': 'in-progress',
                'category': [{
                    'coding': [{
                        'system': 'http://terminology.hl7.org/CodeSystem/communication-category',
                        'code': 'alert',
                        'display': 'Alert'
                    }]
                }],
                'subject': {
                    'reference': f'Patient/{patient_id}'
                },
                'payload': [{
                    'contentString': f"Readmission Risk Alert: {prediction['readmission_risk']:.2f}"
                }]
            }

            response = self.fhir_connector.client.create(alert_data)
            return response

        return None
```

### Step 5: Deploy Integration Service

```bash
# Build Docker image for EHR integration
docker build -t readmission-ehr-integration:1.0.0 -f deployments/docker/ehr-integration.Dockerfile .

# Deploy to Kubernetes
kubectl apply -f deployments/kubernetes/ehr-integration.yaml
```

### Step 6: Configure EHR Hooks

Set up CDS Hooks in your EHR system:

```json
{
  "hooks": [
    {
      "hook": "patient-view",
      "title": "Readmission Risk Assessment",
      "description": "Provides readmission risk assessment for the current patient",
      "id": "readmission-risk-assessment",
      "prefetch": {
        "patient": "Patient/{{context.patientId}}"
      }
    }
  ],
  "services": [
    {
      "title": "Readmission Risk Service",
      "id": "readmission-risk-service",
      "url": "https://api.readmission-risk.org/cds-services"
    }
  ]
}
```

## Using the Clinician Dashboard

This tutorial guides you through using the clinician dashboard to view and interpret readmission risk predictions.

### Prerequisites

- Deployed system
- Clinician access credentials

### Step 1: Access the Dashboard

1. Navigate to https://ui.readmission-risk.org
2. Log in with your clinician credentials
3. You will see the main dashboard with patient list and risk distribution

### Step 2: View Patient Risk

1. Search for a patient using the search bar
2. Click on a patient to view their detailed risk profile
3. The patient profile shows:
   - Current readmission risk score
   - Risk trend over time
   - Contributing factors
   - Recommended interventions

### Step 3: Interpret Risk Factors

1. In the patient profile, navigate to the "Risk Factors" tab
2. Review the list of factors contributing to readmission risk
3. Each factor shows:
   - Factor name
   - Contribution percentage
   - Trend (increasing/decreasing/stable)
   - Clinical context

### Step 4: Implement Interventions

1. Navigate to the "Interventions" tab
2. Review recommended interventions
3. Select interventions to implement
4. Assign responsibility to team members
5. Set target dates for completion

### Step 5: Track Outcomes

1. Navigate to the "Outcomes" tab
2. Review the impact of implemented interventions
3. Track readmission rates over time
4. Compare with baseline and benchmarks

### Step 6: Generate Reports

1. Click on "Reports" in the main menu
2. Select report type (daily, weekly, monthly)
3. Choose parameters and filters
4. Generate and download the report

## Monitoring Model Performance

This tutorial guides you through monitoring the performance of deployed models.

### Prerequisites

- Deployed model
- Access to monitoring tools

### Step 1: Access Monitoring Dashboard

1. Navigate to https://monitoring.readmission-risk.org
2. Log in with your administrator credentials
3. You will see the main monitoring dashboard

### Step 2: Monitor Prediction Metrics

1. Navigate to the "Prediction Metrics" tab
2. Review key performance indicators:
   - Request volume
   - Response time
   - Error rate
   - Prediction distribution

### Step 3: Monitor Model Performance

1. Navigate to the "Model Performance" tab
2. Review performance metrics:
   - AUC-ROC
   - Sensitivity
   - Specificity
   - Calibration

### Step 4: Detect Concept Drift

1. Navigate to the "Concept Drift" tab
2. Review drift detection metrics:
   - Feature distribution drift
   - Prediction distribution drift
   - Performance drift
   - Data quality metrics

### Step 5: Set Up Alerts

1. Navigate to the "Alerts" tab
2. Configure alert thresholds:
   - Performance degradation
   - Drift detection
   - Fairness violations
   - System errors

3. Configure notification channels:
   - Email
   - Slack
   - PagerDuty

### Step 6: Generate Performance Reports

1. Navigate to the "Reports" tab
2. Select report type:
   - Daily performance
   - Weekly drift analysis
   - Monthly fairness audit
3. Generate and download the report

## Implementing Custom Interventions

This tutorial guides you through implementing custom interventions based on readmission risk predictions.

### Prerequisites

- Access to the clinician dashboard
- Care coordinator role

### Step 1: Analyze Patient Risk Factors

1. Access the patient profile
2. Review risk factors and their contributions
3. Identify modifiable risk factors

### Step 2: Design Custom Intervention

1. Navigate to the "Interventions" tab
2. Click "Add Custom Intervention"
3. Fill in intervention details:
   - Name
   - Description
   - Target risk factors
   - Expected impact
   - Required resources
   - Implementation timeline

### Step 3: Implement Intervention Workflow

1. Define intervention steps
2. Assign responsibilities to team members
3. Set up follow-up schedule
4. Define success criteria

### Step 4: Document Intervention

Create an intervention template:

```yaml
intervention:
  name: "Medication Reconciliation Program"
  description: "Comprehensive medication review and reconciliation for patients with polypharmacy"
  target_factors:
    - "polypharmacy"
    - "medication_adherence"
    - "drug_interactions"
  expected_impact: "Reduce medication-related readmissions by 20%"
  steps:
    - name: "Initial Medication Review"
      responsible: "Clinical Pharmacist"
      timeline: "Within 24 hours of identification"
    - name: "Patient Education Session"
      responsible: "Nurse Educator"
      timeline: "Within 48 hours of identification"
    - name: "Follow-up Phone Call"
      responsible: "Care Coordinator"
      timeline: "7 days after discharge"
    - name: "Medication Adherence Check"
      responsible: "Primary Care Provider"
      timeline: "14 days after discharge"
  success_criteria:
    - "90% of patients have complete medication reconciliation"
    - "80% of patients demonstrate understanding of medication regimen"
    - "70% reduction in medication discrepancies"
```

### Step 5: Track Intervention Effectiveness

1. Navigate to the "Outcomes" tab
2. Select the custom intervention
3. Review effectiveness metrics:
   - Implementation rate
   - Completion rate
   - Impact on readmission risk
   - Cost-effectiveness

### Step 6: Refine and Scale

1. Analyze intervention results
2. Identify improvement opportunities
3. Refine intervention design
4. Scale to additional patients or units
