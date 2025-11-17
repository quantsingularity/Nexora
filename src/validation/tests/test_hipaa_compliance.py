"""
Test suite for the HIPAA-compliant readmission prediction pipeline.

This module contains tests for both functionality and compliance
of the readmission prediction pipeline.
"""

import json
import os
import shutil
import tempfile
import unittest
from typing import Any, Dict

import numpy as np
import pandas as pd

from ...data_pipeline.hipaa_compliance.deidentifier import (
    DeidentificationConfig, PHIDeidentifier)
from ...data_pipeline.hipaa_compliance.phi_detector import PHIDetector
from ...validation.pipeline_validator import (AutomatedValidator,
                                              PipelineValidator)


# Mock the ETL class for testing purposes
class MockHIPAACompliantHealthcareETL:
    """A mock ETL class that simulates the de-identification step."""

    def __init__(self, deidentifier):
        self.deidentifier = deidentifier

    def process_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Simulates the ETL process, focusing on de-identification."""
        # In a real scenario, this would involve more steps (parsing, validation, feature gen)
        # For this test, we only focus on the de-identification step

        # Assume the data is passed through the de-identifier
        deidentified_data = self.deidentifier.deidentify_dataframe(
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

        return deidentified_data


class TestHIPAACompliance(unittest.TestCase):
    """Test HIPAA compliance of the de-identification module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample data with PHI
        self.sample_data = pd.DataFrame(
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
                    "789 Pine Rd, Seattle, WA 98101",
                    "321 Elm Blvd, Denver, CO 80202",
                    "654 Maple Dr, Austin, TX 78701",
                ],
                "phone": [
                    "(617) 555-1234",
                    "(312) 555-2345",
                    "(206) 555-3456",
                    "(303) 555-4567",
                    "(512) 555-5678",
                ],
                "email": [
                    "john.s@example.com",
                    "jane.d@example.com",
                    "robert.j@example.com",
                    "emily.w@example.com",
                    "michael.b@example.com",
                ],
                "diagnosis": ["I10", "E11.9", "J44.9", "F32.9", "M54.5"],
                "admission_date": [
                    "2023-01-15",
                    "2023-02-22",
                    "2023-03-08",
                    "2023-04-30",
                    "2023-05-17",
                ],
                "discharge_date": [
                    "2023-01-20",
                    "2023-03-01",
                    "2023-03-15",
                    "2023-05-10",
                    "2023-05-25",
                ],
                "readmission_risk": [0.2, 0.7, 0.4, 0.1, 0.8],
            }
        )

        # Create de-identification config
        self.config = DeidentificationConfig(
            hash_patient_ids=True,
            remove_names=True,
            remove_addresses=True,
            remove_dates_of_birth=True,
            remove_contact_info=True,
            remove_mrns=True,
            remove_ssn=True,
            remove_device_ids=True,
            age_threshold=89,
            shift_dates=True,
        )

        # Create de-identifier
        self.deidentifier = PHIDeidentifier(self.config)

        # Create PHI detector
        self.phi_detector = PHIDetector()

        # Create temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Tear down test fixtures."""
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir)

    def test_phi_detection(self):
        """Test PHI detection functionality."""
        # Detect PHI in sample data
        phi_report = self.phi_detector.generate_phi_report(self.sample_data)

        # Verify PHI detection results
        self.assertGreater(len(phi_report["summary"]["phi_columns"]), 0)
        self.assertIn("name", phi_report["column_details"])
        self.assertIn("ssn", phi_report["column_details"])
        self.assertIn("address", phi_report["column_details"])

    def test_deidentification(self):
        """Test de-identification functionality."""
        # De-identify sample data
        deidentified_data = self.deidentifier.deidentify_dataframe(self.sample_data)

        # Verify de-identification results
        self.assertEqual(len(deidentified_data), len(self.sample_data))

        # Check that PHI has been removed or transformed
        self.assertNotEqual(
            deidentified_data["patient_id"].iloc[0],
            self.sample_data["patient_id"].iloc[0],
        )
        self.assertEqual(deidentified_data["name"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["ssn"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["address"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["phone"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["email"].iloc[0], "[REDACTED]")

        # Check that dates have been shifted
        self.assertNotEqual(
            deidentified_data["admission_date"].iloc[0],
            self.sample_data["admission_date"].iloc[0],
        )
        self.assertNotEqual(
            deidentified_data["discharge_date"].iloc[0],
            self.sample_data["discharge_date"].iloc[0],
        )

        # Check that non-PHI data is preserved
        self.assertEqual(
            deidentified_data["diagnosis"].iloc[0],
            self.sample_data["diagnosis"].iloc[0],
        )
        self.assertEqual(
            deidentified_data["readmission_risk"].iloc[0],
            self.sample_data["readmission_risk"].iloc[0],
        )

    def test_phi_leakage(self):
        """Test for PHI leakage after de-identification."""
        # De-identify sample data
        deidentified_data = self.deidentifier.deidentify_dataframe(self.sample_data)

        # Detect PHI in de-identified data
        phi_report = self.phi_detector.generate_phi_report(deidentified_data)

        # Verify no high-risk PHI remains
        high_risk_columns = [
            col
            for col, details in phi_report["column_details"].items()
            if details["risk_level"] == "high"
        ]

        self.assertEqual(len(high_risk_columns), 0)

    def test_validation_pipeline(self):
        """Test the validation pipeline."""
        # Save sample data to temporary file
        data_path = os.path.join(self.temp_dir, "sample_data.csv")
        self.sample_data.to_csv(data_path, index=False)

        # Create validator
        validator = PipelineValidator(output_dir=self.temp_dir)

        # Validate de-identification
        results = validator.validate_deidentification(self.sample_data, self.config)

        # Verify validation results
        self.assertIn("original_phi_columns", results)
        self.assertIn("remaining_phi_columns", results)
        self.assertIn("phi_types_detected", results)
        self.assertIn("status", results)


class TestFHIRDeidentification(unittest.TestCase):
    """Test de-identification of FHIR resources."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample FHIR bundle
        self.fhir_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Patient",
                        "id": "patient1",
                        "identifier": [
                            {"system": "http://example.org/fhir/mrn", "value": "12345"}
                        ],
                        "name": [
                            {"use": "official", "family": "Smith", "given": ["John"]}
                        ],
                        "telecom": [
                            {"system": "phone", "value": "555-1234", "use": "home"},
                            {"system": "email", "value": "john.smith@example.com"},
                        ],
                        "gender": "male",
                        "birthDate": "1970-01-01",
                        "address": [
                            {
                                "use": "home",
                                "line": ["123 Main St"],
                                "city": "Anytown",
                                "state": "CA",
                                "postalCode": "12345",
                            }
                        ],
                    }
                },
                {
                    "resource": {
                        "resourceType": "Encounter",
                        "id": "encounter1",
                        "status": "finished",
                        "class": {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            "code": "IMP",
                            "display": "inpatient encounter",
                        },
                        "subject": {"reference": "Patient/patient1"},
                        "period": {
                            "start": "2023-01-01T00:00:00Z",
                            "end": "2023-01-05T00:00:00Z",
                        },
                    }
                },
                {
                    "resource": {
                        "resourceType": "Observation",
                        "id": "observation1",
                        "status": "final",
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8867-4",
                                    "display": "Heart rate",
                                }
                            ]
                        },
                        "subject": {"reference": "Patient/patient1"},
                        "effectiveDateTime": "2023-01-02T12:00:00Z",
                        "valueQuantity": {
                            "value": 80,
                            "unit": "beats/minute",
                            "system": "http://unitsofmeasure.org",
                            "code": "/min",
                        },
                    }
                },
            ],
        }

        # Create de-identification config
        self.config = DeidentificationConfig(
            hash_patient_ids=True,
            remove_names=True,
            remove_addresses=True,
            remove_dates_of_birth=True,
            remove_contact_info=True,
            remove_mrns=True,
            remove_ssn=True,
            remove_device_ids=True,
            age_threshold=89,
            shift_dates=True,
        )

        # Create de-identifier
        self.deidentifier = PHIDeidentifier(self.config)

    def test_fhir_deidentification(self):
        """Test de-identification of FHIR bundle."""
        # De-identify FHIR bundle
        deidentified_bundle = self.deidentifier.deidentify_fhir_bundle(self.fhir_bundle)

        # Verify Patient resource de-identification
        patient = None
        for entry in deidentified_bundle["entry"]:
            if entry["resource"]["resourceType"] == "Patient":
                patient = entry["resource"]
                break

        self.assertIsNotNone(patient)

        # Check that PHI has been removed or transformed
        self.assertNotIn("name", patient)
        self.assertNotIn("telecom", patient)
        self.assertNotIn("birthDate", patient)
        self.assertNotIn("address", patient)

        # Check that identifiers are hashed
        original_mrn = self.fhir_bundle["entry"][0]["resource"]["identifier"][0][
            "value"
        ]
        deidentified_mrn = patient["identifier"][0]["value"]
        self.assertNotEqual(original_mrn, deidentified_mrn)

        # Check that dates in other resources are shifted
        encounter = deidentified_bundle["entry"][1]["resource"]
        original_start_date = self.fhir_bundle["entry"][1]["resource"]["period"][
            "start"
        ]
        deidentified_start_date = encounter["period"]["start"]
        self.assertNotEqual(original_start_date, deidentified_start_date)

        # Check that non-PHI data is preserved
        self.assertEqual(patient["gender"], "male")

    def test_pipeline_integration(self):
        """Test integration with the clinical data pipeline."""
        # Create de-identification config
        config = DeidentificationConfig(
            hash_patient_ids=True,
            remove_names=True,
            remove_addresses=True,
            remove_dates_of_birth=True,
            remove_contact_info=True,
            remove_mrns=True,
            remove_ssn=True,
            remove_device_ids=True,
            age_threshold=89,
            shift_dates=True,
        )
        deidentifier = PHIDeidentifier(config)

        # Use the mock ETL class to simulate the pipeline
        etl_mock = MockHIPAACompliantHealthcareETL(deidentifier)
        deidentified_data = etl_mock.process_data(self.sample_data)

        # Verify de-identification results
        self.assertEqual(len(deidentified_data), len(self.sample_data))

        # Check that PHI has been removed or transformed
        self.assertNotEqual(
            deidentified_data["patient_id"].iloc[0],
            self.sample_data["patient_id"].iloc[0],
        )
        self.assertEqual(deidentified_data["name"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["ssn"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["address"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["phone"].iloc[0], "[REDACTED]")
        self.assertEqual(deidentified_data["email"].iloc[0], "[REDACTED]")

        # Check that dates have been shifted
        self.assertNotEqual(
            deidentified_data["admission_date"].iloc[0],
            self.sample_data["admission_date"].iloc[0],
        )
        self.assertNotEqual(
            deidentified_data["discharge_date"].iloc[0],
            self.sample_data["discharge_date"].iloc[0],
        )

        # Verify that non-PHI data is preserved
        self.assertEqual(
            deidentified_data["diagnosis"].iloc[0],
            self.sample_data["diagnosis"].iloc[0],
        )
        self.assertEqual(
            deidentified_data["readmission_risk"].iloc[0],
            self.sample_data["readmission_risk"].iloc[0],
        )


if __name__ == "__main__":
    unittest.main()
