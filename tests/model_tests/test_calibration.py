import os
import sys
import unittest
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.model_factory.model_calibration import ModelCalibrator
from src.utils.healthcare_metrics import HealthcareMetrics


class TestCalibration(unittest.TestCase):
    """Test suite for model calibration functionality."""

    def setUp(self) -> Any:
        """Set up test fixtures."""
        np.random.seed(42)
        n_samples = 1000
        self.y_true = np.random.binomial(1, 0.3, size=n_samples)
        raw_pred = np.random.normal(0.3, 0.2, size=n_samples)
        self.y_pred_uncalibrated = np.clip(raw_pred, 0.01, 0.99)
        self.y_pred_severe = np.power(self.y_pred_uncalibrated, 0.5)
        self.patient_ids = [f"P{i:04d}" for i in range(n_samples)]
        self.ages = np.random.normal(65, 15, size=n_samples).astype(int)
        self.genders = np.random.choice(["M", "F"], size=n_samples)
        self.df = pd.DataFrame(
            {
                "patient_id": self.patient_ids,
                "age": self.ages,
                "gender": self.genders,
                "true_outcome": self.y_true,
                "prediction_uncalibrated": self.y_pred_uncalibrated,
                "prediction_severe": self.y_pred_severe,
            }
        )
        self.calibrator = ModelCalibrator()
        self.metrics = HealthcareMetrics()

    def test_calibration_curve(self) -> Any:
        """Test calibration curve calculation."""
        prob_true, prob_pred = calibration_curve(
            self.y_true, self.y_pred_uncalibrated, n_bins=10
        )
        self.assertEqual(len(prob_true), 10)
        self.assertEqual(len(prob_pred), 10)
        self.assertTrue(np.all(prob_true >= 0) and np.all(prob_true <= 1))
        self.assertTrue(np.all(prob_pred >= 0) and np.all(prob_pred <= 1))

    def test_brier_score(self) -> Any:
        """Test Brier score calculation."""
        brier = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        self.assertTrue(0 <= brier <= 1)
        brier_severe = brier_score_loss(self.y_true, self.y_pred_severe)
        self.assertGreater(brier_severe, brier)

    def test_isotonic_calibration(self) -> Any:
        """Test isotonic regression calibration."""
        calibrated_pred = self.calibrator.calibrate(
            self.y_pred_uncalibrated, self.y_true, method="isotonic"
        )
        self.assertEqual(len(calibrated_pred), len(self.y_pred_uncalibrated))
        self.assertTrue(np.all(calibrated_pred >= 0) and np.all(calibrated_pred <= 1))
        brier_before = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        brier_after = brier_score_loss(self.y_true, calibrated_pred)
        self.assertLessEqual(brier_after, brier_before * 1.05)

    def test_platt_scaling(self) -> Any:
        """Test Platt scaling calibration."""
        calibrated_pred = self.calibrator.calibrate(
            self.y_pred_uncalibrated, self.y_true, method="platt"
        )
        self.assertEqual(len(calibrated_pred), len(self.y_pred_uncalibrated))
        self.assertTrue(np.all(calibrated_pred >= 0) and np.all(calibrated_pred <= 1))
        brier_before = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        brier_after = brier_score_loss(self.y_true, calibrated_pred)
        self.assertLessEqual(brier_after, brier_before * 1.05)

    def test_beta_calibration(self) -> Any:
        """Test Beta calibration."""
        calibrated_pred = self.calibrator.calibrate(
            self.y_pred_uncalibrated, self.y_true, method="beta"
        )
        self.assertEqual(len(calibrated_pred), len(self.y_pred_uncalibrated))
        self.assertTrue(np.all(calibrated_pred >= 0) and np.all(calibrated_pred <= 1))
        brier_before = brier_score_loss(self.y_true, self.y_pred_uncalibrated)
        brier_after = brier_score_loss(self.y_true, calibrated_pred)
        self.assertLessEqual(brier_after, brier_before * 1.05)

    def test_calibration_by_group(self) -> Any:
        """Test calibration by demographic group."""
        df_male = self.df[self.df["gender"] == "M"]
        df_female = self.df[self.df["gender"] == "F"]
        result = self.calibrator.calculate_calibration_by_group(
            self.df,
            prediction_column="prediction_uncalibrated",
            outcome_column="true_outcome",
            group_column="gender",
        )
        self.assertIn("M", result)
        self.assertIn("F", result)
        self.assertIn("prob_true", result["M"])
        self.assertIn("prob_pred", result["M"])
        self.assertIn("prob_true", result["F"])
        self.assertIn("prob_pred", result["F"])
        self.assertTrue(
            np.all(result["M"]["prob_true"] >= 0)
            and np.all(result["M"]["prob_true"] <= 1)
        )
        self.assertTrue(
            np.all(result["M"]["prob_pred"] >= 0)
            and np.all(result["M"]["prob_pred"] <= 1)
        )
        self.assertTrue(
            np.all(result["F"]["prob_true"] >= 0)
            and np.all(result["F"]["prob_true"] <= 1)
        )
        self.assertTrue(
            np.all(result["F"]["prob_pred"] >= 0)
            and np.all(result["F"]["prob_pred"] <= 1)
        )

    def test_calibration_metrics(self) -> Any:
        """Test calibration metrics calculation."""
        metrics = self.calibrator.calculate_calibration_metrics(
            self.y_true, self.y_pred_uncalibrated
        )
        self.assertIn("brier_score", metrics)
        self.assertIn("expected_calibration_error", metrics)
        self.assertIn("maximum_calibration_error", metrics)
        self.assertIn("calibration_slope", metrics)
        self.assertIn("calibration_intercept", metrics)
        self.assertTrue(0 <= metrics["brier_score"] <= 1)
        self.assertTrue(0 <= metrics["expected_calibration_error"] <= 1)
        self.assertTrue(0 <= metrics["maximum_calibration_error"] <= 1)
        metrics_severe = self.calibrator.calculate_calibration_metrics(
            self.y_true, self.y_pred_severe
        )
        self.assertGreater(metrics_severe["brier_score"], metrics["brier_score"])
        self.assertGreater(
            metrics_severe["expected_calibration_error"],
            metrics["expected_calibration_error"],
        )

    def test_calibration_plot(self) -> Any:
        """Test calibration plot generation."""
        fig = self.calibrator.plot_calibration_curve(
            self.y_true, self.y_pred_uncalibrated, title="Calibration Test"
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertEqual(len(fig.axes), 1)
        plt.close(fig)

    def test_group_calibration_plot(self) -> Any:
        """Test group calibration plot generation."""
        fig = self.calibrator.plot_calibration_by_group(
            self.df,
            prediction_column="prediction_uncalibrated",
            outcome_column="true_outcome",
            group_column="gender",
            title="Group Calibration Test",
        )
        self.assertIsInstance(fig, plt.Figure)
        self.assertEqual(len(fig.axes), 1)
        plt.close(fig)

    def test_calibration_comparison(self) -> Any:
        """Test comparison of calibration methods."""
        result = self.calibrator.compare_calibration_methods(
            self.y_pred_uncalibrated, self.y_true, methods=["isotonic", "platt", "beta"]
        )
        self.assertIn("uncalibrated", result)
        self.assertIn("isotonic", result)
        self.assertIn("platt", result)
        self.assertIn("beta", result)
        for method in ["uncalibrated", "isotonic", "platt", "beta"]:
            self.assertIn("brier_score", result[method])
            self.assertIn("expected_calibration_error", result[method])
            self.assertIn("predictions", result[method])
        for method in ["uncalibrated", "isotonic", "platt", "beta"]:
            self.assertEqual(len(result[method]["predictions"]), len(self.y_true))
        fig = self.calibrator.plot_calibration_comparison(
            self.y_pred_uncalibrated,
            self.y_true,
            methods=["isotonic", "platt", "beta"],
            title="Calibration Comparison",
        )
        self.assertIsInstance(fig, plt.Figure)
        plt.close(fig)

    def test_cross_validation_calibration(self) -> Any:
        """Test cross-validation for calibration."""
        cv_result = self.calibrator.cross_validate_calibration(
            self.y_pred_uncalibrated, self.y_true, method="isotonic", cv=3
        )
        self.assertIn("calibrated_predictions", cv_result)
        self.assertIn("fold_metrics", cv_result)
        self.assertIn("mean_brier_score", cv_result)
        self.assertIn("std_brier_score", cv_result)
        self.assertEqual(len(cv_result["calibrated_predictions"]), len(self.y_true))
        self.assertEqual(len(cv_result["fold_metrics"]), 3)
        for fold_metric in cv_result["fold_metrics"]:
            self.assertIn("brier_score", fold_metric)
            self.assertIn("expected_calibration_error", fold_metric)

    def test_integration_with_healthcare_metrics(self) -> Any:
        """Test integration with healthcare metrics."""
        df_clinical = self.df.copy()
        df_clinical["mortality"] = self.y_true
        df_clinical["predicted_mortality"] = self.y_pred_uncalibrated
        calibration_metrics = self.calibrator.calculate_calibration_metrics(
            df_clinical["mortality"], df_clinical["predicted_mortality"]
        )
        clinical_eval = self.metrics.evaluate_clinical_model(
            df_clinical,
            outcome_column="mortality",
            prediction_column="predicted_mortality",
        )
        self.assertAlmostEqual(
            calibration_metrics["brier_score"], clinical_eval["brier_score"], places=4
        )
        self.assertAlmostEqual(
            calibration_metrics["calibration_slope"],
            clinical_eval["calibration_slope"],
            places=4,
        )
        self.assertAlmostEqual(
            calibration_metrics["calibration_intercept"],
            clinical_eval["calibration_intercept"],
            places=4,
        )

    def test_save_and_load_calibrator(self) -> Any:
        """Test saving and loading calibrator models."""
        self.calibrator.fit(self.y_pred_uncalibrated, self.y_true, method="isotonic")
        save_path = "test_calibrator.pkl"
        self.calibrator.save(save_path)
        self.assertTrue(os.path.exists(save_path))
        loaded_calibrator = ModelCalibrator.load(save_path)
        original_pred = self.calibrator.transform(self.y_pred_uncalibrated)
        loaded_pred = loaded_calibrator.transform(self.y_pred_uncalibrated)
        np.testing.assert_array_almost_equal(original_pred, loaded_pred)
        os.remove(save_path)

    def test_recalibration_over_time(self) -> Any:
        """Test recalibration over time simulation."""
        np.random.seed(42)
        n_samples = 1000
        y_true_period1 = np.random.binomial(1, 0.3, size=n_samples)
        y_pred_period1 = np.random.normal(0.3, 0.2, size=n_samples)
        y_pred_period1 = np.clip(y_pred_period1, 0.01, 0.99)
        y_true_period2 = np.random.binomial(1, 0.4, size=n_samples)
        y_pred_period2 = np.random.normal(0.3, 0.2, size=n_samples)
        y_pred_period2 = np.clip(y_pred_period2, 0.01, 0.99)
        df_period1 = pd.DataFrame(
            {"true_outcome": y_true_period1, "prediction": y_pred_period1, "period": 1}
        )
        df_period2 = pd.DataFrame(
            {"true_outcome": y_true_period2, "prediction": y_pred_period2, "period": 2}
        )
        df_combined = pd.concat([df_period1, df_period2])
        drift_result = self.calibrator.detect_calibration_drift(
            df_combined,
            prediction_column="prediction",
            outcome_column="true_outcome",
            time_column="period",
        )
        self.assertIn("drift_detected", drift_result)
        self.assertIn("period_metrics", drift_result)
        self.assertIn(1, drift_result["period_metrics"])
        self.assertIn(2, drift_result["period_metrics"])
        self.assertGreater(
            drift_result["period_metrics"][2]["brier_score"],
            drift_result["period_metrics"][1]["brier_score"],
        )
        recal_result = self.calibrator.recalibrate_by_period(
            df_combined,
            prediction_column="prediction",
            outcome_column="true_outcome",
            time_column="period",
            reference_period=1,
            target_period=2,
            method="isotonic",
        )
        self.assertLess(
            recal_result["after"]["brier_score"], recal_result["before"]["brier_score"]
        )


if __name__ == "__main__":
    unittest.main()
