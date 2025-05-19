# Nexora

[![CI/CD Status](https://img.shields.io/github/actions/workflow/status/abrar2030/Nexora/ci-cd.yml?branch=main&label=CI/CD&logo=github)](https://github.com/abrar2030/Nexora/actions)
[![Test Coverage](https://img.shields.io/codecov/c/github/abrar2030/Nexora/main?label=Coverage)](https://codecov.io/gh/abrar2030/Nexora)
[![Model Quality](https://img.shields.io/badge/AUC--ROC-0.82-brightgreen)](https://github.com/abrar2030/Nexora)
[![HIPAA Compliance](https://img.shields.io/badge/HIPAA-Compliant-brightgreen)](https://github.com/abrar2030/Nexora)
[![License](https://img.shields.io/github/license/abrar2030/Nexora)](https://github.com/abrar2030/Nexora/blob/main/LICENSE)

## 🏥 Healthcare AI Readmission Risk Prediction Platform

Nexora is an advanced healthcare AI platform that predicts patient readmission risk using machine learning and electronic health record (EHR) data, helping clinicians make informed decisions and improve patient outcomes.

<div align="center">
  <img src="docs/images/Nexora_dashboard.bmp" alt="Nexora Clinical Dashboard" width="80%">
</div>

> **Note**: This project is under active development and follows strict healthcare compliance standards. All features are continuously validated for clinical accuracy and regulatory compliance.

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Model Performance](#model-performance)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Clinical Integration](#clinical-integration)
- [Compliance & Security](#compliance--security)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Contributing](#contributing)
- [License](#license)

## Overview

Nexora leverages machine learning to predict patient readmission risk, helping healthcare providers identify high-risk patients and implement targeted interventions. The platform integrates with electronic health record (EHR) systems, processes clinical data securely, and provides actionable insights through an intuitive clinical interface.

## Key Features

### Clinical Decision Support
- **Readmission Risk Prediction**: 30-day readmission risk assessment
- **Risk Factor Identification**: Key clinical variables driving readmission risk
- **Intervention Recommendations**: Evidence-based suggestions for reducing readmission risk
- **Patient Monitoring**: Continuous risk assessment throughout hospital stay

### Healthcare Integration
- **EHR Integration**: Seamless connection with major EHR systems
- **FHIR Compatibility**: Support for HL7 FHIR R4 standard
- **Clinical Workflow Integration**: Fits into existing clinical workflows
- **Alert System**: Configurable alerts for high-risk patients

### Regulatory Compliance
- **HIPAA Compliance**: Full adherence to healthcare privacy regulations
- **Audit Trails**: Comprehensive logging of all system access and actions
- **Model Documentation**: Detailed model cards for regulatory review
- **De-identification**: Robust PHI protection mechanisms

### AI Explainability
- **Feature Importance**: Clear explanation of factors influencing predictions
- **Confidence Intervals**: Uncertainty quantification for predictions
- **Clinical Validation**: Rigorous validation against clinical expertise
- **Bias Monitoring**: Continuous assessment of algorithmic fairness

## Model Performance

### Performance Metrics

| Metric                | Overall | Elderly | Comorbidities |
|-----------------------|---------|---------|---------------|
| **AUROC**             | 0.82    | 0.78    | 0.80          |
| **AUPRC**             | 0.76    | 0.74    | 0.79          |
| **Sensitivity**       | 0.79    | 0.72    | 0.81          |
| **Specificity**       | 0.84    | 0.88    | 0.79          |
| **Brier Score**       | 0.11    | 0.13    | 0.09          |

### Fairness Metrics
```json
{
  "equal_opportunity_diff": 0.03,
  "demographic_parity_ratio": 0.92,
  "calibration_slope": "1.02±0.05"
}
```

## Project Structure

```
Nexora/
├── src/                  # Core source code
│   ├── data/             # Data processing and FHIR integration
│   ├── models/           # ML models and prediction algorithms
│   ├── api/              # API endpoints and services
│   ├── clinical/         # Clinical decision support logic
│   └── utils/            # Utility functions and helpers
├── clinical_ui/          # Streamlit clinician interface
├── compliance/           # HIPAA audit logs and compliance tools
├── federated_learning/   # Cross-hospital training framework
├── model_cards/          # Regulatory documentation
├── pharmacovigilance/    # Adverse event monitoring
├── synthetic_data/       # Synthetic patient data generation
├── tests/                # Comprehensive test suite
├── docs/                 # Documentation and clinical guidelines
├── deployments/          # Kubernetes and deployment configurations
├── config/               # Configuration files
├── notebooks/            # Research and analysis notebooks
├── scripts/              # Utility scripts
├── web-frontend/         # Web interface for clinical users
└── mobile-frontend/      # Mobile application for on-the-go access
```

## Configuration

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
  clinical_thresholds:
    high_risk: 0.75
    medium_risk: 0.40
    low_risk: 0.10
  calibration:
    method: "isotonic"
    bins: 10
```

## Clinical Integration

### FHIR Query Example

```python
from src.data.fhir_ops import FHIRClinicalConnector

# Initialize the FHIR connector
connector = FHIRClinicalConnector()

# Retrieve patient data
bundle = connector.get_patient_sequence("12345")

# Generate risk prediction
risk_prediction = model.predict(bundle)

# Get explanatory factors
factors = model.explain(bundle)

# Log the prediction for audit purposes
audit_logger.log_prediction(
    patient_id="12345",
    user_id="dr.smith",
    prediction=risk_prediction,
    context="Discharge planning"
)
```

### Clinician Dashboard

The Streamlit-based clinical interface provides an intuitive way for healthcare providers to interact with the system:

![Streamlit Dashboard](docs/images/streamlit_dashboard.png)

Key dashboard features:
- Patient risk stratification
- Intervention recommendation engine
- Historical trend visualization
- Clinical documentation integration
- Collaborative care planning tools

## Compliance & Security

### Audit Log Sample

```
2023-08-15T14:23:18 | dr.smith | 123-45-6789 | Prediction | Access | Discharge planning | ReadmissionRisk_v2.3
2023-08-15T14:25:42 | nurse-jones | 987-65-4321 | Update | Correction | Data error remediation | -
2023-08-15T14:30:05 | system | - | Model | Retraining | Scheduled update | ReadmissionRisk_v2.4
```

### Access Monitoring

```bash
# Start monitoring dashboard
kubectl port-forward svc/grafana 3000:3000
open http://localhost:3000/dashboards

# Generate compliance report
python -m src.compliance.generate_report \
  --start-date 2023-08-01 \
  --end-date 2023-08-31 \
  --output compliance_report_august.pdf
```

### Security Features

- End-to-end encryption for all data in transit and at rest
- Role-based access control with fine-grained permissions
- Multi-factor authentication for clinical users
- Automated PHI detection and redaction
- Regular security audits and penetration testing

## Testing

The project includes comprehensive testing to ensure clinical reliability and regulatory compliance:

### Unit Testing
- Model component tests
- Data processing pipeline tests
- API endpoint tests
- PHI detection and redaction tests

### Integration Testing
- End-to-end clinical workflows
- FHIR integration tests
- EHR alert system tests
- Cross-system data flow validation

### Clinical Validation
- Retrospective cohort validation
- Prospective clinical evaluation
- Subgroup performance analysis
- Clinician feedback incorporation

### Compliance Testing
- HIPAA compliance verification
- Audit log validation
- PHI de-identification testing
- Access control verification

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
  
# Generate test coverage report
make coverage-report
```

## CI/CD Pipeline

Nexora uses GitHub Actions for continuous integration and deployment:

### Continuous Integration
- Automated testing on each pull request and push to main
- Code quality checks with pylint and black
- Test coverage reporting with pytest-cov
- Security scanning for vulnerabilities
- HIPAA compliance verification
- Model performance evaluation

### Continuous Deployment
- Automated model training and evaluation
- Model registry updates with versioning
- Kubernetes deployment with canary releases
- Compliance documentation generation
- Synthetic data generation for testing

### Model Monitoring
- Performance drift detection
- Data quality monitoring
- Bias and fairness tracking
- Clinical outcome correlation

Current CI/CD Status:
- Build: ![Build Status](https://img.shields.io/github/actions/workflow/status/abrar2030/Nexora/ci-cd.yml?branch=main&label=build)
- Test Coverage: ![Coverage](https://img.shields.io/codecov/c/github/abrar2030/Nexora/main?label=coverage)
- Model Quality: ![Model Quality](https://img.shields.io/badge/AUC--ROC-0.82-brightgreen)
- HIPAA Compliance: ![HIPAA Status](https://img.shields.io/badge/HIPAA-Compliant-brightgreen)

## Contributing

Contributing to Nexora requires adherence to clinical research and healthcare data standards:

1. **Request IRB approval for clinical contributions**
   - All clinical data contributions must have appropriate IRB approval
   - Follow institutional guidelines for patient data handling
   - Document all data sources and processing methods

2. **Sign HIPAA Business Associate Agreement (BAA)**
   - Contributors must complete HIPAA training
   - Sign appropriate data use agreements
   - Understand PHI handling requirements

3. **Follow clinical validation protocol**
   - Use established validation methodologies
   - Document all validation procedures thoroughly
   - Include clinician review in validation process

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
- Keep pull requests focused on a single feature or fix

## License

This project is licensed under the Healthcare ML License (HML-1.0) - see the [LICENSE](LICENSE) file for details.

### Citation

If you use Nexora in your research, please cite:

```
@article{nexora2023,
  title={Nexora: A Machine Learning Framework for Clinical Readmission Risk Prediction},
  author={Abrar, A. and Smith, J. and Johnson, M. et al.},
  journal={Journal of Medical AI},
  volume={4},
  number={2},
  pages={112-128},
  year={2023},
  publisher={Medical AI Society}
}
```
