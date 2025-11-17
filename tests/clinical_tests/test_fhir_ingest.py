import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from src.data_pipeline.data_validation import DataValidator
from src.utils.fhir_connector import FHIRConnector


class TestFHIRIngest(unittest.TestCase):
    """Test suite for FHIR data ingestion functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a mock FHIR server configuration
        self.mock_config = {
            "base_url": "http://test-fhir-server.example.com/fhir",
            "auth_type": "none",
            "verify_ssl": False,
            "timeout": 10,
            "max_retries": 2,
        }

        # Create sample FHIR resources for testing
        self.sample_patient = {
            "resourceType": "Patient",
            "id": "patient-001",
            "meta": {"versionId": "1", "lastUpdated": "2023-05-15T10:15:00Z"},
            "identifier": [
                {
                    "system": "http://hospital.example.org/identifiers/patients",
                    "value": "P123456",
                },
                {"system": "http://hl7.org/fhir/sid/us-ssn", "value": "123-45-6789"},
            ],
            "name": [
                {"use": "official", "family": "Smith", "given": ["John", "Edward"]}
            ],
            "gender": "male",
            "birthDate": "1970-01-25",
            "address": [
                {
                    "use": "home",
                    "line": ["123 Main St"],
                    "city": "Anytown",
                    "state": "CA",
                    "postalCode": "12345",
                    "country": "USA",
                }
            ],
            "telecom": [
                {"system": "phone", "value": "555-123-4567", "use": "home"},
                {"system": "email", "value": "john.smith@example.com"},
            ],
            "maritalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
                        "code": "M",
                        "display": "Married",
                    }
                ]
            },
            "communication": [
                {
                    "language": {
                        "coding": [
                            {
                                "system": "urn:ietf:bcp:47",
                                "code": "en",
                                "display": "English",
                            }
                        ]
                    },
                    "preferred": True,
                }
            ],
        }

        self.sample_observation = {
            "resourceType": "Observation",
            "id": "observation-001",
            "meta": {"versionId": "1", "lastUpdated": "2023-05-15T10:30:00Z"},
            "status": "final",
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "vital-signs",
                            "display": "Vital Signs",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8480-6",
                        "display": "Systolic blood pressure",
                    }
                ],
                "text": "Systolic blood pressure",
            },
            "subject": {"reference": "Patient/patient-001"},
            "effectiveDateTime": "2023-05-15T10:25:00Z",
            "valueQuantity": {
                "value": 120,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]",
            },
        }

        self.sample_condition = {
            "resourceType": "Condition",
            "id": "condition-001",
            "meta": {"versionId": "1", "lastUpdated": "2023-05-15T10:35:00Z"},
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                        "display": "Active",
                    }
                ]
            },
            "verificationStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                        "code": "confirmed",
                        "display": "Confirmed",
                    }
                ]
            },
            "category": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                            "code": "problem-list-item",
                            "display": "Problem List Item",
                        }
                    ]
                }
            ],
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "38341003",
                        "display": "Hypertension",
                    },
                    {
                        "system": "http://hl7.org/fhir/sid/icd-10-cm",
                        "code": "I10",
                        "display": "Essential (primary) hypertension",
                    },
                ],
                "text": "Hypertension",
            },
            "subject": {"reference": "Patient/patient-001"},
            "onsetDateTime": "2022-01-10",
            "recordedDate": "2022-01-15",
        }

        self.sample_medication_request = {
            "resourceType": "MedicationRequest",
            "id": "medication-request-001",
            "meta": {"versionId": "1", "lastUpdated": "2023-05-15T10:40:00Z"},
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "197361",
                        "display": "Amlodipine 5 MG Oral Tablet",
                    }
                ],
                "text": "Amlodipine 5 MG Oral Tablet",
            },
            "subject": {"reference": "Patient/patient-001"},
            "authoredOn": "2023-05-15",
            "requester": {
                "reference": "Practitioner/practitioner-001",
                "display": "Dr. Jane Doe",
            },
            "dosageInstruction": [
                {
                    "text": "Take 1 tablet by mouth once daily",
                    "timing": {
                        "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                    },
                    "route": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "26643006",
                                "display": "Oral route",
                            }
                        ]
                    },
                    "doseAndRate": [
                        {
                            "doseQuantity": {
                                "value": 1,
                                "unit": "tablet",
                                "system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
                                "code": "TAB",
                            }
                        }
                    ],
                }
            ],
        }

        # Create a mock FHIR connector
        self.mock_connector = MockFHIRConnector(
            patients=[self.sample_patient],
            observations=[self.sample_observation],
            conditions=[self.sample_condition],
            medications=[self.sample_medication_request],
        )

        # Create a data validator
        self.validator = DataValidator()

    def test_patient_conversion(self):
        """Test conversion of FHIR Patient resources to DataFrame."""
        # Convert patient to DataFrame
        patients_df = self.mock_connector.patients_to_dataframe([self.sample_patient])

        # Check DataFrame structure
        self.assertIsInstance(patients_df, pd.DataFrame)
        self.assertGreater(len(patients_df), 0)

        # Check essential columns
        essential_columns = [
            "patient_id",
            "family_name",
            "given_name",
            "gender",
            "birth_date",
        ]
        for column in essential_columns:
            self.assertIn(column, patients_df.columns)

        # Check values
        self.assertEqual(patients_df.iloc[0]["patient_id"], "patient-001")
        self.assertEqual(patients_df.iloc[0]["family_name"], "Smith")
        self.assertEqual(patients_df.iloc[0]["gender"], "male")
        self.assertEqual(patients_df.iloc[0]["birth_date"], "1970-01-25")

    def test_observation_conversion(self):
        """Test conversion of FHIR Observation resources to DataFrame."""
        # Convert observation to DataFrame
        observations_df = self.mock_connector.observations_to_dataframe(
            [self.sample_observation]
        )

        # Check DataFrame structure
        self.assertIsInstance(observations_df, pd.DataFrame)
        self.assertGreater(len(observations_df), 0)

        # Check essential columns
        essential_columns = [
            "observation_id",
            "patient_id",
            "code",
            "display",
            "value",
            "unit",
            "date",
        ]
        for column in essential_columns:
            self.assertIn(column, observations_df.columns)

        # Check values
        self.assertEqual(observations_df.iloc[0]["observation_id"], "observation-001")
        self.assertEqual(observations_df.iloc[0]["patient_id"], "patient-001")
        self.assertEqual(observations_df.iloc[0]["code"], "8480-6")
        self.assertEqual(observations_df.iloc[0]["value"], 120)
        self.assertEqual(observations_df.iloc[0]["unit"], "mmHg")

    def test_condition_conversion(self):
        """Test conversion of FHIR Condition resources to DataFrame."""
        # Convert condition to DataFrame
        conditions_df = self.mock_connector.conditions_to_dataframe(
            [self.sample_condition]
        )

        # Check DataFrame structure
        self.assertIsInstance(conditions_df, pd.DataFrame)
        self.assertGreater(len(conditions_df), 0)

        # Check essential columns
        essential_columns = [
            "condition_id",
            "patient_id",
            "code",
            "display",
            "onset_date",
            "clinical_status",
        ]
        for column in essential_columns:
            self.assertIn(column, conditions_df.columns)

        # Check values
        self.assertEqual(conditions_df.iloc[0]["condition_id"], "condition-001")
        self.assertEqual(conditions_df.iloc[0]["patient_id"], "patient-001")
        self.assertEqual(conditions_df.iloc[0]["clinical_status"], "active")
        self.assertIn("I10", conditions_df.iloc[0]["code"])  # ICD-10 code

    def test_medication_conversion(self):
        """Test conversion of FHIR MedicationRequest resources to DataFrame."""
        # Convert medication request to DataFrame
        medications_df = self.mock_connector.medications_to_dataframe(
            [self.sample_medication_request]
        )

        # Check DataFrame structure
        self.assertIsInstance(medications_df, pd.DataFrame)
        self.assertGreater(len(medications_df), 0)

        # Check essential columns
        essential_columns = [
            "medication_id",
            "patient_id",
            "medication_display",
            "status",
            "authored_date",
        ]
        for column in essential_columns:
            self.assertIn(column, medications_df.columns)

        # Check values
        self.assertEqual(
            medications_df.iloc[0]["medication_id"], "medication-request-001"
        )
        self.assertEqual(medications_df.iloc[0]["patient_id"], "patient-001")
        self.assertEqual(medications_df.iloc[0]["status"], "active")
        self.assertIn("Amlodipine", medications_df.iloc[0]["medication_display"])

    def test_bulk_export(self):
        """Test bulk export of FHIR resources."""
        # Create a temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export resources
            result = self.mock_connector.bulk_export(
                resource_types=[
                    "Patient",
                    "Observation",
                    "Condition",
                    "MedicationRequest",
                ],
                output_dir=temp_dir,
                format_type="json",
            )

            # Check result
            self.assertIsInstance(result, dict)
            self.assertEqual(len(result), 4)

            # Check exported files
            for resource_type in [
                "Patient",
                "Observation",
                "Condition",
                "MedicationRequest",
            ]:
                file_path = os.path.join(temp_dir, f"{resource_type}.json")
                self.assertTrue(os.path.exists(file_path))

                # Check file content
                with open(file_path, "r") as f:
                    content = json.load(f)
                    self.assertIsInstance(content, list)
                    self.assertGreater(len(content), 0)

    def test_dataframe_to_fhir(self):
        """Test conversion of DataFrames back to FHIR resources."""
        # Convert patient to DataFrame
        patients_df = self.mock_connector.patients_to_dataframe([self.sample_patient])

        # Convert DataFrame back to FHIR resources
        fhir_patients = self.mock_connector.dataframe_to_patients(patients_df)

        # Check result
        self.assertIsInstance(fhir_patients, list)
        self.assertGreater(len(fhir_patients), 0)
        self.assertEqual(fhir_patients[0]["resourceType"], "Patient")
        self.assertEqual(fhir_patients[0]["id"], "patient-001")

    def test_data_validation_integration(self):
        """Test integration with data validation."""
        # Convert patient to DataFrame
        patients_df = self.mock_connector.patients_to_dataframe([self.sample_patient])

        # Define schema for validation
        patient_schema = {
            "patient_id": {"type": "string", "required": True, "unique": True},
            "family_name": {"type": "string", "required": True},
            "given_name": {"type": "string", "required": True},
            "gender": {
                "type": "category",
                "required": True,
                "categories": ["male", "female", "other", "unknown"],
            },
            "birth_date": {"type": "string", "required": True},
        }

        # Validate data
        result = self.validator.validate_schema(patients_df, patient_schema)

        # Check validation result
        self.assertIsInstance(result, dict)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result.get("errors", [])), 0)

    def test_search_functionality(self):
        """Test FHIR search functionality."""
        # Test patient search
        patients = self.mock_connector.search("Patient", {"name": "Smith"})
        self.assertIsInstance(patients, list)
        self.assertGreater(len(patients), 0)

        # Test observation search
        observations = self.mock_connector.search("Observation", {"code": "8480-6"})
        self.assertIsInstance(observations, list)
        self.assertGreater(len(observations), 0)

        # Test condition search
        conditions = self.mock_connector.search("Condition", {"code": "I10"})
        self.assertIsInstance(conditions, list)
        self.assertGreater(len(conditions), 0)

    def test_error_handling(self):
        """Test error handling in FHIR connector."""
        # Test invalid resource type
        with self.assertRaises(ValueError):
            self.mock_connector.search("InvalidResourceType")

        # Test connection error
        error_connector = MockFHIRConnector(connection_error=True)
        with self.assertRaises(Exception):
            error_connector.search("Patient")

        # Test authentication error
        auth_error_connector = MockFHIRConnector(auth_error=True)
        with self.assertRaises(Exception):
            auth_error_connector.search("Patient")

    def test_pagination(self):
        """Test pagination of FHIR search results."""
        # Create a connector with many resources
        many_patients = [self.sample_patient.copy() for _ in range(20)]
        for i, patient in enumerate(many_patients):
            patient["id"] = f"patient-{i+1:03d}"

        pagination_connector = MockFHIRConnector(patients=many_patients)

        # Test pagination with limit
        patients = pagination_connector.search("Patient", max_count=10)
        self.assertIsInstance(patients, list)
        self.assertEqual(len(patients), 10)

        # Test pagination with no limit
        all_patients = pagination_connector.search("Patient")
        self.assertIsInstance(all_patients, list)
        self.assertEqual(len(all_patients), 20)

    def test_data_integration(self):
        """Test integration of different FHIR resource types."""
        # Convert all resources to DataFrames
        patients_df = self.mock_connector.patients_to_dataframe([self.sample_patient])
        observations_df = self.mock_connector.observations_to_dataframe(
            [self.sample_observation]
        )
        conditions_df = self.mock_connector.conditions_to_dataframe(
            [self.sample_condition]
        )
        medications_df = self.mock_connector.medications_to_dataframe(
            [self.sample_medication_request]
        )

        # Merge DataFrames
        patient_observations = pd.merge(
            patients_df, observations_df, on="patient_id", how="inner"
        )

        patient_conditions = pd.merge(
            patients_df, conditions_df, on="patient_id", how="inner"
        )

        patient_medications = pd.merge(
            patients_df, medications_df, on="patient_id", how="inner"
        )

        # Check merged DataFrames
        self.assertGreater(len(patient_observations), 0)
        self.assertGreater(len(patient_conditions), 0)
        self.assertGreater(len(patient_medications), 0)

        # Check patient data is preserved
        self.assertEqual(patient_observations.iloc[0]["family_name"], "Smith")
        self.assertEqual(patient_conditions.iloc[0]["family_name"], "Smith")
        self.assertEqual(patient_medications.iloc[0]["family_name"], "Smith")


class MockFHIRConnector:
    """Mock implementation of FHIRConnector for testing."""

    def __init__(
        self,
        patients=None,
        observations=None,
        conditions=None,
        medications=None,
        connection_error=False,
        auth_error=False,
    ):
        """Initialize the mock connector."""
        self.patients = patients or []
        self.observations = observations or []
        self.conditions = conditions or []
        self.medications = medications or []
        self.connection_error = connection_error
        self.auth_error = auth_error

        # Resource type mapping
        self.resources = {
            "Patient": self.patients,
            "Observation": self.observations,
            "Condition": self.conditions,
            "MedicationRequest": self.medications,
        }

    def search(self, resource_type, params=None, max_count=None):
        """Mock search functionality."""
        if self.connection_error:
            raise Exception("Connection error")

        if self.auth_error:
            raise Exception("Authentication error")

        if resource_type not in self.resources:
            raise ValueError(f"Unknown resource type: {resource_type}")

        resources = self.resources[resource_type]

        # Apply filtering if params provided
        if params:
            filtered_resources = []
            for resource in resources:
                match = True
                for key, value in params.items():
                    if key == "name" and resource.get("resourceType") == "Patient":
                        # Special handling for name search
                        patient_name = resource.get("name", [{}])[0].get("family", "")
                        if value not in patient_name:
                            match = False
                            break
                    elif key == "code":
                        # Special handling for code search
                        if resource.get("resourceType") == "Observation":
                            code_value = (
                                resource.get("code", {})
                                .get("coding", [{}])[0]
                                .get("code", "")
                            )
                            if value != code_value:
                                match = False
                                break
                        elif resource.get("resourceType") == "Condition":
                            # Check all codings
                            code_found = False
                            for coding in resource.get("code", {}).get("coding", []):
                                if coding.get("code") == value:
                                    code_found = True
                                    break
                            if not code_found:
                                match = False
                                break

                if match:
                    filtered_resources.append(resource)

            resources = filtered_resources

        # Apply pagination
        if max_count is not None and max_count < len(resources):
            resources = resources[:max_count]

        return resources

    def get(self, resource_type, resource_id):
        """Mock get functionality."""
        if self.connection_error:
            raise Exception("Connection error")

        if self.auth_error:
            raise Exception("Authentication error")

        if resource_type not in self.resources:
            raise ValueError(f"Unknown resource type: {resource_type}")

        for resource in self.resources[resource_type]:
            if resource.get("id") == resource_id:
                return resource

        raise Exception(f"Resource not found: {resource_type}/{resource_id}")

    def patients_to_dataframe(self, patients):
        """Convert Patient resources to DataFrame."""
        data = []

        for patient in patients:
            # Extract basic information
            patient_id = patient.get("id", "")

            # Extract name
            name = patient.get("name", [{}])[0]
            family = name.get("family", "")
            given = " ".join(name.get("given", []))

            # Extract other fields
            gender = patient.get("gender", "")
            birth_date = patient.get("birthDate", "")

            # Extract address
            address = patient.get("address", [{}])[0]
            address_line = ", ".join(address.get("line", []))
            city = address.get("city", "")
            state = address.get("state", "")
            postal_code = address.get("postalCode", "")
            country = address.get("country", "")

            # Extract contact information
            telecom = patient.get("telecom", [])
            phone = next(
                (t.get("value", "") for t in telecom if t.get("system") == "phone"), ""
            )
            email = next(
                (t.get("value", "") for t in telecom if t.get("system") == "email"), ""
            )

            # Create row
            row = {
                "patient_id": patient_id,
                "family_name": family,
                "given_name": given,
                "gender": gender,
                "birth_date": birth_date,
                "address_line": address_line,
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "country": country,
                "phone": phone,
                "email": email,
            }

            data.append(row)

        return pd.DataFrame(data)

    def observations_to_dataframe(self, observations):
        """Convert Observation resources to DataFrame."""
        data = []

        for obs in observations:
            # Extract basic information
            obs_id = obs.get("id", "")
            patient_id = (
                obs.get("subject", {}).get("reference", "").replace("Patient/", "")
            )

            # Extract date
            effective_date = obs.get("effectiveDateTime", "")

            # Extract code
            coding = obs.get("code", {}).get("coding", [{}])[0]
            code = coding.get("code", "")
            system = coding.get("system", "")
            display = coding.get("display", "")

            # Extract value
            value = None
            unit = ""

            if "valueQuantity" in obs:
                value = obs["valueQuantity"].get("value", "")
                unit = obs["valueQuantity"].get("unit", "")

            # Create row
            row = {
                "observation_id": obs_id,
                "patient_id": patient_id,
                "date": effective_date,
                "code": code,
                "system": system,
                "display": display,
                "value": value,
                "unit": unit,
                "status": obs.get("status", ""),
            }

            data.append(row)

        return pd.DataFrame(data)

    def conditions_to_dataframe(self, conditions):
        """Convert Condition resources to DataFrame."""
        data = []

        for condition in conditions:
            # Extract basic information
            condition_id = condition.get("id", "")
            patient_id = (
                condition.get("subject", {})
                .get("reference", "")
                .replace("Patient/", "")
            )

            # Extract dates
            onset_date = condition.get("onsetDateTime", "")

            # Extract code - use ICD-10 if available, otherwise first coding
            code = ""
            system = ""
            display = ""

            for coding in condition.get("code", {}).get("coding", []):
                if coding.get("system") == "http://hl7.org/fhir/sid/icd-10-cm":
                    code = coding.get("code", "")
                    system = coding.get("system", "")
                    display = coding.get("display", "")
                    break

            if not code and condition.get("code", {}).get("coding", []):
                coding = condition.get("code", {}).get("coding", [{}])[0]
                code = coding.get("code", "")
                system = coding.get("system", "")
                display = coding.get("display", "")

            # Extract clinical status
            clinical_status = (
                condition.get("clinicalStatus", {})
                .get("coding", [{}])[0]
                .get("code", "")
            )

            # Create row
            row = {
                "condition_id": condition_id,
                "patient_id": patient_id,
                "onset_date": onset_date,
                "code": code,
                "system": system,
                "display": display,
                "clinical_status": clinical_status,
            }

            data.append(row)

        return pd.DataFrame(data)

    def medications_to_dataframe(self, medications):
        """Convert MedicationRequest resources to DataFrame."""
        data = []

        for med in medications:
            # Extract basic information
            med_id = med.get("id", "")
            patient_id = (
                med.get("subject", {}).get("reference", "").replace("Patient/", "")
            )

            # Extract dates
            authored_date = med.get("authoredOn", "")

            # Extract medication
            medication_display = ""
            code = ""
            system = ""

            if "medicationCodeableConcept" in med:
                medication_coding = med["medicationCodeableConcept"].get(
                    "coding", [{}]
                )[0]
                medication_display = medication_coding.get("display", "")
                code = medication_coding.get("code", "")
                system = medication_coding.get("system", "")

            # Extract dosage
            dosage_text = ""
            if "dosageInstruction" in med and med["dosageInstruction"]:
                dosage_text = med["dosageInstruction"][0].get("text", "")

            # Create row
            row = {
                "medication_id": med_id,
                "patient_id": patient_id,
                "authored_date": authored_date,
                "medication_display": medication_display,
                "code": code,
                "system": system,
                "dosage_text": dosage_text,
                "status": med.get("status", ""),
            }

            data.append(row)

        return pd.DataFrame(data)

    def dataframe_to_patients(self, df):
        """Convert DataFrame back to Patient resources."""
        patients = []

        for _, row in df.iterrows():
            patient = {
                "resourceType": "Patient",
                "id": row.get("patient_id", ""),
                "name": [
                    {
                        "family": row.get("family_name", ""),
                        "given": (
                            row.get("given_name", "").split()
                            if row.get("given_name")
                            else []
                        ),
                    }
                ],
                "gender": row.get("gender", ""),
                "birthDate": row.get("birth_date", ""),
            }

            # Add address if available
            if (
                row.get("address_line")
                or row.get("city")
                or row.get("state")
                or row.get("postal_code")
            ):
                patient["address"] = [
                    {
                        "line": (
                            [row.get("address_line", "")]
                            if row.get("address_line")
                            else []
                        ),
                        "city": row.get("city", ""),
                        "state": row.get("state", ""),
                        "postalCode": row.get("postal_code", ""),
                        "country": row.get("country", ""),
                    }
                ]

            # Add telecom if available
            telecom = []
            if row.get("phone"):
                telecom.append({"system": "phone", "value": row.get("phone", "")})

            if row.get("email"):
                telecom.append({"system": "email", "value": row.get("email", "")})

            if telecom:
                patient["telecom"] = telecom

            patients.append(patient)

        return patients

    def bulk_export(self, resource_types, output_dir, format_type="json"):
        """Mock bulk export functionality."""
        if self.connection_error:
            raise Exception("Connection error")

        if self.auth_error:
            raise Exception("Authentication error")

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Initialize result
        result = {}

        # Export each resource type
        for resource_type in resource_types:
            if resource_type not in self.resources:
                continue

            resources = self.resources[resource_type]

            if not resources:
                continue

            # Determine file path
            file_path = os.path.join(output_dir, f"{resource_type}.{format_type}")

            # Write to file
            if format_type == "json":
                # Write as JSON array
                with open(file_path, "w") as f:
                    json.dump(resources, f, indent=2)

            elif format_type == "ndjson":
                # Write as newline-delimited JSON
                with open(file_path, "w") as f:
                    for resource in resources:
                        f.write(json.dumps(resource) + "\n")

            # Add to result
            result[resource_type] = file_path

        return result


if __name__ == "__main__":
    unittest.main()
