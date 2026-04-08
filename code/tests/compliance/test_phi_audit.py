import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from compliance.phi_audit_logger import PHIAuditLogger


@pytest.fixture
def audit_logger(tmp_path):
    return PHIAuditLogger(db_path=str(tmp_path / "test_phi_audit.db"))


def test_phi_audit_logging(audit_logger):
    audit_logger.log_prediction_request(
        patient_id="12345", user_id="test_user", model_used="readmission_risk_v1.0"
    )
    df = audit_logger.get_patient_access_history("12345")
    assert len(df) >= 1
    assert df.iloc[0]["patient"] == "12345"
    assert "timestamp" in df.columns


def test_log_access(audit_logger):
    audit_logger.log_access(
        user_id="clinician_01",
        patient_id="P999",
        resource_type="Patient",
        operation="READ",
        justification="Clinical review",
        model="risk_model_v2",
    )
    df = audit_logger.get_patient_access_history("P999")
    assert len(df) == 1
    assert df.iloc[0]["operation"] == "READ"
    assert df.iloc[0]["user"] == "clinician_01"


def test_generate_report(audit_logger):
    audit_logger.log_prediction_request(
        patient_id="RPT001", user_id="user_a", model_used="model_x"
    )
    audit_logger.log_prediction_request(
        patient_id="RPT002", user_id="user_b", model_used="model_y"
    )
    start = (datetime.utcnow() - timedelta(seconds=10)).isoformat()
    end = (datetime.utcnow() + timedelta(seconds=10)).isoformat()
    df = audit_logger.generate_report(start, end)
    assert len(df) >= 2
    assert "timestamp" in df.columns
    assert "patient" in df.columns


def test_multiple_log_same_patient(audit_logger):
    for i in range(5):
        audit_logger.log_prediction_request(
            patient_id="MULTI_PAT", user_id=f"user_{i}", model_used="model_v1"
        )
    df = audit_logger.get_patient_access_history("MULTI_PAT")
    assert len(df) == 5


def test_patient_history_empty(audit_logger):
    df = audit_logger.get_patient_access_history("NONEXISTENT_PATIENT")
    assert len(df) == 0


def test_audit_logger_close(tmp_path):
    logger = PHIAuditLogger(db_path=str(tmp_path / "close_test.db"))
    logger.log_prediction_request(patient_id="P1", user_id="u1", model_used="m1")
    logger.close()


def test_log_access_all_fields(audit_logger):
    audit_logger.log_access(
        user_id="admin",
        patient_id="FIELD_TEST",
        resource_type="DiagnosticReport",
        operation="WRITE",
        justification="Research",
        model="deepfm_v2",
    )
    df = audit_logger.get_patient_access_history("FIELD_TEST")
    assert len(df) == 1
    row = df.iloc[0]
    assert row["resource"] == "DiagnosticReport"
    assert row["operation"] == "WRITE"
    assert row["reason"] == "Research"
    assert row["model"] == "deepfm_v2"


def test_column_aliases_correct(audit_logger):
    audit_logger.log_access(
        user_id="u1",
        patient_id="COL_TEST",
        resource_type="R",
        operation="READ",
        justification="J",
        model="M",
    )
    df = audit_logger.get_patient_access_history("COL_TEST")
    assert "user" in df.columns
    assert "patient" in df.columns
    assert "resource" in df.columns
    assert "reason" in df.columns
    assert "model" in df.columns


def test_prediction_request_operation_is_read(audit_logger):
    audit_logger.log_prediction_request(
        patient_id="OP_TEST", user_id="u", model_used="m"
    )
    df = audit_logger.get_patient_access_history("OP_TEST")
    assert df.iloc[0]["operation"] == "READ"


def test_report_column_names(audit_logger):
    audit_logger.log_prediction_request(
        patient_id="COL_RPT", user_id="u", model_used="m"
    )
    start = (datetime.utcnow() - timedelta(seconds=5)).isoformat()
    end = (datetime.utcnow() + timedelta(seconds=5)).isoformat()
    df = audit_logger.generate_report(start, end)
    for col in [
        "timestamp",
        "user",
        "patient",
        "resource",
        "operation",
        "reason",
        "model",
    ]:
        assert col in df.columns, f"Missing column: {col}"
