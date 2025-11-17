from datetime import datetime

import pytest
from fastapi import HTTPException


def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_list_models(test_client):
    response = test_client.get("/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) > 0
    assert all("name" in model and "versions" in model for model in data["models"])


def test_predict_endpoint(test_client, synthetic_data):
    test_patient = synthetic_data.iloc[0].to_dict()
    request_data = {
        "model_name": "readmission_risk",
        "model_version": "1.0.0",
        "patient_data": {
            "patient_id": test_patient["patient_id"],
            "demographics": {
                "age": test_patient["age"],
                "gender": test_patient["gender"],
            },
            "clinical_events": [
                {"type": "diagnosis", "code": test_patient["diagnosis"]}
            ],
            "lab_results": [],
            "medications": test_patient["medications"],
        },
    }

    response = test_client.post("/predict", json=request_data)
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert data["model_name"] == "readmission_risk"
    assert "predictions" in data
    assert "explanations" in data
    assert "uncertainty" in data
    assert "timestamp" in data


def test_predict_endpoint_invalid_data(test_client):
    invalid_request = {
        "model_name": "readmission_risk",
        "patient_data": {},  # Missing required fields
    }

    response = test_client.post("/predict", json=invalid_request)
    assert response.status_code == 422  # Validation error


def test_predict_from_fhir(test_client):
    response = test_client.post("/fhir/patient/123/predict?model_name=readmission_risk")
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert data["model_name"] == "readmission_risk"
    assert "predictions" in data
    assert "timestamp" in data


def test_predict_from_fhir_invalid_patient(test_client):
    response = test_client.post(
        "/fhir/patient/invalid/predict?model_name=readmission_risk"
    )
    assert response.status_code == 500  # Error handling


def test_request_logging(test_client):
    # Test that requests are properly logged
    response = test_client.get("/health", headers={"X-Request-ID": "test-123"})
    assert response.status_code == 200
    # Note: In a real test, we would verify the logs here
