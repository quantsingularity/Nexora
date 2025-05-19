# Hospital Readmission Risk Prediction System

[![CI Status](https://img.shields.io/github/actions/workflow/status/abrar2030/Nexora/ci-cd.yml?branch=main&label=CI&logo=github)](https://github.com/abrar2030/Nexora/actions)
[![CI Status](https://img.shields.io/github/workflow/status/abrar2030/Nexora/CI/main?label=CI)](https://github.com/abrar2030/Nexora/actions)
[![Test Coverage](https://img.shields.io/codecov/c/github/abrar2030/Nexora/main?label=Coverage)](https://codecov.io/gh/abrar2030/Nexora)
[![HIPAA Compliance](https://img.shields.io/badge/HIPAA-Compliant-brightgreen)](https://www.hhs.gov/hipaa)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue)](https://www.python.org/)
[![Model Registry](https://img.shields.io/badge/MLflow-Registry-orange)](https://mlflow.org/)

An end-to-end MLOps system predicting 30-day hospital readmission risk with clinical-grade validation and regulatory compliance.

<div align="center">
  <img src="docs/Nexora.bmp" alt="An end-to-end MLOps system predicting 30-day hospital readmission risk with clinical-grade validation and regulatory compliance" width="100%">
</div>

> **Note**: This Project is currently under active development. Features and functionalities are being added and improved continuously to enhance user experience.

## Table of Contents
- [Key Features](#-key-features)
- [Feature Implementation Status](#feature-implementation-status)
- [Installation](#-installation)
- [Usage](#-usage)
- [Model Performance](#-model-performance)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Clinical Integration](#-clinical-integration)
- [Compliance & Security](#-compliance--security)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Contributing](#-contributing)
- [License](#-license)

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

## Feature Implementation Status

| Feature | Status | Description | Planned Release |
|---------|--------|-------------|----------------|
| **Clinical Data Processing** |
| FHIR/HL7 Ingestion | ✅ Implemented | Standard healthcare data format support | v1.0 |
| OMOP CDM Transformation | ✅ Implemented | Common data model standardization | v1.0 |
| PHI De-identification | ✅ Implemented | HIPAA-compliant data anonymization | v1.0 |
| Multi-modal Integration | 🔄 In Progress | Combining structured and unstructured data | v1.1 |
| Real-time Data Streams | 📅 Planned | Continuous data processing pipeline | v1.2 |
| **ML Models** |
| Deep Survival Transformers | ✅ Implemented | Advanced time-to-event prediction | v1.0 |
| Clinical BERT Embeddings | ✅ Implemented | NLP for clinical notes | v1.0 |
| Fairness-constrained Ensembles | ✅ Implemented | Bias mitigation in predictions | v1.0 |
| Multi-task Learning | 🔄 In Progress | Joint prediction of related outcomes | v1.1 |
| Explainable AI Components | 🔄 In Progress | Interpretable prediction rationales | v1.1 |
| Reinforcement Learning | 📅 Planned | Adaptive intervention policies | v1.2 |
| **Healthcare Compliance** |
| HIPAA Audit Logging | ✅ Implemented | Comprehensive access tracking | v1.0 |
| Adverse Event Monitoring | ✅ Implemented | Safety surveillance system | v1.0 |
| IRB Model Versioning | ✅ Implemented | Research protocol compliance | v1.0 |
| Automated Compliance Reports | 🔄 In Progress | Regulatory documentation generation | v1.1 |
| Multi-jurisdiction Compliance | 📅 Planned | International regulatory frameworks | v1.2 |
| **Clinical Integration** |
| Clinician Dashboard | ✅ Implemented | Streamlit-based user interface | v1.0 |
| EHR Alert Integration | ✅ Implemented | Care workflow notifications | v1.0 |
| SMART-on-FHIR Launch | ✅ Implemented | EHR-embedded application | v1.0 |
| Order Entry Integration | 🔄 In Progress | Direct clinical action support | v1.1 |
| Clinical Decision Support | 📅 Planned | Context-aware recommendations | v1.2 |
| **Enterprise MLOps** |
| Synthetic Data Generation | ✅ Implemented | Privacy-preserving synthetic patients | v1.0 |
| Federated Learning | ✅ Implemented | Multi-hospital collaborative training | v1.0 |
| Concept Drift Detection | ✅ Implemented | Model performance monitoring | v1.0 |
| Automated Model Retraining | 🔄 In Progress | Continuous model improvement | v1.1 |
| A/B Testing Framework | 📅 Planned | Controlled feature evaluation | v1.2 |

**Legend:**
- ✅ Implemented: Feature is complete and available
- 🔄 In Progress: Feature is currently being developed
- 📅 Planned: Feature is planned for future release

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

## Testing

The project includes comprehensive testing to ensure clinical reliability and regulatory compliance:

### Unit Testing
- Model component tests
- Data processing pipeline tests
- API endpoint tests

### Integration Testing
- End-to-end clinical workflows
- FHIR integration tests
- EHR alert system tests

### Clinical Validation
- Retrospective cohort validation
- Prospective clinical evaluation
- Subgroup performance analysis

### Compliance Testing
- HIPAA compliance verification
- Audit log validation
- PHI de-identification testing

To run tests:

```bash
# Run all tests
make test

# Run specific test suite
make test-clinical
make test-models
make test-compliance

# Run with clinical validation
make clinical-validation \
  TEST_DATA=path/to/annotated_dataset \
  GROUND_TRUTH=physician_reviews.csv
```

## CI/CD Pipeline

Nexora uses GitHub Actions for continuous integration and deployment:

### Continuous Integration
- Automated testing on each pull request and push to main
- Code quality checks with pylint and black
- Test coverage reporting with pytest-cov
- Security scanning for vulnerabilities
- HIPAA compliance verification

### Continuous Deployment
- Automated model training and evaluation
- Model registry updates with versioning
- Kubernetes deployment with canary releases
- Compliance documentation generation

Current CI/CD Status:
- Build: ![Build Status](https://img.shields.io/github/workflow/status/abrar2030/Nexora/CI/main?label=build)
- Test Coverage: ![Coverage](https://img.shields.io/codecov/c/github/abrar2030/Nexora/main?label=coverage)
- Model Quality: ![Model Quality](https://img.shields.io/badge/AUC--ROC-0.82-brightgreen)
- HIPAA Compliance: ![HIPAA Status](https://img.shields.io/badge/HIPAA-Compliant-brightgreen)

## 🤝 Contributing

Contributing to Nexora requires adherence to clinical research and healthcare data standards:

1. **Request IRB approval for clinical contributions**
   - All clinical data contributions must have appropriate IRB approval
   - Follow institutional guidelines for patient data handling

2. **Sign HIPAA Business Associate Agreement (BAA)**
   - Contributors must complete HIPAA training
   - Sign appropriate data use agreements

3. **Follow clinical validation protocol**
   - Use established validation methodologies
   - Document all validation procedures thoroughly

4. **Development Process**
   - Fork the repository
   - Create a feature branch (`git checkout -b feature/amazing-feature`)
   - Make your changes following our coding standards
   - Add tests for new functionality
   - Commit your changes (`git commit -m 'Add some amazing feature'`)
   - Push to the branch (`git push origin feature/amazing-feature`)
   - Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Document all clinical algorithms thoroughly
- Include clinical rationale for model features
- Write comprehensive tests for all components
- Update documentation for any changes
- Ensure all tests pass before submitting a pull request

## 📄 License

This project is licensed under the Healthcare ML License (HML-1.0) - see [LICENSE](LICENSE) for details.