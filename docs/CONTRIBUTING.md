# Contributing to Nexora

Thank you for your interest in contributing to Nexora! This guide will help you get started with development, testing, and submitting contributions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)

---

## Code of Conduct

We are committed to providing a welcoming and inclusive environment. Please be respectful and professional in all interactions.

---

## Getting Started

### Prerequisites

- Python 3.9+
- Git 2.30+
- Node.js 16+ (for frontend development)
- Docker (optional, for container testing)

### Fork and Clone

```bash
# Fork the repository on GitHub first

# Clone your fork
git clone https://github.com/abrar2030/Nexora.git
cd Nexora

# Add upstream remote
git remote add upstream https://github.com/abrar2030/Nexora.git
```

### Setup Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r code/requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # If available

# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### Verify Installation

```bash
# Run tests
make test

# Start API server
python code/run_rest_api.py

# Visit http://localhost:8000/docs
```

---

## Development Workflow

### 1. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code patterns
- Add tests for new features
- Update documentation

### 3. Commit Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add feature: description of what you did"

# Push to your fork
git push origin feature/your-feature-name
```

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Examples**:

```
feat(api): add batch prediction endpoint

fix(model): correct survival analysis calculations

docs(readme): update installation instructions

test(compliance): add PHI detection tests
```

### 4. Submit Pull Request

1. Go to your fork on GitHub
2. Click "Pull Request"
3. Select your branch
4. Fill out PR template
5. Wait for review

---

## Code Style

### Python Code Style

We follow PEP 8 with Black formatting.

**Configuration**:

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39']
```

**Format code**:

```bash
# Format all Python files
make format

# Or manually
black code/ scripts/ tests/
```

**Linting**:

```bash
# Run flake8
make lint

# Or manually
flake8 code/ scripts/ tests/
```

### Python Type Hints

Use type hints for function signatures:

```python
from typing import Dict, List, Optional

def predict(
    patient_data: Dict[str, Any],
    model_name: str,
    model_version: Optional[str] = None
) -> Dict[str, Any]:
    """Generate prediction for patient."""
    pass
```

### Documentation Strings

Use Google-style docstrings:

```python
def calculate_risk_score(features: np.ndarray) -> float:
    """Calculate readmission risk score.

    Args:
        features: Patient feature array of shape (n_features,)

    Returns:
        Risk score between 0.0 and 1.0

    Raises:
        ValueError: If features have invalid shape

    Examples:
        >>> features = np.array([0.5, 0.3, 0.8])
        >>> score = calculate_risk_score(features)
        >>> print(f"Risk: {score:.2f}")
        Risk: 0.75
    """
    if features.ndim != 1:
        raise ValueError("Features must be 1-dimensional")
    return float(model.predict(features))
```

### JavaScript/TypeScript Style

For frontend code:

```bash
# Install dependencies
cd web-frontend
npm install

# Run linting
npm run lint

# Format code
npm run format
```

---

## Testing

### Test Structure

```
tests/
├── unit/                  # Unit tests
├── integration/           # Integration tests
├── clinical_tests/        # Clinical validation
├── model_tests/           # Model performance
├── compliance/            # Compliance tests
└── conftest.py           # Pytest fixtures
```

### Writing Tests

```python
# tests/unit/test_model.py
import pytest
from code.model_factory.model_registry import ModelRegistry

def test_model_registry_get_model():
    """Test model loading from registry."""
    registry = ModelRegistry()
    model = registry.get_model("readmission_v1")
    assert model is not None
    assert hasattr(model, 'predict')

def test_prediction_output_format():
    """Test prediction response format."""
    from code.serving.rest_api import app
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/predict", json={
        "model_name": "readmission_v1",
        "patient_data": {
            "patient_id": "test-123",
            "demographics": {"age": 65, "gender": "M"},
            "clinical_events": []
        }
    })

    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert "risk" in data["predictions"]
    assert 0.0 <= data["predictions"]["risk"] <= 1.0
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/test_model.py -v

# Run with coverage
make test-coverage

# Run specific test category
make test-unit
make test-integration
make test-clinical

# Run single test
pytest tests/unit/test_model.py::test_model_registry_get_model -v
```

### Test Coverage

Maintain >80% test coverage:

```bash
# Generate coverage report
pytest --cov=code --cov-report=html tests/

# View report
open htmlcov/index.html
```

---

## Documentation

### Code Documentation

- Add docstrings to all public functions and classes
- Include type hints
- Provide usage examples

### Updating Docs

When adding features, update:

1. **README.md**: If changing core functionality
2. **docs/API.md**: For new API endpoints
3. **docs/CLI.md**: For new CLI commands
4. **docs/FEATURE_MATRIX.md**: For new features
5. **docs/examples/**: Add practical examples

### Building Documentation

```bash
# Generate docs (if using Sphinx)
make docs

# Preview documentation
cd docs/build/html
python -m http.server 8080
```

---

## Submitting Changes

### Before Submitting

**Checklist**:

- [ ] Code follows style guidelines
- [ ] Tests pass locally (`make test`)
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] No merge conflicts with main branch

### Pull Request Guidelines

**Title Format**:

```
[Type] Brief description

Examples:
[Feature] Add batch prediction API endpoint
[Fix] Correct FHIR date parsing
[Docs] Update installation guide
```

**Description Template**:

```markdown
## Description

Brief description of changes

## Related Issue

Closes #123

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)

(Add screenshots)

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests
2. **Code Review**: Maintainers review code
3. **Feedback**: Address review comments
4. **Approval**: Get approval from maintainers
5. **Merge**: Maintainer merges PR

---

## Development Tips

### Local API Development

```bash
# Start API with auto-reload
uvicorn code.serving.rest_api:app --reload --host 0.0.0.0 --port 8000

# Test with curl
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"model_name": "readmission_v1", "patient_data": {...}}'
```

### Debugging

```python
# Add breakpoints
import pdb; pdb.set_trace()

# Or use ipdb for better debugging
import ipdb; ipdb.set_trace()
```

### Working with Models

```python
# Register a new model
from code.model_factory.model_registry import ModelRegistry

registry = ModelRegistry()
registry.register_model(
    model=my_model,
    name="my_new_model",
    version="1.0.0",
    metadata={"author": "Your Name"}
)
```

### Database Migrations

```bash
# If using Alembic
alembic revision --autogenerate -m "Add new table"
alembic upgrade head
```

---

## Specific Contribution Areas

### Adding New ML Models

1. Extend `BaseModel` in `code/model_factory/base_model.py`
2. Implement `predict()`, `explain()`, `train()`, `evaluate()`
3. Add model config in `config/model_configs/`
4. Register in `model_registry.py`
5. Add tests in `tests/model_tests/`
6. Update documentation

### Adding API Endpoints

1. Add route in `code/serving/rest_api.py`
2. Define Pydantic models for request/response
3. Add audit logging
4. Add tests in `tests/api/`
5. Update `docs/API.md`

### Adding Data Pipeline Components

1. Create module in `code/data_pipeline/`
2. Follow ETL pattern: extract, transform, load
3. Add configuration options
4. Add tests in `tests/data_pipeline/`
5. Update pipeline documentation

---
