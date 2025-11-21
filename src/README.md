# Source Directory

## Overview

The src directory is the core of the Nexora system, containing all the source code for the backend components. This directory implements the clinical data processing pipelines, machine learning models, monitoring systems, and service interfaces that power the Nexora platform's healthcare analytics and prediction capabilities.

## Directory Structure

```
src/
├── compliance/
│   └── phi_audit_logger.py
├── data/
│   └── synthetic_clinical_data.py
├── data_pipeline/
│   ├── clinical_etl.py
│   ├── hipaa_compliance/
│   │   ├── __init__.py
│   │   ├── deidentifier.py
│   │   ├── integration.py
│   │   └── phi_detector.py
│   ├── icd10_encoder.py
│   └── temporal_features.py
├── interfaces/
│   └── clinician_ui.py
├── model_factory/
│   ├── deep_fm.py
│   ├── survival_analysis.py
│   └── transformer_model.py
├── monitoring/
│   ├── adverse_event_reporting.py
│   ├── clinical_metrics.py
│   ├── concept_drift.py
│   └── fairness_metrics.py
├── serving/
│   ├── grpc_server.py
│   └── rest_api.py
├── utils/
│   ├── fhir_connector.py
│   ├── fhir_ops.py
│   └── healthcare_metrics.py
└── validation/
    ├── pipeline_validator.py
    ├── run_tests.py
    └── tests/
        └── test_hipaa_compliance.py
```

## Contents Description

### compliance/

This directory contains components for ensuring regulatory compliance:

- **phi_audit_logger.py**: Implements logging mechanisms for Protected Health Information (PHI) access and usage, creating audit trails required for HIPAA compliance. This module likely records who accessed what data, when, and for what purpose.

### data/

This directory contains data-related utilities:

- **synthetic_clinical_data.py**: Provides functionality for generating synthetic clinical data that mimics real patient data while preserving privacy. This is useful for development, testing, and demonstration purposes without exposing real patient information.

### data_pipeline/

This directory contains the data processing pipeline components:

- **clinical_etl.py**: Implements Extract, Transform, Load (ETL) processes for clinical data, handling the ingestion and preprocessing of healthcare data from various sources.

- **hipaa_compliance/**: A submodule focused on HIPAA compliance in data processing:
  - **deidentifier.py**: Implements algorithms to remove or mask PHI from clinical data.
  - **integration.py**: Provides integration points for the HIPAA compliance tools with the rest of the data pipeline.
  - **phi_detector.py**: Implements detection algorithms for identifying PHI in unstructured text.

- **icd10_encoder.py**: Provides encoding and normalization of ICD-10 diagnosis codes, likely converting them to embeddings or categorical features for machine learning models.

- **temporal_features.py**: Implements extraction of temporal features from clinical time series data, capturing patterns over time in patient records.

### interfaces/

This directory contains user interface components:

- **clinician_ui.py**: Implements backend logic for the clinician-facing user interface, likely providing data and functionality to the web and mobile frontends.

### model_factory/

This directory contains machine learning model implementations:

- **deep_fm.py**: Implements a Deep Factorization Machine model, likely used for patient risk prediction or treatment recommendation.

- **survival_analysis.py**: Implements survival analysis models for time-to-event prediction, such as hospital readmission risk over time.

- **transformer_model.py**: Implements transformer-based models, likely for processing sequential clinical data or medical text.

### monitoring/

This directory contains monitoring and evaluation components:

- **adverse_event_reporting.py**: Implements reporting mechanisms for adverse events detected by the system.

- **clinical_metrics.py**: Implements clinical performance metrics to evaluate the system's impact on healthcare outcomes.

- **concept_drift.py**: Implements detection of concept drift in model inputs and outputs, alerting when the data distribution changes significantly.

- **fairness_metrics.py**: Implements fairness evaluation metrics to ensure the system performs equitably across different patient demographics.

### serving/

This directory contains model serving components:

- **grpc_server.py**: Implements a gRPC server for high-performance model serving.

- **rest_api.py**: Implements a REST API for model serving and data access.

### utils/

This directory contains utility functions:

- **fhir_connector.py**: Provides connectivity to FHIR (Fast Healthcare Interoperability Resources) servers for standardized healthcare data exchange.

- **fhir_ops.py**: Implements operations on FHIR resources, such as querying, filtering, and transformation.

- **healthcare_metrics.py**: Implements healthcare-specific metrics and calculations.

### validation/

This directory contains validation and testing components:

- **pipeline_validator.py**: Implements validation of the data pipeline, ensuring data quality and integrity.

- **run_tests.py**: Script to run validation tests.

- **tests/test_hipaa_compliance.py**: Tests for the HIPAA compliance components.

## Usage

The source code in this directory is used in various ways:

1. **Data Processing**:

   ```python
   from src.data_pipeline.clinical_etl import ClinicalETL

   etl = ClinicalETL(config_path)
   processed_data = etl.process(raw_data)
   ```

2. **Model Training**:

   ```python
   from src.model_factory.deep_fm import DeepFMModel

   model = DeepFMModel(config)
   model.train(train_data, validation_data)
   model.save(model_path)
   ```

3. **Model Serving**:

   ```bash
   # Start the REST API server
   python -m src.serving.rest_api

   # Start the gRPC server
   python -m src.serving.grpc_server
   ```

4. **Validation**:
   ```bash
   # Run validation tests
   python -m src.validation.run_tests
   ```

## Development Guidelines

1. **Code Style**: Follow PEP 8 guidelines for Python code style.
2. **Documentation**: Use docstrings for all modules, classes, and functions.
3. **Testing**: Write unit tests for all components and ensure they pass before committing.
4. **Error Handling**: Implement proper error handling and logging throughout the codebase.
5. **Configuration**: Use configuration files rather than hardcoded values.
6. **Security**: Follow security best practices, especially when handling PHI.
7. **Performance**: Consider performance implications, especially for components in the critical path.

## Dependencies

The source code depends on various Python libraries:

- **Data Processing**: pandas, numpy, scikit-learn
- **Machine Learning**: tensorflow, pytorch, xgboost
- **API**: flask, fastapi, grpcio
- **Healthcare**: fhir.resources, pydicom
- **Monitoring**: prometheus_client, grafana_api

Specific version requirements are defined in the project's requirements.txt file.

## Related Components

- The source code is deployed using configurations in the `deployments/` directory.
- Infrastructure for running the code is defined in the `infrastructure/` directory.
- Exploratory analyses related to the code are in the `notebooks/` directory.
- Tests for the code are in the `tests/` directory.
- Web and mobile frontends consume the APIs defined in `src/serving/`.
