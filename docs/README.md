# Nexora Documentation

Welcome to the comprehensive documentation for **Nexora**, an advanced healthcare AI platform that predicts patient readmission risk using machine learning and electronic health record (EHR) data.

## Quick Summary

Nexora helps healthcare providers identify high-risk patients and implement targeted interventions by leveraging ML to predict 30-day readmission risk with clinical-grade validation and full HIPAA compliance.

## 3-Step Quickstart

1. **Install dependencies**: `pip install -r code/requirements.txt`
2. **Start the API**: `python code/run_rest_api.py`
3. **Access the UI**: Navigate to `http://localhost:8000/docs` for interactive API documentation

## Table of Contents

### Core Documentation

- **[Installation Guide](INSTALLATION.md)** - System requirements, installation options, and environment setup
- **[Usage Guide](USAGE.md)** - Common usage patterns, CLI commands, and library usage
- **[Configuration](CONFIGURATION.md)** - All configuration variables, file formats, and settings
- **[API Reference](API.md)** - Complete REST API documentation with examples
- **[CLI Reference](CLI.md)** - Command-line interface reference
- **[Feature Matrix](FEATURE_MATRIX.md)** - Comprehensive feature list with availability

### Advanced Topics

- **[Architecture](ARCHITECTURE.md)** - System architecture, components, and data flow
- **[Examples](examples/)** - Practical examples demonstrating key features
- **[Contributing](CONTRIBUTING.md)** - How to contribute, code style, and development workflow
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

### Additional Resources

- **[Project Overview](#project-overview)**
- **[Key Features](#key-features)**
- **[Model Performance](#model-performance)**
- **[Compliance & Security](#compliance--security)**

---

## Project Overview

Nexora is a comprehensive healthcare ML platform that:

- **Predicts readmission risk** using advanced machine learning models (AUROC 0.82)
- **Integrates with EHR systems** via FHIR R4 standard
- **Ensures HIPAA compliance** with comprehensive audit logging and PHI protection
- **Provides explainable AI** with feature importance and confidence intervals
- **Supports clinical workflows** through intuitive interfaces and alerts

### Technology Stack

| Component           | Technology                                                  |
| ------------------- | ----------------------------------------------------------- |
| **Backend**         | Python 3.9+, FastAPI, Uvicorn                               |
| **ML Frameworks**   | TensorFlow 2.15, PyTorch 2.1, scikit-learn 1.3              |
| **Data Processing** | Pandas, NumPy, Apache Beam                                  |
| **Healthcare**      | FHIR Resources 7.1, HL7 FHIR R4                             |
| **Frontend**        | React (web), React Native (mobile), Streamlit (clinical UI) |
| **Infrastructure**  | Kubernetes, Terraform, Ansible                              |
| **Testing**         | Pytest, Cypress, Detox                                      |

---

## Key Features

### 🏥 Clinical Decision Support

- 30-day readmission risk prediction
- Risk factor identification and explanation
- Evidence-based intervention recommendations
- Continuous patient monitoring throughout hospital stay

### 🔗 Healthcare Integration

- Seamless EHR integration via FHIR R4
- SMART-on-FHIR launch capability
- HL7 message support
- Configurable clinical alerts and notifications

### 🔒 Regulatory Compliance

- Full HIPAA compliance with audit trails
- PHI de-identification and protection
- Regulatory-ready model cards
- Comprehensive access logging

### 🤖 Advanced ML Capabilities

- Multiple model architectures (DeepFM, Transformers, Survival Analysis)
- Fairness-constrained predictions
- Uncertainty quantification
- Real-time concept drift detection

### 📊 Monitoring & Observability

- Clinical metrics dashboard
- Adverse event reporting
- Model performance monitoring
- Fairness and bias detection

---

## Model Performance

### Clinical Validation Metrics

| Metric          | Overall | Elderly (65+) | High Comorbidity |
| --------------- | ------: | ------------: | ---------------: |
| **AUROC**       |    0.82 |          0.78 |             0.80 |
| **AUPRC**       |    0.76 |          0.74 |             0.79 |
| **Sensitivity** |    0.79 |          0.72 |             0.81 |
| **Specificity** |    0.84 |          0.88 |             0.79 |
| **Brier Score** |    0.11 |          0.13 |             0.09 |
| **PPV**         |    0.68 |          0.71 |             0.65 |
| **NPV**         |    0.91 |          0.89 |             0.92 |

### Fairness Metrics

| Metric                       |     Value | Threshold |
| ---------------------------- | --------: | --------: |
| Equal Opportunity Difference |      0.03 |     ≤0.10 |
| Demographic Parity Ratio     |      0.92 |     ≥0.80 |
| Calibration Slope            | 1.02±0.05 | 1.00±0.10 |

---

## Compliance & Security

### HIPAA Compliance Features

- ✅ Audit logging of all PHI access
- ✅ Automatic PHI detection and de-identification
- ✅ Role-based access control (RBAC)
- ✅ Data encryption at rest and in transit
- ✅ Regular security audits
- ✅ Compliance reporting tools

### Security Measures

- Multi-factor authentication (MFA)
- End-to-end encryption (TLS 1.3)
- Automated vulnerability scanning
- Penetration testing
- Regular security updates

---

## Getting Help

- **Documentation Issues**: Open an issue on GitHub
- **Bug Reports**: Use GitHub Issues with `bug` label
- **Feature Requests**: Use GitHub Issues with `enhancement` label
- **Security Concerns**: Email security contact (see SECURITY.md)

---

## License

This project is licensed under the MIT License - see [LICENSE](../LICENSE) file for details.

---

## Quick Links

- [GitHub Repository](https://github.com/quantsingularity/Nexora)
- [API Documentation](API.md)
- [Installation Guide](INSTALLATION.md)
- [Examples](examples/)
