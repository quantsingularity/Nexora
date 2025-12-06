import pytest
from fastapi.testclient import TestClient
from src.data.synthetic_clinical_data import ClinicalDataGenerator
from src.serving.rest_api import app
from src.utils.fhir_ops import FHIRClinicalConnector


@pytest.fixture
def test_client() -> Any:
    return TestClient(app)


@pytest.fixture
def synthetic_data() -> Any:
    generator = ClinicalDataGenerator(seed=42)
    return generator.generate_patient_records(n=100)


@pytest.fixture
def fhir_connector() -> Any:
    return FHIRClinicalConnector(base_url="http://test-fhir-server")


@pytest.fixture
def mock_model_registry() -> Any:

    class MockModelRegistry:

        def get_model(self, name, version=None):

            class MockModel:

                def predict(self, data):
                    return {
                        "risk": 0.75,
                        "top_features": ["age", "previous_admissions", "diabetes"],
                    }

                def explain(self, data):
                    return {"method": "SHAP", "values": [0.3, 0.25, 0.2, 0.15, 0.1]}

            return MockModel()

    return MockModelRegistry()


@pytest.fixture
def mock_audit_logger() -> Any:

    class MockAuditLogger:

        def log_prediction_request(self, patient_id):
            return True

    return MockAuditLogger()
