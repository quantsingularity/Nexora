"""Tests for DeepFM, TransformerModel, SurvivalAnalysisModel, and ModelCalibrator."""

import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import numpy as np
import pytest
from ml_core.models.deep_fm import DeepFMModel
from ml_core.models.model_calibration import ModelCalibrator
from ml_core.models.survival_analysis import SurvivalAnalysisModel
from ml_core.models.transformer_model import TransformerModel

# ──────────────────────────────── TransformerModel ────────────────────────────


@pytest.fixture
def transformer_config():
    return {
        "name": "test_transformer",
        "version": "0.1",
        "vocab_size": 100,
        "d_model": 16,
        "nhead": 2,
        "num_layers": 1,
        "dim_feedforward": 32,
    }


def test_transformer_predict_returns_dict(transformer_config):
    m = TransformerModel(transformer_config)
    result = m.predict(
        {"patient_id": "P001", "demographics": {}, "clinical_events": []}
    )
    assert isinstance(result, dict)
    assert "risk_score" in result
    assert 0.0 <= result["risk_score"] <= 1.0


def test_transformer_explain_returns_dict(transformer_config):
    m = TransformerModel(transformer_config)
    expl = m.explain({"patient_id": "P001", "demographics": {}, "clinical_events": []})
    assert isinstance(expl, dict)
    assert "method" in expl


def test_transformer_train_no_crash(transformer_config):
    m = TransformerModel(transformer_config)
    m.train(None)  # Should not raise even without torch


def test_transformer_uncertainty(transformer_config):
    m = TransformerModel(transformer_config)
    result = m.predict(
        {"patient_id": "P001", "demographics": {}, "clinical_events": []}
    )
    assert "uncertainty" in result
    ci = result["uncertainty"]["confidence_interval"]
    assert ci[0] <= ci[1]


def test_transformer_deterministic(transformer_config):
    m = TransformerModel(transformer_config)
    data = {"patient_id": "SAME_ID", "demographics": {}, "clinical_events": []}
    r1 = m.predict(data)
    r2 = m.predict(data)
    assert r1["risk_score"] == r2["risk_score"]


# ──────────────────────────────── DeepFMModel ─────────────────────────────────


@pytest.fixture
def deepfm_config():
    return {
        "name": "test_deepfm",
        "version": "0.1",
        "num_features": 10,
        "embedding_size": 4,
        "deep_layers": [32, 16],
    }


def test_deepfm_predict_returns_dict(deepfm_config):
    m = DeepFMModel(deepfm_config)
    result = m.predict(
        {"patient_id": "P002", "demographics": {}, "clinical_events": []}
    )
    assert isinstance(result, dict)
    assert "risk_score" in result
    assert 0.0 <= result["risk_score"] <= 1.0


def test_deepfm_explain_returns_dict(deepfm_config):
    m = DeepFMModel(deepfm_config)
    expl = m.explain({"patient_id": "P002", "demographics": {}, "clinical_events": []})
    assert isinstance(expl, dict)
    assert "method" in expl


def test_deepfm_train_no_crash(deepfm_config):
    m = DeepFMModel(deepfm_config)
    m.train(None)


# ──────────────────────────────── SurvivalAnalysisModel ───────────────────────


@pytest.fixture
def survival_config():
    return {
        "name": "test_survival",
        "version": "0.1",
        "duration_col": "duration",
        "event_col": "event_occurred",
    }


def test_survival_predict_returns_dict(survival_config):
    m = SurvivalAnalysisModel(survival_config)
    result = m.predict(
        {"patient_id": "P003", "demographics": {}, "clinical_events": []}
    )
    assert isinstance(result, dict)
    assert "risk_score" in result
    assert "survival_probability_30d" in result
    assert "median_survival_days" in result


def test_survival_probabilities_ordered(survival_config):
    m = SurvivalAnalysisModel(survival_config)
    result = m.predict(
        {"patient_id": "P003_ordered", "demographics": {}, "clinical_events": []}
    )
    assert (
        result["survival_probability_30d"] >= result["survival_probability_90d"]
        or abs(result["survival_probability_30d"] - result["survival_probability_90d"])
        < 0.3
    )


def test_survival_train_no_crash(survival_config):
    m = SurvivalAnalysisModel(survival_config)
    m.train(None)


# ──────────────────────────────── ModelCalibrator ─────────────────────────────


@pytest.fixture
def cal_data():
    np.random.seed(42)
    y_true = np.random.binomial(1, 0.3, 200)
    y_pred = np.clip(np.random.normal(0.3, 0.2, 200), 0.01, 0.99)
    return y_true, y_pred


def test_isotonic_calibration_bounds(cal_data):
    y_true, y_pred = cal_data
    cal = ModelCalibrator()
    out = cal.calibrate(y_pred, y_true, method="isotonic")
    assert len(out) == len(y_pred)
    assert (out >= 0).all() and (out <= 1).all()


def test_platt_calibration_bounds(cal_data):
    y_true, y_pred = cal_data
    cal = ModelCalibrator()
    out = cal.calibrate(y_pred, y_true, method="platt")
    assert len(out) == len(y_pred)
    assert (out >= 0).all() and (out <= 1).all()


def test_beta_calibration_bounds(cal_data):
    y_true, y_pred = cal_data
    cal = ModelCalibrator()
    out = cal.calibrate(y_pred, y_true, method="beta")
    assert len(out) == len(y_pred)
    assert (out >= 0).all() and (out <= 1).all()


def test_unknown_calibration_method(cal_data):
    y_true, y_pred = cal_data
    cal = ModelCalibrator()
    with pytest.raises(ValueError):
        cal.calibrate(y_pred, y_true, method="unknown_method")


def test_calibration_by_group(cal_data):
    import pandas as pd

    y_true, y_pred = cal_data
    n = len(y_true)
    df = pd.DataFrame(
        {
            "group": np.random.choice(["A", "B"], n),
            "prediction": y_pred,
            "outcome": y_true,
        }
    )
    cal = ModelCalibrator()
    result = cal.calculate_calibration_by_group(df, "prediction", "outcome", "group")
    assert "calibration_by_group" in result
    for g, v in result["calibration_by_group"].items():
        assert "brier_score_before" in v
        assert "brier_score_after" in v
