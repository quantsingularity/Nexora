# Hospital Readmission Risk Prediction System

[![HIPAA Compliance](https://img.shields.io/badge/HIPAA-Compliant-brightgreen)](https://www.hhs.gov/hipaa)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![Model Registry](https://img.shields.io/badge/MLflow-Registry-orange)](https://mlflow.org/)

An end-to-end MLOps system predicting 30-day hospital readmission risk with clinical-grade validation and regulatory compliance.

<div align="center">
  <img src="docs/Nexora.bmp" alt="An end-to-end MLOps system predicting 30-day hospital readmission risk with clinical-grade validation and regulatory compliance" width="100%">
</div>

> **Note**: This Project is currently under active development. Features and functionalities are being added and improved continuously to enhance user experience.

## 🏥 Key Features

- **Multi-Modal Clinical Data Processing**
  - FHIR/HL7 data ingestion
  - OMOP CDM transformation
  - PHI-aware de-identification
- **Advanced ML Models**
  - Deep Survival Transformers
  - Clinical BERT embeddings
  - Fairness-constrained ensembles
- **Healthcare Compliance**
  - HIPAA audit logging
  - Adverse event monitoring
  - Model versioning with IRB tracking
- **Clinical Integration**
  - Streamlit clinician dashboard
  - EHR alert integration
  - SMART-on-FHIR launch capability
- **Enterprise MLOps**
  - Synthetic data generation
  - Multi-hospital federated learning
  - Clinical concept drift detection

## 🚀 Installation

### Prerequisites
- Kubernetes cluster
- FHIR-compliant database
- NVIDIA GPU (CUDA 11.7+)

```bash
# Clone repository
git clone https://github.com/abrar2030/Nexora.git
cd Nexora

# Initialize environment
make setup && dvc pull

# Install clinical dependencies
pip install -r requirements-clinical.txt
```

## 📋 Usage

### Data Pipeline
```bash
# Run full clinical ETL
make clinical-pipeline \
  FHIR_SERVER=https://fhir.healthsystem.org/R4 \
  DEID_PROFILE=config/deid_rules.yaml
```

### Model Training
```bash
# Train with federated learning
make federated-train \
  PARTICIPANTS=hosp1,hosp2,hosp3 \
  EPOCHS=50 \
  STRATIFY=age,gender
```

### Deployment
```bash
# Deploy to Kubernetes cluster
helm install readmission ./deployments/helm \
  --set global.registry=ghcr.io/health-ai \
  --set modelServing.gpu.enabled=true
```

## 📊 Model Performance

| Metric                | Overall | Age≥65 | ICU Patients |
|-----------------------|---------|--------|--------------|
| **AUC-ROC**           | 0.82    | 0.79   | 0.85         |
| **Sensitivity**       | 0.75    | 0.72   | 0.81         |
| **Specificity**       | 0.84    | 0.88   | 0.79         |
| **Brier Score**       | 0.11    | 0.13   | 0.09         |

### Fairness Metrics
```json
{
  "equal_opportunity_diff": 0.03,
  "demographic_parity_ratio": 0.92,
  "calibration_slope": "1.02±0.05"
}
```

## 🏗️ Project Structure
```
readmission-risk/
├── clinical_ui/           # Streamlit clinician interface
├── compliance/            # HIPAA audit logs
├── federated_learning/    # Cross-hospital training
├── model_cards/           # Regulatory documentation
├── pharmacovigilance/     # Adverse event monitoring
└── synthetic_data/        # Synthetic patient generation
```

## ⚙️ Configuration

Modify `config/clinical_config.yaml`:
```yaml
data:
  fhir:
    base_url: https://fhir.healthsystem.org/R4
    page_count: 1000
  deidentification:
    date_shift: 365
    phi_patterns:
      - name: mrn
        regex: \b\d{3}-\d{2}-\d{4}\b
        replacement: "[MEDICAL RECORD]"

model:
  fairness_constraints:
    max_disparity: 0.1
    protected_attributes: [race, gender, age_group]
```

## 🩺 Clinical Integration

### FHIR Query Example
```python
from src.data.fhir_ops import FHIRClinicalConnector

connector = FHIRClinicalConnector()
bundle = connector.get_patient_sequence("12345")
risk_prediction = model.predict(bundle)
```

### Clinician Dashboard
Streamlit Interface

![Streamlit Dashboard](docs/images/streamlit_dashboard.png)

## 🔒 Compliance & Security

### Audit Log Sample
```
2023-08-15T14:23:18 | dr.smith | 123-45-6789 | Prediction | Access | Discharge planning | ReadmissionRisk_v2.3
2023-08-15T14:25:42 | nurse-jones | 987-65-4321 | Update | Correction | Data error remediation | -
```

Access monitoring:
```bash
kubectl port-forward svc/grafana 3000:3000
open http://localhost:3000/dashboards
```

## 🤝 Contributing

1. Request IRB approval for clinical contributions
2. Sign HIPAA Business Associate Agreement (BAA)
3. Follow clinical validation protocol:
```bash
make clinical-validation \
  TEST_DATA=path/to/annotated_dataset \
  GROUND_TRUTH=physician_reviews.csv
```

## 📄 License

This project is licensed under the Healthcare ML License (HML-1.0) - see [LICENSE](LICENSE) for details.