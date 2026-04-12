import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import pandas as pd
import pytest
from ml_core.utils.healthcare_metrics import HealthcareMetrics


@pytest.fixture
def encounter_df():
    return pd.DataFrame(
        {
            "patient_id": ["P001", "P001", "P002", "P003"],
            "encounter_id": ["E001", "E002", "E003", "E004"],
            "admission_date": pd.to_datetime(
                ["2023-01-01", "2023-02-10", "2023-03-01", "2023-04-01"]
            ),
            "discharge_date": pd.to_datetime(
                ["2023-01-05", "2023-02-15", "2023-03-08", "2023-04-10"]
            ),
            "mortality": [0, 0, 0, 1],
            "expected": [0.05, 0.08, 0.10, 0.80],
            "readmission": [0, 1, 0, 0],
            "complication": [0, 1, 0, 0],
            "prediction": [0.3, 0.7, 0.2, 0.9],
        }
    )


@pytest.fixture
def metrics():
    return HealthcareMetrics()


def test_length_of_stay(metrics, encounter_df):
    los = metrics.calculate_length_of_stay(encounter_df)
    assert len(los) == len(encounter_df)
    assert (los >= 0).all()
    assert abs(los.iloc[0] - 4.0) < 0.01  # Jan 1-5 = 4 days


def test_los_missing_col(metrics, encounter_df):
    bad = encounter_df.drop(columns=["admission_date"])
    with pytest.raises(ValueError):
        metrics.calculate_length_of_stay(bad)


def test_readmission_rate(metrics, encounter_df):
    rate = metrics.calculate_readmission_rate(encounter_df, window_days=30)
    assert 0.0 <= rate <= 1.0


def test_mortality_index(metrics, encounter_df):
    idx = metrics.calculate_mortality_index(encounter_df)
    assert isinstance(idx, float)
    assert idx >= 0


def test_mortality_index_missing_col(metrics, encounter_df):
    bad = encounter_df.drop(columns=["expected"])
    with pytest.raises(ValueError):
        metrics.calculate_mortality_index(bad)


def test_complication_rate(metrics, encounter_df):
    rate = metrics.calculate_complication_rate(encounter_df)
    assert 0.0 <= rate <= 1.0


def test_evaluate_clinical_model(metrics, encounter_df):
    result = metrics.evaluate_clinical_model(encounter_df, "mortality", "prediction")
    assert "auc" in result
    assert "brier_score" in result
    assert "sensitivity" in result
    assert "specificity" in result


def test_evaluate_clinical_model_missing_col(metrics, encounter_df):
    with pytest.raises(ValueError):
        metrics.evaluate_clinical_model(encounter_df, "nonexistent_col", "prediction")


def test_quality_metrics(metrics, encounter_df):
    qm = metrics.calculate_quality_metrics(encounter_df)
    assert isinstance(qm, dict)
    assert "mean_los" in qm
    assert "readmission_30day" in qm


def test_smr_scalar(metrics, encounter_df):
    smr = metrics.calculate_standardized_mortality_ratio(encounter_df)
    assert isinstance(smr, dict)
    assert "smr" in smr


def test_oe_ratio(metrics, encounter_df):
    ratio = metrics.calculate_observed_expected_ratio(
        encounter_df, "mortality", "expected"
    )
    assert isinstance(ratio, float)
    assert ratio >= 0


def test_excess_events(metrics, encounter_df):
    excess = metrics.calculate_excess_events(encounter_df, "mortality", "expected")
    assert isinstance(excess, (int, float))
