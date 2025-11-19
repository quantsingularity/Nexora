from datetime import datetime, timedelta

import pytest

from src.compliance.deid_rules import DeidentificationRules
from src.compliance.phi_audit_logger import PHIAuditLogger
from src.database.database_connection import DatabaseConnection


@pytest.fixture
def sample_phi_data():
    return {
        "patient_id": "12345",
        "name": "John Doe",
        "dob": "1970-01-01",
        "ssn": "123-45-6789",
        "address": "123 Main St",
        "phone": "555-0123",
        "email": "john.doe@email.com",
        "medical_record_number": "MRN12345",
    }


@pytest.fixture
def deid_rules():
    return DeidentificationRules.from_yaml("config/deid_rules.yaml")


def test_phi_audit_logging(sample_phi_data):
    logger = PHIAuditLogger()

    # Test logging of prediction request
    log_entry = logger.log_prediction_request(
        patient_id=sample_phi_data["patient_id"],
        model_name="readmission_risk",
        timestamp=datetime.now(),
    )

    assert log_entry is not None
    assert "timestamp" in log_entry
    assert "patient_id" in log_entry
    assert "model_name" in log_entry
    assert "access_type" in log_entry

    # Verify log was stored
    with DatabaseConnection("phi_audit_logs") as conn:
        cursor = conn.execute(
            "SELECT * FROM audit_logs WHERE patient_id = ?",
            (sample_phi_data["patient_id"],),
        )
        stored_log = cursor.fetchone()
        assert stored_log is not None
        assert stored_log["access_type"] == "prediction_request"


def test_deidentification_rules(deid_rules, sample_phi_data):
    # Test application of de-identification rules
    deidentified_data = deid_rules.apply(sample_phi_data)

    # Verify PHI elements are removed
    assert "name" not in deidentified_data
    assert "ssn" not in deidentified_data
    assert "address" not in deidentified_data
    assert "phone" not in deidentified_data
    assert "email" not in deidentified_data

    # Verify date shifting
    assert deidentified_data["dob"] != sample_phi_data["dob"]

    # Verify age handling
    if "age" in deidentified_data:
        assert deidentified_data["age"] >= 0
        assert deidentified_data["age"] <= 90


def test_audit_log_retention():
    logger = PHIAuditLogger()

    # Test log retention policy
    retention_period = 365  # days
    old_date = datetime.now() - timedelta(days=retention_period + 1)

    # Create old log entry
    logger.log_prediction_request(
        patient_id="old_patient", model_name="readmission_risk", timestamp=old_date
    )

    # Run retention cleanup
    logger.cleanup_old_logs(retention_period)

    # Verify old logs are removed
    with DatabaseConnection("phi_audit_logs") as conn:
        cursor = conn.execute(
            "SELECT * FROM audit_logs WHERE patient_id = ?", ("old_patient",)
        )
        assert cursor.fetchone() is None


def test_audit_log_aggregation():
    logger = PHIAuditLogger()

    # Test log aggregation
    with DatabaseConnection("phi_audit_logs") as conn:
        stats = conn.execute(
            """
            SELECT
                access_type,
                COUNT(*) as count,
                COUNT(DISTINCT patient_id) as unique_patients
            FROM audit_logs
            GROUP BY access_type
        """
        ).fetchall()

        assert len(stats) > 0
        for stat in stats:
            assert "access_type" in stat
            assert "count" in stat
            assert "unique_patients" in stat
            assert stat["count"] >= stat["unique_patients"]


def test_phi_access_controls():
    logger = PHIAuditLogger()

    # Test access control validation
    with pytest.raises(PermissionError):
        logger.log_prediction_request(
            patient_id="12345",
            model_name="readmission_risk",
            timestamp=datetime.now(),
            user_id="unauthorized_user",
        )


def test_phi_audit_trail():
    logger = PHIAuditLogger()

    # Test complete audit trail
    patient_id = "12345"
    events = [
        ("prediction_request", "readmission_risk"),
        ("data_access", "patient_records"),
        ("model_update", "readmission_risk"),
    ]

    for event_type, resource in events:
        logger.log_event(
            patient_id=patient_id,
            event_type=event_type,
            resource=resource,
            timestamp=datetime.now(),
        )

    # Verify complete trail
    with DatabaseConnection("phi_audit_logs") as conn:
        cursor = conn.execute(
            "SELECT * FROM audit_logs WHERE patient_id = ? ORDER BY timestamp",
            (patient_id,),
        )
        trail = cursor.fetchall()
        assert len(trail) == len(events)
        for i, event in enumerate(trail):
            assert event["event_type"] == events[i][0]
            assert event["resource"] == events[i][1]
