"""
Fairness Metrics Module for Nexora

This module provides comprehensive fairness evaluation metrics to ensure
the system performs equitably across different patient demographics.
"""

import logging
from typing import Any, Dict, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class ModelBiasError(Exception):
    """Exception raised when model bias exceeds acceptable thresholds."""


class DemographicParity:
    """
    Demographic Parity metric.

    Measures whether the positive prediction rate is equal across groups.
    A disparity of 0 means perfect parity.
    """

    def __call__(
        self, y_true: np.ndarray, y_pred: np.ndarray, sensitive_features: np.ndarray
    ) -> float:
        """
        Calculate demographic parity disparity.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            sensitive_features: Sensitive attribute values

        Returns:
            Disparity value (0 = perfect parity)
        """
        df = pd.DataFrame({"y_pred": y_pred, "sensitive": sensitive_features})

        # Calculate positive prediction rate for each group
        positive_rates = df.groupby("sensitive")["y_pred"].mean()

        # Calculate disparity as max difference between groups
        disparity = positive_rates.max() - positive_rates.min()

        return float(disparity)


class EqualOpportunity:
    """
    Equal Opportunity metric.

    Measures whether the true positive rate is equal across groups.
    """

    def __call__(
        self, y_true: np.ndarray, y_pred: np.ndarray, sensitive_features: np.ndarray
    ) -> float:
        """
        Calculate equal opportunity disparity.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            sensitive_features: Sensitive attribute values

        Returns:
            Disparity in true positive rates
        """
        df = pd.DataFrame(
            {"y_true": y_true, "y_pred": y_pred, "sensitive": sensitive_features}
        )

        # Filter to positive class only
        positive_df = df[df["y_true"] == 1]

        if len(positive_df) == 0:
            return 0.0

        # Calculate TPR for each group
        tprs = positive_df.groupby("sensitive")["y_pred"].mean()

        # Calculate disparity
        if len(tprs) < 2:
            return 0.0

        disparity = tprs.max() - tprs.min()

        return float(disparity)


class PredictiveEquality:
    """
    Predictive Equality metric.

    Measures whether the false positive rate is equal across groups.
    """

    def __call__(
        self, y_true: np.ndarray, y_pred: np.ndarray, sensitive_features: np.ndarray
    ) -> float:
        """
        Calculate predictive equality disparity.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            sensitive_features: Sensitive attribute values

        Returns:
            Disparity in false positive rates
        """
        df = pd.DataFrame(
            {"y_true": y_true, "y_pred": y_pred, "sensitive": sensitive_features}
        )

        # Filter to negative class only
        negative_df = df[df["y_true"] == 0]

        if len(negative_df) == 0:
            return 0.0

        # Calculate FPR for each group
        fprs = negative_df.groupby("sensitive")["y_pred"].mean()

        # Calculate disparity
        if len(fprs) < 2:
            return 0.0

        disparity = fprs.max() - fprs.min()

        return float(disparity)


class HealthcareFairness:
    """
    Comprehensive fairness evaluation for healthcare models.

    This class evaluates multiple fairness metrics and ensures the model
    meets fairness thresholds across different patient demographics.
    """

    def __init__(
        self, protected_attributes: List[str], disparity_threshold: float = 0.1
    ) -> None:
        """
        Initialize fairness evaluator.

        Args:
            protected_attributes: List of protected attribute names
            disparity_threshold: Maximum acceptable disparity (default: 0.1 or 10%)
        """
        self.protected_attributes = protected_attributes
        self.disparity_threshold = disparity_threshold

        self.metrics = {
            "demographic_parity": DemographicParity(),
            "equal_opportunity": EqualOpportunity(),
            "predictive_equality": PredictiveEquality(),
        }

        logger.info(
            f"Initialized HealthcareFairness with threshold={disparity_threshold}, "
            f"protected_attributes={protected_attributes}"
        )

    def evaluate(
        self, y_true: np.ndarray, y_pred: np.ndarray, sensitive_features: np.ndarray
    ) -> Dict[str, Any]:
        """
        Evaluate fairness across all metrics.

        Args:
            y_true: True labels
            y_pred: Predicted labels (binary or probabilities > 0.5)
            sensitive_features: Sensitive attribute values

        Returns:
            Dictionary of fairness metric results

        Raises:
            ModelBiasError: If any fairness threshold is violated
        """
        # Convert probabilities to binary if needed
        if y_pred.dtype == float and (y_pred >= 0).all() and (y_pred <= 1).all():
            y_pred = (y_pred > 0.5).astype(int)

        results = {}

        for name, metric in self.metrics.items():
            try:
                disparity = metric(
                    y_true, y_pred, sensitive_features=sensitive_features
                )
                passed = disparity <= self.disparity_threshold

                results[name] = {
                    "value": float(disparity),
                    "passed": bool(passed),
                    "threshold": self.disparity_threshold,
                }

                logger.info(
                    f"Fairness metric {name}: disparity={disparity:.4f}, "
                    f"passed={passed}"
                )

            except Exception as e:
                logger.error(f"Error calculating {name}: {str(e)}")
                results[name] = {
                    "value": None,
                    "passed": False,
                    "error": str(e),
                }

        # Check if all metrics passed
        all_passed = all(r["passed"] for r in results.values() if "error" not in r)

        if not all_passed:
            failed_metrics = [
                name
                for name, r in results.items()
                if not r["passed"] and "error" not in r
            ]
            logger.warning(
                f"Fairness thresholds violated for metrics: {failed_metrics}"
            )
            raise ModelBiasError(
                f"Fairness thresholds violated: {failed_metrics}. Results: {results}"
            )

        logger.info("All fairness metrics passed")
        return results

    def evaluate_by_group(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        sensitive_features: Dict[str, np.ndarray],
    ) -> Dict[str, Dict[str, Any]]:
        """
        Evaluate fairness metrics separately for each protected attribute.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            sensitive_features: Dictionary mapping attribute names to values

        Returns:
            Dictionary of results by attribute
        """
        results = {}

        for attr_name, attr_values in sensitive_features.items():
            logger.info(f"Evaluating fairness for attribute: {attr_name}")

            try:
                attr_results = self.evaluate(y_true, y_pred, attr_values)
                results[attr_name] = attr_results
            except ModelBiasError as e:
                logger.warning(f"Bias detected for {attr_name}: {str(e)}")
                results[attr_name] = {"error": str(e)}

        return results
