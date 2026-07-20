import os
import sys
import uuid

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import pytest

# Skip entire module if fastapi is unavailable
fastapi = pytest.importorskip("fastapi", reason="fastapi not installed")
httpx = pytest.importorskip("httpx", reason="httpx not installed")

from fastapi.testclient import TestClient

from backend.app.core import config as config_module
from backend.serving.rest_api import app


@pytest.fixture(autouse=True)
def isolated_app_db(tmp_path, monkeypatch):
    """Point the app database at a fresh temp file for every test, so
    registering the same email across tests (or across test runs) never
    collides with leftover data from a previous run."""
    monkeypatch.setattr(
        config_module.settings, "APP_DB_PATH", str(tmp_path / "test_app.db")
    )


@pytest.fixture
def test_client():
    return TestClient(app)


def _unique_email():
    return f"clinician-{uuid.uuid4().hex[:10]}@example.com"


def _register(test_client, **overrides):
    payload = {
        "full_name": "Dr. Test Clinician",
        "email": _unique_email(),
        "password": "TestPass123",
        "organization": "Test Hospital",
        "specialty": "Internal Medicine",
    }
    payload.update(overrides)
    response = test_client.post("/auth/register", json=payload)
    return response, payload


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Auth ─────────────────────────────────────────────────────────────────


def test_register_returns_token_and_user(test_client) -> None:
    response, payload = _register(test_client)
    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == payload["email"].lower()
    assert data["user"]["full_name"] == payload["full_name"]
    assert "password" not in data["user"]


def test_register_duplicate_email_conflicts(test_client) -> None:
    _, payload = _register(test_client)
    response = test_client.post("/auth/register", json=payload)
    assert response.status_code == 409


def test_register_rejects_short_password(test_client) -> None:
    response, _ = _register(test_client, password="short")
    assert response.status_code == 422


def test_login_with_correct_credentials(test_client) -> None:
    _, payload = _register(test_client)
    response = test_client.post(
        "/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["user"]["email"] == payload["email"].lower()


def test_login_with_wrong_password_fails(test_client) -> None:
    _, payload = _register(test_client)
    response = test_client.post(
        "/auth/login", json={"email": payload["email"], "password": "WrongPass123"}
    )
    assert response.status_code == 401


def test_get_me_requires_auth(test_client) -> None:
    response = test_client.get("/auth/me")
    assert response.status_code == 401


def test_get_me_with_valid_token(test_client) -> None:
    register_response, payload = _register(test_client)
    token = register_response.json()["access_token"]
    response = test_client.get("/auth/me", headers=_auth_headers(token))
    assert response.status_code == 200
    assert response.json()["email"] == payload["email"].lower()


def test_update_profile(test_client) -> None:
    register_response, _ = _register(test_client)
    token = register_response.json()["access_token"]
    response = test_client.patch(
        "/auth/me",
        json={"full_name": "Dr. Updated Name"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200
    assert response.json()["full_name"] == "Dr. Updated Name"


def test_change_password_then_login_with_new_password(test_client) -> None:
    register_response, payload = _register(test_client)
    token = register_response.json()["access_token"]
    response = test_client.post(
        "/auth/change-password",
        json={"current_password": payload["password"], "new_password": "NewPass456"},
        headers=_auth_headers(token),
    )
    assert response.status_code == 200

    login_response = test_client.post(
        "/auth/login", json={"email": payload["email"], "password": "NewPass456"}
    )
    assert login_response.status_code == 200


# ── Patients ─────────────────────────────────────────────────────────────


def test_patients_endpoints_require_auth(test_client) -> None:
    assert test_client.get("/patients").status_code == 401


def test_list_patients_is_seeded(test_client) -> None:
    register_response, _ = _register(test_client)
    token = register_response.json()["access_token"]
    response = test_client.get("/patients", headers=_auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["patients"]) > 0
    assert "riskScore" in data["patients"][0]


def test_create_and_fetch_patient(test_client) -> None:
    register_response, _ = _register(test_client)
    token = register_response.json()["access_token"]
    headers = _auth_headers(token)

    create_response = test_client.post(
        "/patients",
        json={
            "name": "Integration Test Patient",
            "age": 60,
            "gender": "Female",
            "diagnosis": "Hypertension",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["name"] == "Integration Test Patient"
    assert 0 <= created["riskScore"] <= 1
    assert created["riskBand"] in ("low", "medium", "high")

    detail_response = test_client.get(f"/patients/{created['id']}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == created["id"]
    assert isinstance(detail_response.json()["riskFactors"], list)


def test_recompute_risk(test_client) -> None:
    register_response, _ = _register(test_client)
    token = register_response.json()["access_token"]
    headers = _auth_headers(token)

    create_response = test_client.post(
        "/patients", json={"name": "Risk Recompute Patient"}, headers=headers
    )
    patient_id = create_response.json()["id"]

    response = test_client.post(
        f"/patients/{patient_id}/recompute-risk", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == patient_id


def test_delete_patient(test_client) -> None:
    register_response, _ = _register(test_client)
    token = register_response.json()["access_token"]
    headers = _auth_headers(token)

    create_response = test_client.post(
        "/patients", json={"name": "To Be Deleted"}, headers=headers
    )
    patient_id = create_response.json()["id"]

    delete_response = test_client.delete(f"/patients/{patient_id}", headers=headers)
    assert delete_response.status_code == 200

    get_response = test_client.get(f"/patients/{patient_id}", headers=headers)
    assert get_response.status_code == 404


# ── Dashboard ────────────────────────────────────────────────────────────


def test_dashboard_summary_requires_auth(test_client) -> None:
    assert test_client.get("/dashboard/summary").status_code == 401


def test_dashboard_summary_shape(test_client) -> None:
    register_response, _ = _register(test_client)
    token = register_response.json()["access_token"]
    response = test_client.get("/dashboard/summary", headers=_auth_headers(token))
    assert response.status_code == 200
    data = response.json()
    for key in (
        "stats",
        "patientRiskDistribution",
        "admissionsData",
        "modelPerformance",
    ):
        assert key in data
    assert data["stats"]["activePatients"] > 0


# ── Notifications ────────────────────────────────────────────────────────


def test_notifications_require_auth(test_client) -> None:
    assert test_client.get("/notifications").status_code == 401


def test_list_and_mark_read_notifications(test_client) -> None:
    register_response, _ = _register(test_client)
    token = register_response.json()["access_token"]
    headers = _auth_headers(token)

    response = test_client.get("/notifications", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "notifications" in data
    assert "unread" in data

    if data["notifications"]:
        notif_id = data["notifications"][0]["id"]
        mark_response = test_client.patch(
            f"/notifications/{notif_id}/read", headers=headers
        )
        assert mark_response.status_code == 200
