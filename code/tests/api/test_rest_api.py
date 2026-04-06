import os
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


def test_health_check(test_client: Any) -> None:
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_list_models(test_client: Any) -> None:
    response = test_client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], dict)
    assert len(data["models"]) > 0


def test_predict_endpoint(test_client: Any) -> None:
    request_data = {
        "model_name": "transformer_model",
        "model_version": "latest",
        "patient_data": {
            "patient_id": "PAT001",
            "demographics": {"gender": "male", "birthDate": "1970-01-01"},
            "clinical_events": [
                {"type": "diagnosis", "code": "I10", "date": "2023-01-01"}
            ],
            "lab_results": [],
            "medications": [],
        },
    }
    response = test_client.post("/predict", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["model_name"] == "transformer_model"
    assert "predictions" in data
    assert "explanations" in data
    assert "uncertainty" in data
    assert "timestamp" in data


def test_predict_endpoint_invalid_data(test_client: Any) -> None:
    invalid_request = {"model_name": "transformer_model", "patient_data": {}}
    response = test_client.post("/predict", json=invalid_request)
    assert response.status_code == 422


def test_predict_endpoint_unknown_model(test_client: Any) -> None:
    request_data = {
        "model_name": "nonexistent_model_xyz",
        "patient_data": {
            "patient_id": "PAT001",
            "demographics": {"gender": "male"},
            "clinical_events": [],
        },
    }
    response = test_client.post("/predict", json=request_data)
    assert response.status_code == 500


def test_predict_from_fhir_unreachable(test_client: Any) -> None:
    response = test_client.post(
        "/fhir/patient/123/predict?model_name=transformer_model"
    )
    assert response.status_code == 500


def test_predict_from_fhir_invalid_patient(test_client: Any) -> None:
    response = test_client.post(
        "/fhir/patient/invalid_patient/predict?model_name=transformer_model"
    )
    assert response.status_code == 500


def test_request_logging(test_client: Any) -> None:
    response = test_client.get("/health", headers={"X-Request-ID": "test-123"})
    assert response.status_code == 200


def test_get_metrics(test_client: Any) -> None:
    response = test_client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "cohort_metrics" in data


def test_audit_patient_history(test_client: Any) -> None:
    request_data = {
        "model_name": "transformer_model",
        "patient_data": {
            "patient_id": "AUDIT_PAT_001",
            "demographics": {"gender": "female"},
            "clinical_events": [],
        },
    }
    test_client.post("/predict", json=request_data)
    response = test_client.get("/audit/patient/AUDIT_PAT_001")
    assert response.status_code == 200
    data = response.json()
    assert "patient_id" in data
    assert "access_history" in data
    assert isinstance(data["access_history"], list)
