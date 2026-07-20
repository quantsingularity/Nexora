import os
import sys
from datetime import timedelta

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import numpy as np
import pandas as pd
import pytest

from ml_core.pipeline.data_validation import DataValidator


@pytest.fixture
def sample_data():
    df = pd.DataFrame(
        {
            "patient_id": pd.array(["P001", "P002", "P003", "P004", "P005"]),
            "age": pd.array([45, 67, 32, 78, 50], dtype=object),
            "gender": pd.array(["M", "F", "M", "F", "M"]),
            "diagnosis_code": pd.array(["I25.10", "E11.9", "J44.9", "I10", "K21.0"]),
            "admission_date": pd.to_datetime(
                ["2023-01-15", "2023-02-20", "2023-03-10", "2023-04-05", "2023-05-12"]
            ),
            "discharge_date": pd.to_datetime(
                ["2023-01-20", "2023-03-01", "2023-03-15", "2023-04-15", "2023-05-18"]
            ),
            "lab_value": pd.array([120.5, 95.2, 110.8, 140.3, 105.7]),
            "medication_count": pd.array([3, 5, 2, 7, 4]),
            "readmission": pd.array([0, 1, 0, 0, 0]),
            "mortality": pd.array([0, 0, 0, 1, 0]),
        }
    )
    return df


@pytest.fixture
def schema():
    return {
        "patient_id": {"type": "string", "required": True, "unique": True},
        "age": {"type": "integer", "required": True, "min": 0, "max": 120},
        "gender": {"type": "category", "required": True, "categories": ["M", "F", "O"]},
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


@pytest.fixture
def relationships():
    return [
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


@pytest.fixture
def validator():
    return DataValidator()


def test_validate_schema_valid(validator, sample_data, schema):
    result = validator.validate_schema(sample_data, schema)
    assert result["valid"], result["errors"]


def test_validate_schema_invalid_type(validator, sample_data, schema):
    bad = sample_data.copy()
    bad["age"] = bad["age"].astype(object)
    bad.loc[0, "age"] = "forty-five"
    result = validator.validate_schema(bad, schema)
    assert not result["valid"]


def test_validate_schema_out_of_range(validator, sample_data, schema):
    bad = sample_data.copy()
    bad["age"] = bad["age"].astype(object)
    bad.loc[0, "age"] = 150
    result = validator.validate_schema(bad, schema)
    assert not result["valid"]


def test_validate_schema_invalid_category(validator, sample_data, schema):
    bad = sample_data.copy()
    bad.loc[0, "gender"] = "X"
    result = validator.validate_schema(bad, schema)
    assert not result["valid"]


def test_validate_schema_invalid_pattern(validator, sample_data, schema):
    bad = sample_data.copy()
    bad.loc[0, "diagnosis_code"] = "12345"
    result = validator.validate_schema(bad, schema)
    assert not result["valid"]


def test_validate_relationships_valid(validator, sample_data, relationships):
    result = validator.validate_relationships(sample_data, relationships)
    assert result["valid"], result["errors"]


def test_validate_relationships_temporal_violation(
    validator, sample_data, relationships
):
    bad = sample_data.copy()
    bad.loc[0, "discharge_date"] = bad.loc[0, "admission_date"] - timedelta(days=1)
    result = validator.validate_relationships(bad, relationships)
    assert not result["valid"]


def test_validate_relationships_logical_violation(
    validator, sample_data, relationships
):
    bad = sample_data.copy()
    bad.loc[3, "mortality"] = 1
    bad.loc[3, "readmission"] = 1
    result = validator.validate_relationships(bad, relationships)
    assert not result["valid"]


def test_detect_outliers_iqr(validator, sample_data):
    result = validator.detect_outliers(
        sample_data, ["age", "lab_value", "medication_count"]
    )
    assert isinstance(result, dict)
    assert "outliers" in result
    assert "age" in result["outliers"]


def test_detect_outliers_zscore(validator, sample_data):
    result = validator.detect_outliers(
        sample_data,
        ["age", "lab_value", "medication_count"],
        method="z-score",
        threshold=3.0,
    )
    assert isinstance(result, dict)


def test_check_missing_values(validator, sample_data):
    bad = sample_data.copy()
    bad.loc[0, "lab_value"] = np.nan
    bad.loc[1, "medication_count"] = np.nan
    result = validator.check_missing_values(bad)
    assert result["missing_counts"]["lab_value"] == 1
    assert result["missing_counts"]["medication_count"] == 1


def test_validate_icd10_codes_valid(validator):
    valid = pd.Series(["A01.0", "B20", "C34.90", "E11.9", "I25.10", "J44.9", "K21.0"])
    result = validator.validate_icd10_codes(valid)
    assert result["valid"]


def test_validate_icd10_codes_invalid(validator):
    invalid = pd.Series(["A01.0", "XYZ", "123.45", "B20.ABC", "I25.999"])
    result = validator.validate_icd10_codes(invalid)
    assert not result["valid"]
    assert len(result["invalid_codes"]) >= 3


def test_validate_date_ranges_valid(validator, sample_data):
    result = validator.validate_date_ranges(
        sample_data, "admission_date", min_date="2023-01-01", max_date="2023-12-31"
    )
    assert result["valid"]


def test_validate_date_ranges_invalid(validator, sample_data):
    result = validator.validate_date_ranges(
        sample_data, "admission_date", min_date="2023-03-01", max_date="2023-04-30"
    )
    assert not result["valid"]


def test_check_duplicates_none(validator, sample_data):
    result = validator.check_duplicates(sample_data, ["patient_id"])
    assert not result["has_duplicates"]


def test_check_duplicates_found(validator, sample_data):
    dupe = pd.concat([sample_data, sample_data.iloc[0:2]], ignore_index=True)
    result = validator.check_duplicates(dupe, ["patient_id"])
    assert result["has_duplicates"]


def test_validate_consistency(validator, sample_data):
    rules = [
        {
            "condition": "age >= 65",
            "expected": "medication_count >= 3",
            "name": "elderly_medication",
        },
        {
            "condition": "mortality == 1",
            "expected": "age > 70",
            "name": "mortality_age",
        },
    ]
    result = validator.validate_consistency(sample_data, rules)
    assert isinstance(result, dict)
    assert "rule_results" in result


def test_generate_validation_report(validator, sample_data, schema, relationships):
    report = validator.generate_validation_report(
        sample_data,
        schema=schema,
        relationships=relationships,
        outlier_columns=["lab_value", "medication_count"],
        consistency_rules=[
            {
                "condition": "age >= 65",
                "expected": "medication_count >= 3",
                "name": "elderly_medication",
            }
        ],
    )
    for key in [
        "schema_validation",
        "relationship_validation",
        "missing_values",
        "outliers",
        "duplicates",
        "consistency",
        "summary",
    ]:
        assert key in report
    assert "valid" in report["summary"]


def test_integration_with_fhir_mock(validator):
    patients_df = pd.DataFrame(
        {
            "patient_id": ["P001", "P002"],
            "gender": ["M", "F"],
            "birth_date": ["1978-01-15", "1956-05-22"],
        }
    )
    schema = {
        "patient_id": {"type": "string", "required": True, "unique": True},
        "gender": {"type": "category", "required": True, "categories": ["M", "F", "O"]},
        "birth_date": {"type": "string", "required": True},
    }
    result = validator.validate_schema(patients_df, schema)
    assert result["valid"], result["errors"]
