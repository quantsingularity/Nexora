import json

import apache_beam as beam
import pytest
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to

from src.data_pipeline.clinical_etl import HealthcareETL


@pytest.fixture
def sample_fhir_bundle():
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "123",
                    "gender": "male",
                    "birthDate": "1970-01-01",
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"code": "A1C", "system": "LOINC"}]},
                    "valueQuantity": {"value": 6.5, "unit": "%"},
                }
            },
        ],
    }


def test_parse_fhir_bundle():
    with TestPipeline() as p:
        input_data = [json.dumps(sample_fhir_bundle())]
        output = (
            p | beam.Create(input_data) | "ParseFHIR" >> beam.Map(parse_fhir_bundle)
        )

        expected_output = [
            {
                "patient_id": "123",
                "gender": "male",
                "birth_date": "1970-01-01",
                "observations": [{"code": "A1C", "value": 6.5, "unit": "%"}],
            }
        ]

        assert_that(output, equal_to(expected_output))


def test_validate_clinical_data():
    with TestPipeline() as p:
        input_data = [
            {
                "patient_id": "123",
                "gender": "male",
                "birth_date": "1970-01-01",
                "observations": [{"code": "A1C", "value": 6.5, "unit": "%"}],
            }
        ]

        output = (
            p
            | beam.Create(input_data)
            | "ValidateClinicalData" >> beam.Map(ClinicalValidator().validate)
        )

        assert_that(output, equal_to(input_data))


def test_encode_medical_concepts():
    with TestPipeline() as p:
        input_data = [
            {
                "patient_id": "123",
                "diagnoses": ["E11.9", "I10"],
                "procedures": ["99213"],
            }
        ]

        output = (
            p
            | beam.Create(input_data)
            | "EncodeMedicalConcepts" >> beam.ParDo(ICD10Encoder())
        )

        expected_output = [
            {
                "patient_id": "123",
                "diagnosis_codes": [1001, 1002],  # Encoded ICD-10 codes
                "procedure_codes": [2001],  # Encoded CPT codes
            }
        ]

        assert_that(output, equal_to(expected_output))


def test_feature_generation():
    with TestPipeline() as p:
        input_data = [
            {
                "patient_id": "123",
                "age": 50,
                "gender": "M",
                "diagnosis_codes": [1001, 1002],
                "procedure_codes": [2001],
                "lab_results": [
                    {"code": "A1C", "value": 6.5, "timestamp": "2023-01-01"}
                ],
            }
        ]

        output = (
            p
            | beam.Create(input_data)
            | "FeatureGeneration" >> beam.ParDo(ClinicalFeatureGenerator())
        )

        expected_output = [
            {
                "patient_id": "123",
                "features": {
                    "age": 50,
                    "gender_M": 1,
                    "gender_F": 0,
                    "num_diagnoses": 2,
                    "num_procedures": 1,
                    "a1c_last": 6.5,
                    "a1c_trend": 0.0,
                },
            }
        ]

        assert_that(output, equal_to(expected_output))


def test_full_pipeline():
    with TestPipeline() as p:
        input_data = [json.dumps(sample_fhir_bundle())]

        output = p | beam.Create(input_data) | HealthcareETL()

        # Verify the output structure
        assert_that(
            output,
            lambda results: all(
                "patient_id" in result
                and "features" in result
                and "timestamp" in result
                for result in results
            ),
        )
