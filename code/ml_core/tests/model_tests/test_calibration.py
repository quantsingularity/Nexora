import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pandas as pd
import pytest
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

from ml_core.models.model_calibration import ModelCalibrator
from ml_core.utils.healthcare_metrics import HealthcareMetrics


@pytest.fixture
def calibration_data():
    np.random.seed(42)
    n = 1000
    y_true = np.random.binomial(1, 0.3, size=n)
    raw = np.random.normal(0.3, 0.2, size=n)
    y_pred_uncalibrated = np.clip(raw, 0.01, 0.99)
    y_pred_severe = np.power(y_pred_uncalibrated, 0.5)
    patient_ids = [f"P{i:04d}" for i in range(n)]
    ages = np.random.normal(65, 15, size=n).astype(int)
    genders = np.random.choice(["M", "F"], size=n)
    df = pd.DataFrame(
        {
            "patient_id": patient_ids,
            "age": ages,
            "gender": genders,
            "true_outcome": y_true,
            "prediction_uncalibrated": y_pred_uncalibrated,
            "prediction_severe": y_pred_severe,
        }
    )
    return {
        "y_true": y_true,
        "y_pred_uncalibrated": y_pred_uncalibrated,
        "y_pred_severe": y_pred_severe,
        "df": df,
    }


def test_calibration_curve(calibration_data):
    y_true = calibration_data["y_true"]
    y_pred = calibration_data["y_pred_uncalibrated"]
    prob_true, prob_pred = calibration_curve(y_true, y_pred, n_bins=10)
    assert len(prob_true) <= 10
    assert len(prob_pred) <= 10
    assert np.all(prob_true >= 0) and np.all(prob_true <= 1)
    assert np.all(prob_pred >= 0) and np.all(prob_pred <= 1)


def test_brier_score(calibration_data):
    y_true = calibration_data["y_true"]
    y_pred = calibration_data["y_pred_uncalibrated"]
    y_pred_severe = calibration_data["y_pred_severe"]
    brier = brier_score_loss(y_true, y_pred)
    assert 0 <= brier <= 1
    brier_severe = brier_score_loss(y_true, y_pred_severe)
    assert brier_severe > brier


def test_isotonic_calibration(calibration_data):
    calibrator = ModelCalibrator()
    y_true = calibration_data["y_true"]
    y_pred = calibration_data["y_pred_uncalibrated"]
    calibrated = calibrator.calibrate(y_pred, y_true, method="isotonic")
    assert len(calibrated) == len(y_pred)
    assert np.all(calibrated >= 0) and np.all(calibrated <= 1)
    brier_before = brier_score_loss(y_true, y_pred)
    brier_after = brier_score_loss(y_true, calibrated)
    assert brier_after <= brier_before * 1.05


def test_platt_scaling(calibration_data):
    calibrator = ModelCalibrator()
    y_true = calibration_data["y_true"]
    y_pred = calibration_data["y_pred_uncalibrated"]
    calibrated = calibrator.calibrate(y_pred, y_true, method="platt")
    assert len(calibrated) == len(y_pred)
    assert np.all(calibrated >= 0) and np.all(calibrated <= 1)
    brier_before = brier_score_loss(y_true, y_pred)
    brier_after = brier_score_loss(y_true, calibrated)
    assert brier_after <= brier_before * 1.05


def test_beta_calibration(calibration_data):
    calibrator = ModelCalibrator()
    y_true = calibration_data["y_true"]
    y_pred = calibration_data["y_pred_uncalibrated"]
    calibrated = calibrator.calibrate(y_pred, y_true, method="beta")
    assert len(calibrated) == len(y_pred)
    assert np.all(calibrated >= 0) and np.all(calibrated <= 1)
    brier_before = brier_score_loss(y_true, y_pred)
    brier_after = brier_score_loss(y_true, calibrated)
    assert brier_after <= brier_before * 1.05


def test_calibration_by_group(calibration_data):
    calibrator = ModelCalibrator()
    df = calibration_data["df"]
    result = calibrator.calculate_calibration_by_group(
        df,
        prediction_column="prediction_uncalibrated",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert "calibration_by_group" in result
    by_group = result["calibration_by_group"]
    assert "M" in by_group
    assert "F" in by_group
    for g, info in by_group.items():
        assert "brier_score_before" in info
        assert 0 <= info["brier_score_before"] <= 1


def test_invalid_calibration_method(calibration_data):
    calibrator = ModelCalibrator()
    y_true = calibration_data["y_true"]
    y_pred = calibration_data["y_pred_uncalibrated"]
    with pytest.raises(ValueError):
        calibrator.calibrate(y_pred, y_true, method="unknown_method")


def test_healthcare_metrics_evaluate(calibration_data):
    df = calibration_data["df"]
    metrics = HealthcareMetrics()
    results = metrics.evaluate_clinical_model(
        df,
        outcome_column="true_outcome",
        prediction_column="prediction_uncalibrated",
    )
    assert "auc" in results
    assert "brier_score" in results
    assert "calibration_slope" in results
    assert 0.0 <= results["auc"] <= 1.0
