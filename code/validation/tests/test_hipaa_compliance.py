"""
Test suite for the HIPAA-compliant readmission prediction pipeline.

This module contains tests for both functionality and compliance
of the readmission prediction pipeline.
"""

import os
import sys
import unittest
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pandas as pd
import pytest
from data_pipeline.hipaa_compliance.deidentifier import (
    DeidentificationConfig,
    PHIDeidentifier,
)
from data_pipeline.hipaa_compliance.phi_detector import PHIDetector


class MockHIPAACompliantHealthcareETL:
    """A mock ETL class that simulates the de-identification step."""

    def __init__(self, deidentifier: Any) -> None:
        self.deidentifier = deidentifier

    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Simulates the ETL process, focusing on de-identification."""
        return self.deidentifier.deidentify_dataframe(
            data,
            patient_id_col="patient_id",
            phi_cols=[
                "name",
                "dob",
                "ssn",
                "address",
                "phone",
                "email",
                "admission_date",
                "discharge_date",
            ],
        )


@pytest.fixture
def sample_data():
    return pd.DataFrame(
        {
            "patient_id": ["P001", "P002", "P003", "P004", "P005"],
            "name": [
                "John Smith",
                "Jane Doe",
                "Robert Johnson",
                "Emily Wilson",
                "Michael Brown",
            ],
            "dob": [
                "1980-05-15",
                "1975-10-22",
                "1990-03-08",
                "1988-12-30",
                "1965-07-17",
            ],
            "ssn": [
                "123-45-6789",
                "234-56-7890",
                "345-67-8901",
                "456-78-9012",
                "567-89-0123",
            ],
            "address": [
                "123 Main St, Boston, MA 02108",
                "456 Oak Ave, Chicago, IL 60601",
                "789 Pine Rd, Houston, TX 77001",
                "321 Elm St, Phoenix, AZ 85001",
                "654 Maple Dr, Philadelphia, PA 19101",
            ],
            "phone": [
                "617-555-0101",
                "312-555-0102",
                "713-555-0103",
                "602-555-0104",
                "215-555-0105",
            ],
            "email": [
                "john@email.com",
                "jane@email.com",
                "rob@email.com",
                "emily@email.com",
                "mike@email.com",
            ],
            "admission_date": [
                "2024-01-15",
                "2024-02-20",
                "2024-03-10",
                "2024-04-05",
                "2024-05-12",
            ],
            "discharge_date": [
                "2024-01-20",
                "2024-02-25",
                "2024-03-15",
                "2024-04-10",
                "2024-05-17",
            ],
            "diagnosis": ["I10", "E11", "J44", "I50", "N18"],
            "readmission_risk": [0.3, 0.7, 0.5, 0.8, 0.2],
        }
    )


@pytest.fixture
def deidentifier():
    return PHIDeidentifier(config=DeidentificationConfig())


def test_deidentification_redacts_phi(sample_data, deidentifier):
    result = deidentifier.deidentify_dataframe(
        sample_data,
        patient_id_col="patient_id",
        phi_cols=["name", "dob", "ssn", "address", "phone", "email"],
    )
    # Columns are kept but values are redacted/shifted
    assert "patient_id" in result.columns
    assert "diagnosis" in result.columns
    # Name values should be redacted
    assert (result["name"] == "[REDACTED]").all()
    # Address values should be redacted
    assert (result["address"] == "[REDACTED]").all()
    # SSN values should be redacted
    assert (result["ssn"] == "[REDACTED]").all()


def test_deidentification_preserves_non_phi(sample_data, deidentifier):
    result = deidentifier.deidentify_dataframe(
        sample_data,
        patient_id_col="patient_id",
        phi_cols=["name", "ssn", "address", "phone", "email"],
    )
    assert "diagnosis" in result.columns
    assert "readmission_risk" in result.columns
    assert list(result["diagnosis"]) == list(sample_data["diagnosis"])


def test_phi_detector_finds_phi(sample_data):
    detector = PHIDetector()
    report = detector.generate_phi_report(sample_data)
    assert "summary" in report
    assert report["summary"]["phi_columns"] > 0


def test_phi_detector_report_structure(sample_data):
    detector = PHIDetector()
    report = detector.generate_phi_report(sample_data)
    assert "summary" in report
    assert "column_details" in report
    assert "total_columns" in report["summary"]
    assert "phi_columns" in report["summary"]
    assert "high_risk_columns" in report["summary"]


def test_mock_etl_deidentifies(sample_data, deidentifier):
    etl = MockHIPAACompliantHealthcareETL(deidentifier)
    result = etl.process_data(sample_data)
    assert "diagnosis" in result.columns
    assert (result["name"] == "[REDACTED]").all()
    assert (result["ssn"] == "[REDACTED]").all()


def test_patient_id_is_hashed(sample_data):
    config = DeidentificationConfig(hash_patient_ids=True)
    deid = PHIDeidentifier(config=config)
    result = deid.deidentify_dataframe(
        sample_data,
        patient_id_col="patient_id",
        phi_cols=[],
    )
    # Patient IDs should be hashed (not the original values)
    original_ids = set(sample_data["patient_id"].tolist())
    result_ids = set(result["patient_id"].tolist())
    assert original_ids != result_ids
    # Hash values should be longer than original IDs
    assert all(len(pid) > 10 for pid in result_ids)


def test_dates_are_shifted(sample_data):
    config = DeidentificationConfig(shift_dates=True)
    deid = PHIDeidentifier(config=config)
    result = deid.deidentify_dataframe(
        sample_data,
        patient_id_col="patient_id",
        phi_cols=["admission_date", "discharge_date"],
    )
    # After shifting, dates should differ from originals
    original_admission = set(sample_data["admission_date"].tolist())
    result_admission = set(result["admission_date"].astype(str).tolist())
    assert original_admission != result_admission


def test_fhir_bundle_deidentification(deidentifier):
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-001",
                    "name": [{"family": "Smith", "given": ["John"]}],
                    "birthDate": "1970-01-25",
                    "address": [{"line": ["123 Main St"], "city": "Boston"}],
                    "telecom": [{"system": "phone", "value": "555-1234"}],
                }
            }
        ],
    }
    result = deidentifier.deidentify_fhir_bundle(bundle)
    patient = result["entry"][0]["resource"]
    assert patient["name"] == [{"text": "[REDACTED]"}]
    assert patient["address"] == [{"text": "[REDACTED]"}]
    assert patient["telecom"] == []


def test_phi_columns_identified_by_name(sample_data):
    detector = PHIDetector()
    phi_cols = detector.identify_phi_columns(sample_data, threshold=0.0)
    # Should identify columns with PHI-like names
    assert len(phi_cols) > 0


def test_deidentification_config_defaults():
    config = DeidentificationConfig()
    assert config.hash_patient_ids is True
    assert config.remove_names is True
    assert config.remove_addresses is True
    assert config.remove_ssn is True
    assert config.shift_dates is True
    assert config.age_threshold == 89


if __name__ == "__main__":
    unittest.main()
