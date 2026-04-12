"""
ML test conftest.
Adds the project root (parent of `ml/`) to sys.path so that
`ml` and `backend` are importable as top-level packages.
"""

import os
import sys

# Project root = two levels up from ml/tests/conftest.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from ml_core.pipeline.data.synthetic_clinical_data import ClinicalDataGenerator


@pytest.fixture
def synthetic_data():
    generator = ClinicalDataGenerator(seed=42)
    return generator.generate_patient_records(n=100)


@pytest.fixture
def mock_model_registry():
    class MockModelRegistry:
        def get_model(self, name, version=None):
            class MockModel:
                def predict(self, data):
                    return {
                        "risk_score": 0.75,
                        "top_features": ["age", "previous_admissions", "diabetes"],
                    }

                def explain(self, data):
                    return {"method": "SHAP", "values": [0.3, 0.25, 0.2, 0.15, 0.1]}

            return MockModel()

    return MockModelRegistry()


@pytest.fixture
def mock_audit_logger():
    class MockAuditLogger:
        def log_prediction_request(
            self, patient_id, user_id="API_USER", model_used="UNKNOWN"
        ):
            return True

    return MockAuditLogger()


try:
    from backend.serving.rest_api import app
    from fastapi.testclient import TestClient

    @pytest.fixture
    def test_client():
        return TestClient(app)

except ImportError:

    @pytest.fixture
    def test_client():
        pytest.skip("fastapi/httpx not installed")
