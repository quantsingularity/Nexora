# Developer Guide

This guide provides comprehensive information for developers working on the Hospital Readmission Risk Prediction System. It covers development environment setup, coding standards, testing procedures, and contribution guidelines.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Project Structure](#project-structure)
3. [Coding Standards](#coding-standards)
4. [Development Workflow](#development-workflow)
5. [Testing](#testing)
6. [Continuous Integration](#continuous-integration)
7. [Contribution Guidelines](#contribution-guidelines)
8. [Troubleshooting](#troubleshooting)

## Development Environment Setup

### Prerequisites

- Python 3.10+
- CUDA 11.7+ (for GPU acceleration)
- Docker and Docker Compose
- Kubernetes (for deployment testing)
- Git LFS (for model artifacts)

### Initial Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/abrar2030/Nexora.git
   cd Nexora
   ```

2. Set up a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

5. Initialize data version control:
   ```bash
   dvc init
   dvc pull
   ```

### Configuration

1. Create a local configuration file:

   ```bash
   cp config/config.example.yaml config/config.local.yaml
   ```

2. Update the configuration with your local settings:

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

### Running Locally

1. Start the development server:

   ```bash
   make dev-server
   ```

2. Run the clinician UI:

   ```bash
   make clinician-ui
   ```

3. Access the development interfaces:
   - API: http://localhost:8000/api/v1
   - Clinician UI: http://localhost:8501
   - MLflow: http://localhost:5000

## Project Structure

The project follows a modular structure organized by functionality:

```
readmission-risk/
├── config/                 # Configuration files
├── deployments/            # Deployment configurations
│   ├── docker/             # Docker configurations
│   ├── helm/               # Kubernetes Helm charts
│   └── terraform/          # Infrastructure as Code
├── docs/                   # Documentation
├── frontend/               # User interfaces
│   ├── clinician_ui/       # Streamlit clinician interface
│   └── admin_portal/       # React admin portal
├── infrastructure/         # Infrastructure code
│   ├── terraform/          # Terraform modules
│   └── scripts/            # Infrastructure scripts
├── notebooks/              # Jupyter notebooks for analysis
├── scripts/                # Utility scripts
├── src/                    # Source code
│   ├── compliance/         # Compliance and audit logging
│   ├── data/               # Data handling
│   ├── data_pipeline/      # ETL pipelines
│   ├── interfaces/         # Interface implementations
│   ├── model_factory/      # Model implementations
│   ├── monitoring/         # Monitoring and alerting
│   ├── serving/            # Model serving
│   └── utils/              # Utility functions
└── tests/                  # Test suite
    ├── clinical_tests/     # Clinical validation tests
    └── model_tests/        # Model performance tests
```

### Key Modules

- **src/data_pipeline**: Contains ETL processes for clinical data
- **src/model_factory**: Implements machine learning models
- **src/serving**: Provides API implementations
- **src/monitoring**: Implements monitoring and alerting
- **src/compliance**: Handles regulatory compliance

## Coding Standards

### Python Style Guide

The project follows PEP 8 with the following additions:

1. Line length: 88 characters (Black formatter default)
2. Docstrings: Google style
3. Type hints: Required for all functions

Example:

```python
def calculate_readmission_risk(
    patient_data: Dict[str, Any],
    model_version: str = "latest"
) -> Tuple[float, List[Dict[str, float]]]:
    """Calculate readmission risk for a patient.

    Args:
        patient_data: Dictionary containing patient clinical data
        model_version: Version of the model to use, defaults to "latest"

    Returns:
        Tuple containing:
            - Readmission risk score (0.0 to 1.0)
            - List of risk factors with contribution weights

    Raises:
        ValueError: If patient_data is missing required fields
        ModelNotFoundError: If specified model_version doesn't exist
    """
    # Implementation
```

### Code Organization

1. **Imports**: Organize imports in the following order:
   - Standard library
   - Third-party packages
   - Local modules

2. **Classes**: Follow single responsibility principle
   - One class per file when possible
   - Clear inheritance hierarchies

3. **Functions**: Keep functions focused and small
   - Aim for < 50 lines per function
   - Use descriptive names

### Logging

Use the structured logging framework:

```python
from src.utils.logging import get_logger

logger = get_logger(__name__)

def process_patient_data(patient_id: str) -> None:
    logger.info(
        "Processing patient data",
        extra={"patient_id": patient_id, "operation": "data_processing"}
    )

    try:
        # Processing logic
        pass
    except Exception as e:
        logger.error(
            "Failed to process patient data",
            extra={
                "patient_id": patient_id,
                "error": str(e),
                "operation": "data_processing"
            }
        )
        raise
```

## Development Workflow

### Feature Development

1. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement the feature**:
   - Write tests first (TDD approach)
   - Implement the feature
   - Document the code

3. **Run local tests**:

   ```bash
   make test
   ```

4. **Submit a pull request**:
   - Create a PR against the `develop` branch
   - Fill out the PR template
   - Request reviews from appropriate team members

### Code Review Process

1. Automated checks must pass:
   - Linting
   - Type checking
   - Unit tests
   - Integration tests

2. Code review requirements:
   - At least two approvals required
   - One approval must be from a clinical domain expert for clinical components
   - All comments must be resolved

3. Merge strategy:
   - Squash and merge to keep history clean

### Version Control Practices

1. **Commit messages**: Follow conventional commits

   ```
   feat(model): add transformer-based survival analysis
   fix(api): resolve race condition in batch processing
   docs(readme): update installation instructions
   test(clinical): add tests for ICD-10 encoding
   ```

2. **Branching strategy**:
   - `main`: Production-ready code
   - `develop`: Integration branch for features
   - `feature/*`: New features
   - `fix/*`: Bug fixes
   - `release/*`: Release preparation

## Testing

### Test Types

1. **Unit Tests**: Test individual components in isolation

   ```bash
   pytest tests/unit
   ```

2. **Integration Tests**: Test component interactions

   ```bash
   pytest tests/integration
   ```

3. **Clinical Tests**: Validate clinical correctness

   ```bash
   pytest tests/clinical_tests
   ```

4. **Performance Tests**: Evaluate system performance
   ```bash
   pytest tests/performance
   ```

### Writing Tests

Example unit test:

```python
import pytest
from src.data_pipeline.icd10_encoder import ICD10Encoder

def test_icd10_encoder_initialization():
    encoder = ICD10Encoder()
    assert encoder is not None
    assert hasattr(encoder, 'encode')
    assert hasattr(encoder, 'decode')

def test_icd10_encoder_encode():
    encoder = ICD10Encoder()
    encoded = encoder.encode("I25.10")
    assert isinstance(encoded, int)
    assert encoded > 0

def test_icd10_encoder_decode():
    encoder = ICD10Encoder()
    code = "I25.10"
    encoded = encoder.encode(code)
    decoded = encoder.decode(encoded)
    assert decoded == code

def test_icd10_encoder_invalid_code():
    encoder = ICD10Encoder()
    with pytest.raises(ValueError):
        encoder.encode("INVALID")
```

### Test Data

1. **Synthetic Data**: Use synthetic data for most tests

   ```python
   from src.data.synthetic_clinical_data import generate_synthetic_patients

   def test_with_synthetic_data():
       patients = generate_synthetic_patients(10)
       # Test with synthetic patients
   ```

2. **Test Fixtures**: Use pytest fixtures for common test setups

   ```python
   @pytest.fixture
   def trained_model():
       model = DeepFM()
       model.load_weights("tests/fixtures/model_weights.h5")
       return model

   def test_model_prediction(trained_model):
       prediction = trained_model.predict(test_data)
       assert 0.0 <= prediction <= 1.0
   ```

## Continuous Integration

The project uses GitHub Actions for CI/CD:

### CI Workflow

1. **On Pull Request**:
   - Run linting and type checking
   - Run unit and integration tests
   - Generate test coverage report
   - Build Docker images

2. **On Merge to Develop**:
   - Run all tests including clinical tests
   - Deploy to staging environment
   - Run integration tests against staging

3. **On Release**:
   - Run full test suite
   - Build and tag Docker images
   - Deploy to production
   - Run smoke tests

### CI Configuration

The CI configuration is defined in `.github/workflows/`:

- `pr-checks.yml`: Checks for pull requests
- `staging-deploy.yml`: Deployment to staging
- `production-deploy.yml`: Deployment to production

## Contribution Guidelines

### Getting Started

1. Review the open issues and find one that interests you
2. Comment on the issue to express your interest
3. Fork the repository and create a branch
4. Implement your changes following the development workflow

### Contribution Requirements

1. **Code Quality**:
   - Follow the coding standards
   - Include appropriate tests
   - Maintain or improve test coverage

2. **Documentation**:
   - Update relevant documentation
   - Add docstrings to new code
   - Include examples for new features

3. **Clinical Validation**:
   - For clinical components, include validation against clinical standards
   - Document clinical assumptions

### Pull Request Process

1. Create a pull request against the `develop` branch
2. Fill out the PR template
3. Address review comments
4. Update the PR as needed
5. Once approved, maintainers will merge your PR

## Troubleshooting

### Common Development Issues

#### CUDA/GPU Issues

**Problem**: CUDA version mismatch or GPU not detected

**Solution**:

1. Check CUDA installation:
   ```bash
   nvcc --version
   ```
2. Ensure compatible versions:
   ```bash
   pip install torch==1.12.0+cu113 -f https://download.pytorch.org/whl/torch_stable.html
   ```

#### Data Pipeline Errors

**Problem**: FHIR connection issues

**Solution**:

1. Check FHIR server status:
   ```bash
   curl -I http://localhost:8080/fhir/metadata
   ```
2. Verify credentials in config file
3. Use synthetic data for development:
   ```bash
   make synthetic-data
   ```

#### Model Training Issues

**Problem**: Out of memory during training

**Solution**:

1. Reduce batch size in config
2. Enable gradient accumulation
3. Use mixed precision training:
   ```python
   from src.utils.training import enable_mixed_precision
   enable_mixed_precision()
   ```

### Getting Help

1. Check existing issues on GitHub
2. Join the developer Slack channel
3. Consult the internal knowledge base
4. Contact the core development team
