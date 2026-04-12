import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from ml_core.models.fairness_metrics import FairnessEvaluator
from ml_core.utils.healthcare_metrics import HealthcareMetrics


@pytest.fixture
def fairness_df():
    np.random.seed(42)
    n = 1000
    y_true = np.random.binomial(1, 0.3, size=n)
    genders = np.random.choice(["M", "F"], size=n, p=[0.6, 0.4])
    races = np.random.choice(
        ["White", "Black", "Hispanic", "Asian", "Other"],
        size=n,
        p=[0.6, 0.15, 0.15, 0.05, 0.05],
    )
    insurance = np.random.choice(
        ["Private", "Medicare", "Medicaid", "Uninsured"],
        size=n,
        p=[0.5, 0.3, 0.15, 0.05],
    )
    y_pred = np.clip(np.random.normal(0.3, 0.2, size=n), 0.01, 0.99)
    # Introduce bias: females with condition get lower scores
    female_cond = (genders == "F") & (y_true == 1)
    y_pred[female_cond] *= 0.7
    black_cond = (races == "Black") & (y_true == 1)
    y_pred[black_cond] *= 0.7
    y_pred = np.clip(y_pred, 0.01, 0.99)

    df = pd.DataFrame(
        {
            "patient_id": [f"P{i:04d}" for i in range(n)],
            "age": np.random.normal(65, 15, n).astype(int),
            "gender": genders,
            "race": races,
            "insurance": insurance,
            "true_outcome": y_true,
            "prediction": y_pred,
        }
    )
    df["age_group"] = pd.cut(
        df["age"],
        bins=[0, 18, 35, 50, 65, 80, 120],
        labels=["0-18", "19-35", "36-50", "51-65", "66-80", "80+"],
    )
    return df


@pytest.fixture
def evaluator():
    return FairnessEvaluator()


@pytest.fixture
def metrics():
    return HealthcareMetrics()


def test_demographic_parity(evaluator, fairness_df):
    dp = evaluator.calculate_demographic_parity(
        fairness_df,
        prediction_column="prediction",
        group_column="gender",
        threshold=0.5,
    )
    assert "demographic_parity" in dp
    assert "positive_rates" in dp
    assert "M" in dp["positive_rates"]
    assert "F" in dp["positive_rates"]

    dp_race = evaluator.calculate_demographic_parity(
        fairness_df,
        prediction_column="prediction",
        group_column="race",
        threshold=0.5,
    )
    for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
        assert race in dp_race["positive_rates"]


def test_equal_opportunity(evaluator, fairness_df):
    eo = evaluator.calculate_equal_opportunity(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        threshold=0.5,
    )
    assert "equal_opportunity" in eo
    assert "true_positive_rates" in eo
    assert "M" in eo["true_positive_rates"]
    assert "F" in eo["true_positive_rates"]
    # Biased: females have lower TPR
    assert eo["true_positive_rates"]["F"] < eo["true_positive_rates"]["M"]

    eo_race = evaluator.calculate_equal_opportunity(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="race",
        threshold=0.5,
    )
    for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
        assert race in eo_race["true_positive_rates"]
    assert (
        eo_race["true_positive_rates"]["Black"]
        < eo_race["true_positive_rates"]["White"]
    )


def test_equalized_odds(evaluator, fairness_df):
    eodds = evaluator.calculate_equalized_odds(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        threshold=0.5,
    )
    assert "equalized_odds" in eodds
    assert "true_positive_rates" in eodds
    assert "false_positive_rates" in eodds
    assert "M" in eodds["true_positive_rates"]
    assert "F" in eodds["false_positive_rates"]

    eodds_race = evaluator.calculate_equalized_odds(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="race",
        threshold=0.5,
    )
    for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
        assert race in eodds_race["true_positive_rates"]
        assert race in eodds_race["false_positive_rates"]


def test_predictive_parity(evaluator, fairness_df):
    pp = evaluator.calculate_predictive_parity(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        threshold=0.5,
    )
    assert "predictive_parity" in pp
    assert "positive_predictive_values" in pp
    assert "M" in pp["positive_predictive_values"]
    assert "F" in pp["positive_predictive_values"]

    pp_race = evaluator.calculate_predictive_parity(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="race",
        threshold=0.5,
    )
    for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
        assert race in pp_race["positive_predictive_values"]


def test_calibration_by_group(evaluator, fairness_df):
    cal = evaluator.calculate_calibration_by_group(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert "calibration_by_group" in cal
    assert "brier_scores" in cal
    assert "M" in cal["brier_scores"]
    assert "F" in cal["brier_scores"]
    # Females have higher Brier score due to injected bias
    assert cal["brier_scores"]["F"] > cal["brier_scores"]["M"]

    cal_race = evaluator.calculate_calibration_by_group(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="race",
    )
    for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
        assert race in cal_race["brier_scores"]
    assert cal_race["brier_scores"]["Black"] > cal_race["brier_scores"]["White"]


def test_auc_by_group(evaluator, fairness_df):
    auc_res = evaluator.calculate_auc_by_group(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert "auc_by_group" in auc_res
    assert "M" in auc_res["auc_by_group"]
    assert "F" in auc_res["auc_by_group"]


def test_fairness_metrics_report(evaluator, fairness_df):
    report = evaluator.generate_fairness_report(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        threshold=0.5,
    )
    for key in [
        "demographic_parity",
        "equal_opportunity",
        "equalized_odds",
        "predictive_parity",
        "calibration_by_group",
        "auc_by_group",
    ]:
        assert key in report


def test_fairness_plots(evaluator, fairness_df):
    fig_roc = evaluator.plot_roc_curves_by_group(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert isinstance(fig_roc, plt.Figure)

    fig_pr = evaluator.plot_precision_recall_curves_by_group(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert isinstance(fig_pr, plt.Figure)

    fig_cal = evaluator.plot_calibration_curves_by_group(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert isinstance(fig_cal, plt.Figure)

    fig_cmp = evaluator.plot_fairness_metrics_comparison(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_columns=["gender", "race", "insurance"],
        threshold=0.5,
    )
    assert isinstance(fig_cmp, plt.Figure)
    plt.close("all")


def test_threshold_optimization_equal_opportunity(evaluator, fairness_df):
    result = evaluator.optimize_thresholds_for_equal_opportunity(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert "optimized_thresholds" in result
    assert "M" in result["optimized_thresholds"]
    assert "F" in result["optimized_thresholds"]
    assert "equal_opportunity_before" in result
    assert "equal_opportunity_after" in result
    assert result["equal_opportunity_after"] < result["equal_opportunity_before"]


def test_threshold_optimization_equalized_odds(evaluator, fairness_df):
    result = evaluator.optimize_thresholds_for_equalized_odds(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
    )
    assert "optimized_thresholds" in result
    assert "M" in result["optimized_thresholds"]
    assert "F" in result["optimized_thresholds"]
    assert "equalized_odds_before" in result
    assert "equalized_odds_after" in result
    assert result["equalized_odds_after"] < result["equalized_odds_before"]


def test_intersectional_fairness(evaluator, fairness_df):
    df = fairness_df.copy()
    df["gender_race"] = df["gender"] + "_" + df["race"]
    report = evaluator.generate_fairness_report(
        df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender_race",
        threshold=0.5,
    )
    assert "demographic_parity" in report
    assert "equal_opportunity" in report


def test_fairness_over_thresholds(evaluator, fairness_df):
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    results = evaluator.calculate_fairness_across_thresholds(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        thresholds=thresholds,
    )
    assert "demographic_parity" in results
    assert "equal_opportunity" in results
    assert "equalized_odds" in results
    for t in thresholds:
        assert t in results["demographic_parity"]
        assert t in results["equal_opportunity"]
        assert t in results["equalized_odds"]

    fig = evaluator.plot_fairness_across_thresholds(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        thresholds=thresholds,
    )
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_fairness_with_reweighting(evaluator, fairness_df):
    result = evaluator.improve_fairness_with_reweighting(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        fairness_metric="demographic_parity",
    )
    assert "weights" in result
    assert "fairness_before" in result
    assert "fairness_after" in result
    assert result["fairness_after"] < result["fairness_before"]


def test_adversarial_debiasing(evaluator, fairness_df):
    X = fairness_df[["age"]].values
    y = fairness_df["true_outcome"].values
    sensitive = pd.get_dummies(fairness_df["gender"]).values
    result = evaluator.mock_adversarial_debiasing(
        X, y, sensitive, fairness_metric="demographic_parity"
    )
    assert "original_predictions" in result
    assert "debiased_predictions" in result
    assert "fairness_improvement" in result
    assert len(result["original_predictions"]) == len(fairness_df)
    assert len(result["debiased_predictions"]) == len(fairness_df)


def test_cross_validation_fairness(evaluator, fairness_df):
    cv_results = evaluator.cross_validate_fairness(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        cv=3,
        threshold=0.5,
    )
    assert "demographic_parity" in cv_results
    assert "equal_opportunity" in cv_results
    assert "equalized_odds" in cv_results
    assert "fold_results" in cv_results
    assert len(cv_results["fold_results"]) == 3
    for fold in cv_results["fold_results"]:
        assert "demographic_parity" in fold
        assert "equal_opportunity" in fold
        assert "equalized_odds" in fold


def test_integration_with_healthcare_metrics(evaluator, metrics, fairness_df):
    fairness_report = evaluator.generate_fairness_report(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        threshold=0.5,
    )
    for gender in ["M", "F"]:
        gender_df = fairness_df[fairness_df["gender"] == gender]
        eval_result = metrics.evaluate_clinical_model(
            gender_df, outcome_column="true_outcome", prediction_column="prediction"
        )
        # AUC from both should be close
        assert abs(fairness_report["auc_by_group"][gender] - eval_result["auc"]) < 1e-4


def test_fairness_report_export(evaluator, fairness_df, tmp_path):
    report = evaluator.generate_fairness_report(
        fairness_df,
        prediction_column="prediction",
        outcome_column="true_outcome",
        group_column="gender",
        threshold=0.5,
    )
    json_path = str(tmp_path / "fairness_report.json")
    evaluator.export_fairness_report(report, json_path)
    assert os.path.exists(json_path)
