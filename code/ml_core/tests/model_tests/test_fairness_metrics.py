"""Tests for FairnessEvaluator."""

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
from ml_core.models.fairness_metrics import FairnessEvaluator


@pytest.fixture
def fairness_df():
    np.random.seed(0)
    n = 400
    y_true = np.random.binomial(1, 0.3, n)
    groups = np.random.choice(["A", "B"], n)
    y_pred = np.clip(np.random.normal(0.3, 0.15, n), 0.01, 0.99)
    return pd.DataFrame({"group": groups, "outcome": y_true, "prediction": y_pred})


@pytest.fixture
def evaluator():
    return FairnessEvaluator()


def test_demographic_parity(evaluator, fairness_df):
    result = evaluator.calculate_demographic_parity(fairness_df, "prediction", "group")
    assert "demographic_parity" in result
    assert "positive_rates" in result
    assert 0.0 <= result["demographic_parity"] <= 1.0


def test_equal_opportunity(evaluator, fairness_df):
    result = evaluator.calculate_equal_opportunity(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "equal_opportunity" in result
    assert "true_positive_rates" in result


def test_equalized_odds(evaluator, fairness_df):
    result = evaluator.calculate_equalized_odds(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "equalized_odds" in result
    assert "true_positive_rates" in result
    assert "false_positive_rates" in result


def test_predictive_parity(evaluator, fairness_df):
    result = evaluator.calculate_predictive_parity(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "predictive_parity" in result
    assert "positive_predictive_values" in result


def test_calibration_by_group(evaluator, fairness_df):
    result = evaluator.calculate_calibration_by_group(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "calibration_by_group" in result
    assert "brier_scores" in result
    for g in ["A", "B"]:
        assert g in result["brier_scores"]


def test_auc_by_group(evaluator, fairness_df):
    result = evaluator.calculate_auc_by_group(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "auc_by_group" in result


def test_fairness_report(evaluator, fairness_df):
    report = evaluator.generate_fairness_report(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "demographic_parity" in report
    assert "equal_opportunity" in report
    assert "equalized_odds" in report
    assert "predictive_parity" in report
    assert "calibration_by_group" in report


def test_optimize_thresholds_equal_opportunity(evaluator, fairness_df):
    result = evaluator.optimize_thresholds_for_equal_opportunity(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "optimized_thresholds" in result
    assert "equal_opportunity_before" in result
    assert "equal_opportunity_after" in result
    assert (
        result["equal_opportunity_after"] <= result["equal_opportunity_before"] + 0.01
    )


def test_reweighting_reduces_disparity(evaluator, fairness_df):
    result = evaluator.improve_fairness_with_reweighting(
        fairness_df, "prediction", "outcome", "group"
    )
    assert "weights" in result
    assert "fairness_before" in result
    assert "fairness_after" in result
    assert result["fairness_after"] <= result["fairness_before"] + 1e-9


def test_cross_validate_fairness(evaluator, fairness_df):
    result = evaluator.cross_validate_fairness(
        fairness_df, "prediction", "outcome", "group", cv=3
    )
    assert "demographic_parity" in result
    assert "equal_opportunity" in result
    assert "fold_results" in result
    assert len(result["fold_results"]) == 3


def test_export_fairness_report(evaluator, fairness_df, tmp_path):
    report = evaluator.generate_fairness_report(
        fairness_df, "prediction", "outcome", "group"
    )
    path = str(tmp_path / "report.json")
    evaluator.export_fairness_report(report, path)
    import json

    with open(path) as f:
        loaded = json.load(f)
    assert "demographic_parity" in loaded


def test_plot_roc_curves(evaluator, fairness_df):
    fig = evaluator.plot_roc_curves_by_group(
        fairness_df, "prediction", "outcome", "group"
    )
    assert fig is not None


def test_fairness_across_thresholds(evaluator, fairness_df):
    result = evaluator.calculate_fairness_across_thresholds(
        fairness_df, "prediction", "outcome", "group", thresholds=[0.3, 0.5, 0.7]
    )
    assert "demographic_parity" in result
    assert len(result["demographic_parity"]) == 3
