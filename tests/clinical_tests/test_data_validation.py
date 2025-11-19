import os
import sys
import unittest
from datetime import timedelta

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.data_pipeline.data_validation import DataValidator


class TestDataValidation(unittest.TestCase):
    """Test suite for data validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a sample dataset for testing
        self.sample_data = pd.DataFrame(
            {
                "patient_id": ["P001", "P002", "P003", "P004", "P005"],
                "age": [45, 67, 32, 78, 50],
                "gender": ["M", "F", "M", "F", "M"],
                "diagnosis_code": ["I25.10", "E11.9", "J44.9", "I10", "K21.0"],
                "admission_date": [
                    "2023-01-15",
                    "2023-02-20",
                    "2023-03-10",
                    "2023-04-05",
                    "2023-05-12",
                ],
                "discharge_date": [
                    "2023-01-20",
                    "2023-03-01",
                    "2023-03-15",
                    "2023-04-15",
                    "2023-05-18",
                ],
                "lab_value": [120.5, 95.2, 110.8, 140.3, 105.7],
                "medication_count": [3, 5, 2, 7, 4],
                "readmission": [0, 1, 0, 1, 0],
                "mortality": [0, 0, 0, 1, 0],
            }
        )

        # Convert date strings to datetime objects
        self.sample_data["admission_date"] = pd.to_datetime(
            self.sample_data["admission_date"]
        )
        self.sample_data["discharge_date"] = pd.to_datetime(
            self.sample_data["discharge_date"]
        )

        # Create a validator instance
        self.validator = DataValidator()

        # Define schema for validation
        self.schema = {
            "patient_id": {"type": "string", "required": True, "unique": True},
            "age": {"type": "integer", "required": True, "min": 0, "max": 120},
            "gender": {
                "type": "category",
                "required": True,
                "categories": ["M", "F", "O"],
            },
            "diagnosis_code": {
                "type": "string",
                "required": True,
                "pattern": r"^[A-Z][0-9]{2}(\.[0-9]{1,2})?$",
            },
            "admission_date": {"type": "datetime", "required": True},
            "discharge_date": {"type": "datetime", "required": True},
            "lab_value": {"type": "float", "required": False, "min": 0},
            "medication_count": {"type": "integer", "required": False, "min": 0},
            "readmission": {"type": "boolean", "required": True},
            "mortality": {"type": "boolean", "required": True},
        }

        # Define relationships for validation
        self.relationships = [
            {
                "type": "temporal",
                "first": "admission_date",
                "second": "discharge_date",
                "relation": "<=",
            },
            {
                "type": "logical",
                "condition": "mortality == 1",
                "implication": "readmission == 0",
            },
        ]

    def test_validate_schema(self):
        """Test schema validation functionality."""
        # Test valid data
        result = self.validator.validate_schema(self.sample_data, self.schema)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

        # Test invalid data - wrong data type
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "age"] = "forty-five"  # String instead of integer
        result = self.validator.validate_schema(invalid_data, self.schema)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

        # Test invalid data - out of range
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "age"] = 150  # Above maximum age
        result = self.validator.validate_schema(invalid_data, self.schema)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

        # Test invalid data - invalid category
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "gender"] = "X"  # Not in allowed categories
        result = self.validator.validate_schema(invalid_data, self.schema)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

        # Test invalid data - pattern mismatch
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "diagnosis_code"] = "12345"  # Doesn't match ICD-10 pattern
        result = self.validator.validate_schema(invalid_data, self.schema)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

    def test_validate_relationships(self):
        """Test relationship validation functionality."""
        # Test valid data
        result = self.validator.validate_relationships(
            self.sample_data, self.relationships
        )
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

        # Test invalid data - temporal relationship violation
        invalid_data = self.sample_data.copy()
        invalid_data.loc[0, "discharge_date"] = invalid_data.loc[
            0, "admission_date"
        ] - timedelta(days=1)
        result = self.validator.validate_relationships(invalid_data, self.relationships)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

        # Test invalid data - logical relationship violation
        invalid_data = self.sample_data.copy()
        invalid_data.loc[3, "mortality"] = 1
        invalid_data.loc[3, "readmission"] = (
            1  # Logical contradiction: dead patients can't be readmitted
        )
        result = self.validator.validate_relationships(invalid_data, self.relationships)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)

    def test_detect_outliers(self):
        """Test outlier detection functionality."""
        # Test with default settings
        result = self.validator.detect_outliers(
            self.sample_data, ["age", "lab_value", "medication_count"]
        )
        self.assertIsInstance(result, dict)
        self.assertTrue("outliers" in result)
        self.assertTrue("age" in result["outliers"])
        self.assertTrue("lab_value" in result["outliers"])
        self.assertTrue("medication_count" in result["outliers"])

        # Test with custom z-score threshold
        result = self.validator.detect_outliers(
            self.sample_data,
            ["age", "lab_value", "medication_count"],
            method="z-score",
            threshold=3.0,
        )
        self.assertIsInstance(result, dict)

        # Test with IQR method
        result = self.validator.detect_outliers(
            self.sample_data,
            ["age", "lab_value", "medication_count"],
            method="iqr",
            threshold=1.5,
        )
        self.assertIsInstance(result, dict)

    def test_check_missing_values(self):
        """Test missing value detection functionality."""
        # Create data with missing values
        data_with_missing = self.sample_data.copy()
        data_with_missing.loc[0, "lab_value"] = np.nan
        data_with_missing.loc[1, "medication_count"] = np.nan

        # Test missing value detection
        result = self.validator.check_missing_values(data_with_missing)
        self.assertIsInstance(result, dict)
        self.assertTrue("missing_counts" in result)
        self.assertTrue("missing_percentage" in result)
        self.assertEqual(result["missing_counts"]["lab_value"], 1)
        self.assertEqual(result["missing_counts"]["medication_count"], 1)

    def test_validate_icd10_codes(self):
        """Test ICD-10 code validation functionality."""
        # Test valid ICD-10 codes
        valid_codes = pd.Series(
            [
                "A01.0",
                "B20",
                "C34.90",
                "D61.810",
                "E11.9",
                "I25.10",
                "J44.9",
                "K21.0",
                "Z99.2",
            ]
        )
        result = self.validator.validate_icd10_codes(valid_codes)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["invalid_codes"]), 0)

        # Test invalid ICD-10 codes
        invalid_codes = pd.Series(["A01.0", "XYZ", "123.45", "B20.ABC", "I25.999"])
        result = self.validator.validate_icd10_codes(invalid_codes)
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["invalid_codes"]), 4)

    def test_validate_date_ranges(self):
        """Test date range validation functionality."""
        # Test valid date ranges
        result = self.validator.validate_date_ranges(
            self.sample_data,
            "admission_date",
            min_date="2023-01-01",
            max_date="2023-12-31",
        )
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["out_of_range"]), 0)

        # Test invalid date ranges
        result = self.validator.validate_date_ranges(
            self.sample_data,
            "admission_date",
            min_date="2023-03-01",
            max_date="2023-04-30",
        )
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["out_of_range"]), 0)

    def test_check_duplicates(self):
        """Test duplicate detection functionality."""
        # Test data without duplicates
        result = self.validator.check_duplicates(self.sample_data, ["patient_id"])
        self.assertFalse(result["has_duplicates"])
        self.assertEqual(len(result["duplicate_indices"]), 0)

        # Test data with duplicates
        data_with_duplicates = pd.concat([self.sample_data, self.sample_data.iloc[0:2]])
        result = self.validator.check_duplicates(data_with_duplicates, ["patient_id"])
        self.assertTrue(result["has_duplicates"])
        self.assertEqual(len(result["duplicate_indices"]), 2)

    def test_validate_consistency(self):
        """Test data consistency validation functionality."""
        # Define consistency rules
        consistency_rules = [
            {
                "condition": "age >= 65",
                "expected": "medication_count >= 3",
                "name": "elderly_medication",
            },
            {
                "condition": "mortality == 1",
                "expected": "age > 70",
                "name": "mortality_age_correlation",
            },
        ]

        # Test valid data
        result = self.validator.validate_consistency(
            self.sample_data, consistency_rules
        )

        # We expect some violations in our sample data
        self.assertIsInstance(result, dict)
        self.assertTrue("rule_results" in result)

        # Create data that satisfies all rules
        consistent_data = self.sample_data.copy()
        consistent_data.loc[consistent_data["age"] >= 65, "medication_count"] = 5
        consistent_data.loc[consistent_data["mortality"] == 1, "age"] = 80

        result = self.validator.validate_consistency(consistent_data, consistency_rules)
        self.assertTrue(all(r["valid"] for r in result["rule_results"].values()))

    def test_generate_validation_report(self):
        """Test validation report generation functionality."""
        # Run a full validation
        report = self.validator.generate_validation_report(
            self.sample_data,
            schema=self.schema,
            relationships=self.relationships,
            outlier_columns=["age", "lab_value", "medication_count"],
            consistency_rules=[
                {
                    "condition": "age >= 65",
                    "expected": "medication_count >= 3",
                    "name": "elderly_medication",
                },
                {
                    "condition": "mortality == 1",
                    "expected": "age > 70",
                    "name": "mortality_age_correlation",
                },
            ],
        )

        # Check report structure
        self.assertIsInstance(report, dict)
        self.assertTrue("schema_validation" in report)
        self.assertTrue("relationship_validation" in report)
        self.assertTrue("missing_values" in report)
        self.assertTrue("outliers" in report)
        self.assertTrue("duplicates" in report)
        self.assertTrue("consistency" in report)
        self.assertTrue("summary" in report)

        # Check summary
        self.assertTrue("valid" in report["summary"])
        self.assertTrue("error_count" in report["summary"])
        self.assertTrue("warning_count" in report["summary"])

    def test_integration_with_fhir(self):
        """Test integration with FHIR connector."""
        # This is a mock test since we don't have a real FHIR server
        # In a real environment, we would use a test FHIR server

        # Create a mock FHIR dataset
        fhir_data = {
            "Patient": [
                {
                    "resourceType": "Patient",
                    "id": "P001",
                    "gender": "male",
                    "birthDate": "1978-01-15",
                },
                {
                    "resourceType": "Patient",
                    "id": "P002",
                    "gender": "female",
                    "birthDate": "1956-05-22",
                },
            ],
            "Observation": [
                {
                    "resourceType": "Observation",
                    "id": "O001",
                    "subject": {"reference": "Patient/P001"},
                    "code": {
                        "coding": [
                            {
                                "code": "8480-6",
                                "system": "http://loinc.org",
                                "display": "Systolic blood pressure",
                            }
                        ]
                    },
                    "valueQuantity": {"value": 120, "unit": "mmHg"},
                }
            ],
        }

        # Mock the FHIR connector
        class MockFHIRConnector:
            def patients_to_dataframe(self, patients):
                return pd.DataFrame(
                    {
                        "patient_id": ["P001", "P002"],
                        "gender": ["M", "F"],
                        "birth_date": ["1978-01-15", "1956-05-22"],
                    }
                )

            def observations_to_dataframe(self, observations):
                return pd.DataFrame(
                    {
                        "observation_id": ["O001"],
                        "patient_id": ["P001"],
                        "code": ["8480-6"],
                        "value": [120],
                        "unit": ["mmHg"],
                    }
                )

        mock_connector = MockFHIRConnector()

        # Convert mock FHIR data to DataFrames
        patients_df = mock_connector.patients_to_dataframe(fhir_data["Patient"])
        observations_df = mock_connector.observations_to_dataframe(
            fhir_data["Observation"]
        )

        # Validate the converted data
        patient_schema = {
            "patient_id": {"type": "string", "required": True, "unique": True},
            "gender": {
                "type": "category",
                "required": True,
                "categories": ["M", "F", "O"],
            },
            "birth_date": {"type": "string", "required": True},
        }

        result = self.validator.validate_schema(patients_df, patient_schema)
        self.assertTrue(result["valid"])


if __name__ == "__main__":
    unittest.main()
