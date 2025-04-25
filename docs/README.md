# Hospital Readmission Risk Prediction System Documentation

Welcome to the comprehensive documentation for the Hospital Readmission Risk Prediction System. This documentation provides detailed information about the system architecture, components, installation, usage, and deployment.

## Documentation Structure

- **[Architecture](./architecture/README.md)**: System architecture, component interactions, and data flow diagrams
- **[API Documentation](./api/README.md)**: REST and gRPC API specifications and usage examples
- **[User Guide](./user_guide/README.md)**: End-user instructions for clinicians and healthcare providers
- **[Developer Guide](./developer_guide/README.md)**: Setup, development workflow, and contribution guidelines
- **[Deployment Guide](./deployment/README.md)**: Installation and deployment instructions for various environments
- **[Model Documentation](./model_documentation/README.md)**: Model cards, performance metrics, and validation reports
- **[Infrastructure](./infrastructure/README.md)**: Infrastructure setup, Terraform modules, and cloud deployment
- **[Tutorials](./tutorials/README.md)**: Step-by-step guides for common tasks and workflows
- **[Changelog](./changelog/README.md)**: Version history and release notes

## Project Overview

The Hospital Readmission Risk Prediction System is an end-to-end MLOps system designed to predict 30-day hospital readmission risk with clinical-grade validation and regulatory compliance. The system integrates with healthcare data standards (FHIR/HL7), provides advanced machine learning models, ensures healthcare compliance, offers clinical integration capabilities, and implements enterprise MLOps practices.

## Key Features

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

## Getting Started

For quick setup and usage instructions, refer to the [User Guide](./user_guide/README.md) and [Deployment Guide](./deployment/README.md).

## License

This project is licensed under the Healthcare ML License (HML-1.0) - see [LICENSE](../LICENSE) for details.
