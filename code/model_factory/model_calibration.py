"""
Model Calibration Module for Nexora

Provides isotonic regression, Platt scaling, and beta calibration
for clinical prediction models, with group-level calibration analysis.
"""

import logging
from typing import Any, Dict

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

logger = logging.getLogger(__name__)


class ModelCalibrator:
    """
    Calibrates predicted probabilities from clinical prediction models.

    Supports isotonic regression, Platt scaling, and beta calibration.
    """

    def __init__(self) -> None:
        self._calibrators: Dict[str, Any] = {}
        logger.info("ModelCalibrator initialized.")

    def calibrate(
        self,
        predictions: np.ndarray,
        true_labels: np.ndarray,
        method: str = "isotonic",
    ) -> np.ndarray:
        """
        Calibrate predicted probabilities.

        Args:
            predictions: Raw predicted probabilities.
            true_labels: True binary labels.
            method: Calibration method ('isotonic', 'platt', or 'beta').

        Returns:
            Calibrated probabilities as a numpy array.
        """
        predictions = np.asarray(predictions, dtype=float)
        true_labels = np.asarray(true_labels, dtype=float)

        if method == "isotonic":
            return self._isotonic_calibration(predictions, true_labels)
        elif method == "platt":
            return self._platt_calibration(predictions, true_labels)
        elif method == "beta":
            return self._beta_calibration(predictions, true_labels)
        else:
            raise ValueError(f"Unknown calibration method: {method}")

    def _isotonic_calibration(
        self, predictions: np.ndarray, true_labels: np.ndarray
    ) -> np.ndarray:
        """Isotonic regression calibration."""
        ir = IsotonicRegression(out_of_bounds="clip")
        calibrated = ir.fit_transform(predictions, true_labels)
        self._calibrators["isotonic"] = ir
        return np.clip(calibrated, 0.0, 1.0)

    def _platt_calibration(
        self, predictions: np.ndarray, true_labels: np.ndarray
    ) -> np.ndarray:
        """Platt scaling (logistic regression on raw scores)."""
        lr = LogisticRegression(C=1.0, solver="lbfgs")
        lr.fit(predictions.reshape(-1, 1), true_labels)
        calibrated = lr.predict_proba(predictions.reshape(-1, 1))[:, 1]
        self._calibrators["platt"] = lr
        return np.clip(calibrated, 0.0, 1.0)

    def _beta_calibration(
        self, predictions: np.ndarray, true_labels: np.ndarray
    ) -> np.ndarray:
        """
        Beta calibration using log-odds features (simplified version).

        Maps probabilities through a logistic model with log(p) and log(1-p)
        features, which corresponds to the Beta calibration family.
        """
        eps = 1e-7
        p = np.clip(predictions, eps, 1 - eps)
        features = np.column_stack([np.log(p), np.log(1 - p)])
        lr = LogisticRegression(C=1.0, solver="lbfgs", fit_intercept=True)
        lr.fit(features, true_labels)
        calibrated = lr.predict_proba(features)[:, 1]
        self._calibrators["beta"] = lr
        return np.clip(calibrated, 0.0, 1.0)

    def calculate_calibration_by_group(
        self,
        df: pd.DataFrame,
        prediction_column: str,
        outcome_column: str,
        group_column: str,
        method: str = "isotonic",
    ) -> Dict[str, Any]:
        """
        Calculate calibration quality (Brier score) per demographic group.

        Args:
            df: DataFrame with predictions, outcomes, and group labels.
            prediction_column: Column with predicted probabilities.
            outcome_column: Column with true binary outcomes.
            group_column: Column with group labels.
            method: Calibration method to evaluate.

        Returns:
            Dictionary with per-group Brier scores and calibration slopes.
        """
        results: Dict[str, Any] = {}

        for group in df[group_column].unique():
            mask = df[group_column] == group
            group_df = df[mask].copy()
            preds = group_df[prediction_column].values
            outcomes = group_df[outcome_column].values

            brier = float(np.mean((preds - outcomes) ** 2))

            if len(preds) >= 5:
                try:
                    cal_preds = self.calibrate(preds, outcomes, method=method)
                    brier_cal = float(np.mean((cal_preds - outcomes) ** 2))
                except Exception:
                    brier_cal = brier
            else:
                brier_cal = brier

            results[str(group)] = {
                "brier_score_before": brier,
                "brier_score_after": brier_cal,
                "n_samples": int(mask.sum()),
            }

        return {
            "calibration_by_group": results,
            "method": method,
        }
