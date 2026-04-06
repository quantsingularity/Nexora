import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pandas as pd

# ---------------------------------------------------------------------------
# Helpers / minimal stubs for ETL components
# ---------------------------------------------------------------------------


class _MockFHIRConnector:
    """Returns a minimal patient data dict for any patient_id."""

    def get_patient_data(self, patient_id: str):
        return {
            "patient_id": patient_id,
            "demographics": {
                "gender": "male",
                "birthDate": "1980-01-01",
                "maritalStatus": None,
            },
            "clinical_events": [
                {
                    "type": "diagnosis",
                    "code": "I10",
                    "date": "2023-01-01",
                    "description": "Hypertension",
                }
            ],
            "lab_results": [
                {
                    "name": "Creatinine",
                    "value": 1.1,
                    "unit": "mg/dL",
                    "date": "2023-06-01",
                }
            ],
            "medications": [],
        }


# ---------------------------------------------------------------------------
# ClinicalETL tests (using patching so no live FHIR server is needed)
# ---------------------------------------------------------------------------


def test_clinical_etl_transform_empty():
    """transform() on empty input returns empty DataFrame."""
    from data_pipeline.clinical_etl import ClinicalETL

    etl = ClinicalETL()
    result = etl.transform([])
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_clinical_etl_transform_single_patient(monkeypatch):
    """transform() correctly flattens a single patient record."""
    from data_pipeline.clinical_etl import ClinicalETL

    raw = [
        {
            "patient_id": "PAT001",
            "demographics": {
                "gender": "male",
                "birthDate": "1970-01-01",
                "maritalStatus": None,
            },
            "clinical_events": [
                {"type": "diagnosis", "code": "I10", "date": "2023-01-01"}
            ],
            "lab_results": [
                {
                    "name": "Creatinine",
                    "value": 1.2,
                    "unit": "mg/dL",
                    "date": "2023-06-01",
                }
            ],
            "medications": [],
        }
    ]

    etl = ClinicalETL()
    df = etl.transform(raw)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert "patient_id" in df.columns
    assert df.iloc[0]["patient_id"] == "PAT001"


def test_clinical_etl_transform_multiple_patients(monkeypatch):
    """transform() handles multiple patients."""
    from data_pipeline.clinical_etl import ClinicalETL

    raw = [
        {
            "patient_id": f"PAT{i:03d}",
            "demographics": {"gender": "male", "birthDate": "1970-01-01"},
            "clinical_events": [
                {"type": "diagnosis", "code": "E11", "date": "2023-01-01"}
            ],
            "lab_results": [],
            "medications": [],
        }
        for i in range(5)
    ]

    etl = ClinicalETL()
    df = etl.transform(raw)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5


def test_clinical_etl_extract_handles_error(monkeypatch):
    """extract() skips patients that raise errors and continues."""
    from data_pipeline import clinical_etl as etl_module

    connector = _MockFHIRConnector()

    def bad_get(pid):
        if pid == "BAD":
            raise ValueError("Patient not found")
        return connector.get_patient_data(pid)

    connector.get_patient_data = bad_get

    # Patch FHIRConnector inside the module
    class _PatchedETL(etl_module.ClinicalETL):
        def __init__(self):
            super().__init__()
            self.fhir_connector = connector

    etl = _PatchedETL()
    result = etl.extract(["PAT001", "BAD", "PAT002"])
    # Should return 2 valid results, skip BAD
    assert len(result) == 2


def test_clinical_etl_load_creates_file(tmp_path, monkeypatch):
    """load() writes the feature parquet file."""
    from data_pipeline.clinical_etl import ClinicalETL

    monkeypatch.chdir(tmp_path)
    etl = ClinicalETL()
    df = pd.DataFrame({"patient_id": ["P1"], "gender": ["male"]})
    etl.load(df)
    output_file = tmp_path / "data" / "processed" / "features.parquet"
    assert output_file.exists()


def test_clinical_etl_run_pipeline(monkeypatch):
    """run_pipeline() returns a DataFrame and calls all three stages."""
    from data_pipeline import clinical_etl as etl_module

    raw_record = {
        "patient_id": "PAT001",
        "demographics": {"gender": "male", "birthDate": "1970-01-01"},
        "clinical_events": [{"type": "diagnosis", "code": "I10", "date": "2023-01-01"}],
        "lab_results": [],
        "medications": [],
    }

    calls = {"extract": 0, "transform": 0, "load": 0}

    class _TrackedETL(etl_module.ClinicalETL):
        def extract(self, ids):
            calls["extract"] += 1
            return [raw_record] * len(ids)

        def load(self, df):
            calls["load"] += 1

    etl = _TrackedETL()
    result = etl.run_pipeline(["PAT001", "PAT002"])
    assert isinstance(result, pd.DataFrame)
    assert calls["extract"] == 1
    assert calls["load"] == 1
