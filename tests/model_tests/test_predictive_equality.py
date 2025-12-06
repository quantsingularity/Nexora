import os
import sys
import unittest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.model_factory.fairness_metrics import FairnessEvaluator
from src.utils.healthcare_metrics import HealthcareMetrics


class TestPredictiveEquality(unittest.TestCase):
    """Test suite for predictive equality and fairness functionality."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        np.random.seed(42)
        n_samples = 1000
        self.y_true = np.random.binomial(1, 0.3, size=n_samples)
        self.patient_ids = [f"P{i:04d}" for i in range(n_samples)]
        self.ages = np.random.normal(65, 15, size=n_samples).astype(int)
        self.genders = np.random.choice(["M", "F"], size=n_samples, p=[0.6, 0.4])
        self.races = np.random.choice(
            ["White", "Black", "Hispanic", "Asian", "Other"],
            size=n_samples,
            p=[0.6, 0.15, 0.15, 0.05, 0.05],
        )
        self.insurance = np.random.choice(
            ["Private", "Medicare", "Medicaid", "Uninsured"],
            size=n_samples,
            p=[0.5, 0.3, 0.15, 0.05],
        )
        male_idx = self.genders == "M"
        female_idx = self.genders == "F"
        self.y_pred = np.random.normal(0.3, 0.2, size=n_samples)
        self.y_pred = np.clip(self.y_pred, 0.01, 0.99)
        female_with_condition = female_idx & (self.y_true == 1)
        self.y_pred[female_with_condition] = self.y_pred[female_with_condition] * 0.7
        black_idx = self.races == "Black"
        black_with_condition = black_idx & (self.y_true == 1)
        self.y_pred[black_with_condition] = self.y_pred[black_with_condition] * 0.7
        medicaid_idx = self.insurance == "Medicaid"
        self.y_pred[medicaid_idx] = (
            np.abs(self.y_pred[medicaid_idx] - self.y_true[medicaid_idx]) * 0.8
            + self.y_pred[medicaid_idx] * 0.2
        )
        self.df = pd.DataFrame(
            {
                "patient_id": self.patient_ids,
                "age": self.ages,
                "gender": self.genders,
                "race": self.races,
                "insurance": self.insurance,
                "true_outcome": self.y_true,
                "prediction": self.y_pred,
            }
        )
        self.df["age_group"] = pd.cut(
            self.df["age"],
            bins=[0, 18, 35, 50, 65, 80, 120],
            labels=["0-18", "19-35", "36-50", "51-65", "66-80", "80+"],
        )
        self.evaluator = FairnessEvaluator()
        self.metrics = HealthcareMetrics()

    def test_demographic_parity(self) -> Any:
        """Test demographic parity calculation."""
        dp_gender = self.evaluator.calculate_demographic_parity(
            self.df,
            prediction_column="prediction",
            group_column="gender",
            threshold=0.5,
        )
        self.assertIn("demographic_parity", dp_gender)
        self.assertIn("positive_rates", dp_gender)
        self.assertIn("M", dp_gender["positive_rates"])
        self.assertIn("F", dp_gender["positive_rates"])
        dp_race = self.evaluator.calculate_demographic_parity(
            self.df, prediction_column="prediction", group_column="race", threshold=0.5
        )
        self.assertIn("demographic_parity", dp_race)
        self.assertIn("positive_rates", dp_race)
        for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
            self.assertIn(race, dp_race["positive_rates"])

    def test_equal_opportunity(self) -> Any:
        """Test equal opportunity calculation."""
        eo_gender = self.evaluator.calculate_equal_opportunity(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            threshold=0.5,
        )
        self.assertIn("equal_opportunity", eo_gender)
        self.assertIn("true_positive_rates", eo_gender)
        self.assertIn("M", eo_gender["true_positive_rates"])
        self.assertIn("F", eo_gender["true_positive_rates"])
        self.assertLess(
            eo_gender["true_positive_rates"]["F"], eo_gender["true_positive_rates"]["M"]
        )
        eo_race = self.evaluator.calculate_equal_opportunity(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="race",
            threshold=0.5,
        )
        self.assertIn("equal_opportunity", eo_race)
        self.assertIn("true_positive_rates", eo_race)
        for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
            self.assertIn(race, eo_race["true_positive_rates"])
        self.assertLess(
            eo_race["true_positive_rates"]["Black"],
            eo_race["true_positive_rates"]["White"],
        )

    def test_equalized_odds(self) -> Any:
        """Test equalized odds calculation."""
        eodds_gender = self.evaluator.calculate_equalized_odds(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            threshold=0.5,
        )
        self.assertIn("equalized_odds", eodds_gender)
        self.assertIn("true_positive_rates", eodds_gender)
        self.assertIn("false_positive_rates", eodds_gender)
        self.assertIn("M", eodds_gender["true_positive_rates"])
        self.assertIn("F", eodds_gender["true_positive_rates"])
        self.assertIn("M", eodds_gender["false_positive_rates"])
        self.assertIn("F", eodds_gender["false_positive_rates"])
        eodds_race = self.evaluator.calculate_equalized_odds(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="race",
            threshold=0.5,
        )
        self.assertIn("equalized_odds", eodds_race)
        self.assertIn("true_positive_rates", eodds_race)
        self.assertIn("false_positive_rates", eodds_race)
        for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
            self.assertIn(race, eodds_race["true_positive_rates"])
            self.assertIn(race, eodds_race["false_positive_rates"])

    def test_predictive_parity(self) -> Any:
        """Test predictive parity calculation."""
        pp_gender = self.evaluator.calculate_predictive_parity(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            threshold=0.5,
        )
        self.assertIn("predictive_parity", pp_gender)
        self.assertIn("positive_predictive_values", pp_gender)
        self.assertIn("M", pp_gender["positive_predictive_values"])
        self.assertIn("F", pp_gender["positive_predictive_values"])
        pp_race = self.evaluator.calculate_predictive_parity(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="race",
            threshold=0.5,
        )
        self.assertIn("predictive_parity", pp_race)
        self.assertIn("positive_predictive_values", pp_race)
        for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
            self.assertIn(race, pp_race["positive_predictive_values"])

    def test_calibration_by_group(self) -> Any:
        """Test calibration by group calculation."""
        cal_gender = self.evaluator.calculate_calibration_by_group(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIn("calibration_by_group", cal_gender)
        self.assertIn("brier_scores", cal_gender)
        self.assertIn("M", cal_gender["brier_scores"])
        self.assertIn("F", cal_gender["brier_scores"])
        self.assertGreater(
            cal_gender["brier_scores"]["F"], cal_gender["brier_scores"]["M"]
        )
        cal_race = self.evaluator.calculate_calibration_by_group(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="race",
        )
        self.assertIn("calibration_by_group", cal_race)
        self.assertIn("brier_scores", cal_race)
        for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
            self.assertIn(race, cal_race["brier_scores"])
        self.assertGreater(
            cal_race["brier_scores"]["Black"], cal_race["brier_scores"]["White"]
        )

    def test_auc_by_group(self) -> Any:
        """Test AUC by group calculation."""
        auc_gender = self.evaluator.calculate_auc_by_group(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIn("auc_by_group", auc_gender)
        self.assertIn("M", auc_gender["auc_by_group"])
        self.assertIn("F", auc_gender["auc_by_group"])
        auc_race = self.evaluator.calculate_auc_by_group(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="race",
        )
        self.assertIn("auc_by_group", auc_race)
        for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
            self.assertIn(race, auc_race["auc_by_group"])

    def test_fairness_metrics_report(self) -> Any:
        """Test comprehensive fairness metrics report."""
        report_gender = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            threshold=0.5,
        )
        self.assertIn("demographic_parity", report_gender)
        self.assertIn("equal_opportunity", report_gender)
        self.assertIn("equalized_odds", report_gender)
        self.assertIn("predictive_parity", report_gender)
        self.assertIn("calibration_by_group", report_gender)
        self.assertIn("auc_by_group", report_gender)
        report_race = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="race",
            threshold=0.5,
        )
        self.assertIn("demographic_parity", report_race)
        self.assertIn("equal_opportunity", report_race)
        self.assertIn("equalized_odds", report_race)
        self.assertIn("predictive_parity", report_race)
        self.assertIn("calibration_by_group", report_race)
        self.assertIn("auc_by_group", report_race)

    def test_fairness_plots(self) -> Any:
        """Test fairness visualization plots."""
        fig_roc = self.evaluator.plot_roc_curves_by_group(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIsInstance(fig_roc, plt.Figure)
        fig_pr = self.evaluator.plot_precision_recall_curves_by_group(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIsInstance(fig_pr, plt.Figure)
        fig_cal = self.evaluator.plot_calibration_curves_by_group(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIsInstance(fig_cal, plt.Figure)
        fig_metrics = self.evaluator.plot_fairness_metrics_comparison(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_columns=["gender", "race", "insurance"],
            threshold=0.5,
        )
        self.assertIsInstance(fig_metrics, plt.Figure)
        plt.close("all")

    def test_threshold_optimization(self) -> Any:
        """Test threshold optimization for fairness."""
        opt_result = self.evaluator.optimize_thresholds_for_equal_opportunity(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIn("optimized_thresholds", opt_result)
        self.assertIn("M", opt_result["optimized_thresholds"])
        self.assertIn("F", opt_result["optimized_thresholds"])
        self.assertIn("equal_opportunity_before", opt_result)
        self.assertIn("equal_opportunity_after", opt_result)
        self.assertLess(
            opt_result["equal_opportunity_after"],
            opt_result["equal_opportunity_before"],
        )
        opt_result = self.evaluator.optimize_thresholds_for_equalized_odds(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIn("optimized_thresholds", opt_result)
        self.assertIn("M", opt_result["optimized_thresholds"])
        self.assertIn("F", opt_result["optimized_thresholds"])
        self.assertIn("equalized_odds_before", opt_result)
        self.assertIn("equalized_odds_after", opt_result)
        self.assertLess(
            opt_result["equalized_odds_after"], opt_result["equalized_odds_before"]
        )

    def test_intersectional_fairness(self) -> Any:
        """Test intersectional fairness analysis."""
        self.df["gender_race"] = self.df["gender"] + "_" + self.df["race"]
        report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender_race",
            threshold=0.5,
        )
        self.assertIn("demographic_parity", report)
        self.assertIn("equal_opportunity", report)
        self.assertIn("equalized_odds", report)
        self.assertIn("predictive_parity", report)
        for gender in ["M", "F"]:
            for race in ["White", "Black", "Hispanic", "Asian", "Other"]:
                intersectional_group = f"{gender}_{race}"
                if (
                    intersectional_group
                    in report["demographic_parity"]["positive_rates"]
                ):
                    self.assertIn(
                        intersectional_group,
                        report["demographic_parity"]["positive_rates"],
                    )

    def test_fairness_over_thresholds(self) -> Any:
        """Test fairness metrics across different thresholds."""
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        threshold_results = self.evaluator.calculate_fairness_across_thresholds(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            thresholds=thresholds,
        )
        self.assertIn("demographic_parity", threshold_results)
        self.assertIn("equal_opportunity", threshold_results)
        self.assertIn("equalized_odds", threshold_results)
        for threshold in thresholds:
            self.assertIn(threshold, threshold_results["demographic_parity"])
            self.assertIn(threshold, threshold_results["equal_opportunity"])
            self.assertIn(threshold, threshold_results["equalized_odds"])
        fig = self.evaluator.plot_fairness_across_thresholds(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            thresholds=thresholds,
        )
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)

    def test_fairness_with_reweighting(self) -> Any:
        """Test fairness improvement with instance reweighting."""
        before_report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            threshold=0.5,
        )
        reweighted_result = self.evaluator.improve_fairness_with_reweighting(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            fairness_metric="demographic_parity",
        )
        self.assertIn("weights", reweighted_result)
        self.assertIn("fairness_before", reweighted_result)
        self.assertIn("fairness_after", reweighted_result)
        self.assertLess(
            reweighted_result["fairness_after"], reweighted_result["fairness_before"]
        )

    def test_fairness_with_adversarial_debiasing(self) -> Any:
        """Test fairness improvement with adversarial debiasing simulation."""
        X = self.df[["age"]].values
        y = self.df["true_outcome"].values
        sensitive_features = pd.get_dummies(self.df["gender"]).values
        mock_result = self.evaluator.mock_adversarial_debiasing(
            X, y, sensitive_features, fairness_metric="demographic_parity"
        )
        self.assertIn("original_predictions", mock_result)
        self.assertIn("debiased_predictions", mock_result)
        self.assertIn("fairness_improvement", mock_result)
        self.assertEqual(len(mock_result["original_predictions"]), len(self.df))
        self.assertEqual(len(mock_result["debiased_predictions"]), len(self.df))

    def test_integration_with_healthcare_metrics(self) -> Any:
        """Test integration with healthcare metrics."""
        fairness_report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            threshold=0.5,
        )
        healthcare_report = {}
        for gender in ["M", "F"]:
            gender_df = self.df[self.df["gender"] == gender]
            eval_result = self.metrics.evaluate_clinical_model(
                gender_df, outcome_column="true_outcome", prediction_column="prediction"
            )
            healthcare_report[gender] = eval_result
        for gender in ["M", "F"]:
            self.assertAlmostEqual(
                fairness_report["auc_by_group"][gender],
                healthcare_report[gender]["auc"],
                places=4,
            )

    def test_fairness_report_export(self) -> Any:
        """Test exporting fairness report to file."""
        report = self.evaluator.generate_fairness_report(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            threshold=0.5,
        )
        json_path = "fairness_report.json"
        self.evaluator.export_fairness_report(report, json_path)
        self.assertTrue(os.path.exists(json_path))
        os.remove(json_path)

    def test_cross_validation_fairness(self) -> Any:
        """Test fairness metrics with cross-validation."""
        cv_results = self.evaluator.cross_validate_fairness(
            self.df,
            prediction_column="prediction",
            outcome_column="true_outcome",
            group_column="gender",
            cv=3,
            threshold=0.5,
        )
        self.assertIn("demographic_parity", cv_results)
        self.assertIn("equal_opportunity", cv_results)
        self.assertIn("equalized_odds", cv_results)
        self.assertIn("fold_results", cv_results)
        self.assertEqual(len(cv_results["fold_results"]), 3)
        for fold_result in cv_results["fold_results"]:
            self.assertIn("demographic_parity", fold_result)
            self.assertIn("equal_opportunity", fold_result)
            self.assertIn("equalized_odds", fold_result)


if __name__ == "__main__":
    unittest.main()
