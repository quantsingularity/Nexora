"""Tests for data_pipeline: DataValidator, ClinicalETL."""

import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import pandas as pd
import pytest

from ml_core.pipeline.clinical_etl import ClinicalETL
from ml_core.pipeline.data_validation import DataValidator

# ──────────────────────────────── DataValidator ───────────────────────────────


@pytest.fixture
def validator():
    return DataValidator()


@pytest.fixture
def base_df():
    return pd.DataFrame(
        {
            "patient_id": ["P001", "P002", "P003"],
            "age": [45, 67, 32],
            "gender": ["M", "F", "M"],
            "readmission": [0, 1, 0],
            "mortality": [0, 0, 0],
        }
    )


@pytest.fixture
def full_schema():
    return {
        "patient_id": {"type": "string", "required": True, "unique": True},
        "age": {"type": "integer", "required": True, "min": 0, "max": 120},
        "gender": {"type": "category", "required": True, "categories": ["M", "F", "O"]},
        "readmission": {"type": "boolean", "required": True},
        "mortality": {"type": "boolean", "required": True},
    }


def test_schema_valid(validator, base_df, full_schema):
    result = validator.validate_schema(base_df, full_schema)
    assert result["valid"], result["errors"]


def test_schema_missing_required_col(validator, base_df, full_schema):
    bad = base_df.drop(columns=["age"])
    result = validator.validate_schema(bad, full_schema)
    assert not result["valid"]
    assert any("age" in e for e in result["errors"])


def test_schema_out_of_range(validator, base_df, full_schema):
    bad = base_df.copy()
    bad["age"] = bad["age"].astype(object)
    bad.loc[0, "age"] = 200
    result = validator.validate_schema(bad, full_schema)
    assert not result["valid"]


def test_schema_bad_category(validator, base_df, full_schema):
    bad = base_df.copy()
    bad.loc[0, "gender"] = "X"
    result = validator.validate_schema(bad, full_schema)
    assert not result["valid"]


def test_schema_bad_string_pattern(validator):
    df = pd.DataFrame({"code": ["A01.0", "bad_code", "B20"]})
    schema = {
        "code": {
            "type": "string",
            "required": True,
            "pattern": r"^[A-Z][0-9]{2}(\.[0-9]{1,4})?$",
        }
    }
    result = validator.validate_schema(df, schema)
    assert not result["valid"]


def test_schema_duplicate_unique_col(validator, base_df, full_schema):
    dup = pd.concat([base_df, base_df.iloc[:1]], ignore_index=True)
    result = validator.validate_schema(dup, full_schema)
    assert not result["valid"]


def test_relationships_temporal_ok(validator, base_df):
    df = base_df.copy()
    df["start"] = pd.to_datetime("2023-01-01")
    df["end"] = pd.to_datetime("2023-01-10")
    rels = [{"type": "temporal", "first": "start", "second": "end", "relation": "<="}]
    result = validator.validate_relationships(df, rels)
    assert result["valid"]


def test_relationships_temporal_violation(validator, base_df):
    df = base_df.copy()
    df["start"] = pd.to_datetime("2023-01-10")
    df["end"] = pd.to_datetime("2023-01-01")
    rels = [{"type": "temporal", "first": "start", "second": "end", "relation": "<="}]
    result = validator.validate_relationships(df, rels)
    assert not result["valid"]


def test_relationships_logical_ok(validator, base_df):
    rels = [
        {
            "type": "logical",
            "condition": "mortality == 1",
            "implication": "readmission == 0",
        }
    ]
    result = validator.validate_relationships(base_df, rels)
    assert result["valid"]


def test_relationships_logical_violation(validator, base_df):
    bad = base_df.copy()
    bad.loc[0, "mortality"] = 1
    bad.loc[0, "readmission"] = 1
    rels = [
        {
            "type": "logical",
            "condition": "mortality == 1",
            "implication": "readmission == 0",
        }
    ]
    result = validator.validate_relationships(bad, rels)
    assert not result["valid"]


def test_detect_outliers_iqr(validator):
    df = pd.DataFrame({"val": [1, 2, 2, 2, 3, 3, 100]})
    result = validator.detect_outliers(df, ["val"], method="iqr", threshold=1.5)
    assert "val" in result["outliers"]
    assert len(result["outliers"]["val"]) > 0


def test_detect_outliers_zscore(validator):
    df = pd.DataFrame({"val": [10] * 50 + [1000]})
    result = validator.detect_outliers(df, ["val"], method="z-score", threshold=2.0)
    assert len(result["outliers"]["val"]) > 0


def test_detect_outliers_unknown_method(validator):
    df = pd.DataFrame({"val": [1, 2, 3]})
    with pytest.raises(ValueError):
        validator.detect_outliers(df, ["val"], method="unknown")


def test_check_missing_values(validator):
    df = pd.DataFrame({"a": [1, None, 3], "b": [1, 2, 3]})
    result = validator.check_missing_values(df)
    assert result["missing_counts"]["a"] == 1
    assert result["missing_counts"]["b"] == 0
    assert result["has_missing"]


def test_check_duplicates(validator, base_df):
    result = validator.check_duplicates(base_df, subset=["patient_id"])
    assert not result["has_duplicates"]
    dup = pd.concat([base_df, base_df.iloc[:1]], ignore_index=True)
    result2 = validator.check_duplicates(dup, subset=["patient_id"])
    assert result2["has_duplicates"]


def test_validate_icd10_valid(validator):
    codes = pd.Series(["A01.0", "B20", "I10", "E11.9"])
    result = validator.validate_icd10_codes(codes)
    assert result["valid"]
    assert len(result["invalid_codes"]) == 0


def test_validate_icd10_invalid(validator):
    codes = pd.Series(["A01.0", "XYZ", "999"])
    result = validator.validate_icd10_codes(codes)
    assert not result["valid"]


def test_validate_date_ranges(validator, base_df):
    df = base_df.copy()
    df["date"] = pd.to_datetime(["2023-01-01", "2023-06-01", "2023-12-01"])
    result = validator.validate_date_ranges(
        df, "date", min_date="2023-01-01", max_date="2023-12-31"
    )
    assert result["valid"]
    result2 = validator.validate_date_ranges(
        df, "date", min_date="2023-07-01", max_date="2023-12-31"
    )
    assert not result2["valid"]


def test_validate_consistency(validator, base_df):
    rules = [{"name": "r1", "condition": "age >= 65", "expected": "age < 200"}]
    result = validator.validate_consistency(base_df, rules)
    assert result["valid"]


def test_generate_report_structure(validator, base_df, full_schema):
    report = validator.generate_validation_report(
        base_df,
        schema=full_schema,
        outlier_columns=["age"],
        consistency_rules=[
            {"name": "r", "condition": "age > 0", "expected": "age < 200"}
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
    assert "error_count" in report["summary"]


# ──────────────────────────────── ClinicalETL ─────────────────────────────────


def _make_patient(pid):
    return {
        "patient_id": pid,
        "demographics": {"gender": "M", "birthDate": "1970-01-01"},
        "clinical_events": [{"type": "diagnosis", "code": "I10", "date": "2023-01-01"}],
        "lab_results": [
            {"name": "Creatinine", "value": 1.1, "unit": "mg/dL", "date": "2023-06-01"}
        ],
        "medications": [],
    }


def test_etl_transform_empty():
    etl = ClinicalETL()
    result = etl.transform([])
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_etl_transform_single():
    etl = ClinicalETL()
    raw = [_make_patient("PAT001")]
    df = etl.transform(raw)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "patient_id" in df.columns


def test_etl_transform_multiple():
    etl = ClinicalETL()
    raw = [_make_patient(f"P{i:03d}") for i in range(5)]
    df = etl.transform(raw)
    assert len(df) == 5


def test_etl_transform_no_lab():
    etl = ClinicalETL()
    raw = [
        {
            "patient_id": "P_NOLAB",
            "demographics": {},
            "clinical_events": [],
            "lab_results": [],
        }
    ]
    df = etl.transform(raw)
    assert len(df) == 1


def test_etl_load(tmp_path):
    etl = ClinicalETL()
    df = pd.DataFrame({"patient_id": ["P001"], "age": [45]})
    out_path = str(tmp_path / "features.parquet")
    result = etl.load(df, output_path=out_path)
    assert os.path.exists(result)
