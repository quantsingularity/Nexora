"""
Concept Drift Detection Module for Nexora

This module provides functionality for detecting and monitoring concept drift
in clinical prediction models. It implements various statistical methods for
detecting distribution shifts in data and model predictions over time, enabling
proactive model maintenance and retraining.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.metrics import average_precision_score, f1_score, roc_auc_score
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class ConceptDriftDetector:
    """
    A class for detecting concept drift in clinical prediction models.

    This detector monitors input data distributions and model predictions
    to identify shifts that may indicate concept drift, allowing for
    proactive model maintenance and retraining.
    """

    SUPPORTED_METHODS = [
        "ks_test",  # Kolmogorov-Smirnov test
        "chi_squared",  # Chi-squared test
        "js_divergence",  # Jensen-Shannon divergence
        "hellinger",  # Hellinger distance
        "psi",  # Population Stability Index
        "adwin",  # Adaptive Windowing
        "page_hinkley",  # Page-Hinkley test
        "ddm",  # Drift Detection Method
        "eddm",  # Early Drift Detection Method
        "isolation_forest",  # Isolation Forest for anomaly detection
        "lof",  # Local Outlier Factor
        "performance_drop",  # Performance metrics monitoring
    ]

    def __init__(
        self,
        methods: List[str] = ["ks_test", "psi", "performance_drop"],
        reference_window_size: int = 1000,
        detection_window_size: int = 100,
        sensitivity: float = 0.05,
        feature_names: Optional[List[str]] = None,
        categorical_features: Optional[List[str]] = None,
        performance_metrics: List[str] = ["auc", "average_precision", "f1"],
        performance_threshold: float = 0.05,
    ):
        """
        Initialize the concept drift detector.

        Args:
            methods: List of drift detection methods to use
            reference_window_size: Size of the reference window
            detection_window_size: Size of the detection window
            sensitivity: Sensitivity threshold for drift detection
            feature_names: Names of features to monitor
            categorical_features: Names of categorical features
            performance_metrics: List of performance metrics to monitor
            performance_threshold: Threshold for performance drop detection
        """
        # Validate methods
        for method in methods:
            if method not in self.SUPPORTED_METHODS:
                raise ValueError(
                    f"Unsupported method: {method}. Supported methods: {self.SUPPORTED_METHODS}"
                )

        self.methods = methods
        self.reference_window_size = reference_window_size
        self.detection_window_size = detection_window_size
        self.sensitivity = sensitivity
        self.feature_names = feature_names
        self.categorical_features = categorical_features or []
        self.performance_metrics = performance_metrics
        self.performance_threshold = performance_threshold

        # Initialize reference data
        self.reference_X = None
        self.reference_y = None
        self.reference_predictions = None
        self.reference_timestamps = None
        self.reference_performance = {}

        # Initialize detection statistics
        self.drift_statistics = {}
        self.drift_detected = False
        self.drift_features = []
        self.drift_score = 0.0
        self.last_drift_time = None

        # Initialize models for specific methods
        self._initialize_models()

        logger.info(f"Initialized ConceptDriftDetector with methods: {methods}")

    def _initialize_models(self):
        """Initialize models for specific drift detection methods."""
        self.models = {}

        if "isolation_forest" in self.methods:
            self.models["isolation_forest"] = IsolationForest(
                contamination=0.05, random_state=42
            )

        if "lof" in self.methods:
            self.models["lof"] = LocalOutlierFactor(
                n_neighbors=20, contamination=0.05, novelty=True
            )

        if "adwin" in self.methods:
            self.adwin_sum = 0.0
            self.adwin_variance = 0.0
            self.adwin_n = 0

        if "page_hinkley" in self.methods:
            self.ph_sum = 0.0
            self.ph_threshold = 50.0
            self.ph_lambda = 0.5
            self.ph_alpha = 1e-4
            self.ph_mean = 0.0

        if "ddm" in self.methods or "eddm" in self.methods:
            self.ddm_p = 1.0
            self.ddm_s = 0.0
            self.ddm_p_min = float("inf")
            self.ddm_s_min = float("inf")
            self.ddm_warning_level = 2.0
            self.ddm_drift_level = 3.0

    def set_reference_data(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        predictions: Optional[pd.Series] = None,
        timestamps: Optional[pd.Series] = None,
    ):
        """
        Set the reference data for drift detection.

        Args:
            X: Feature data
            y: Target labels (optional)
            predictions: Model predictions (optional)
            timestamps: Timestamps for the data (optional)
        """
        # Store reference data
        self.reference_X = X.copy()

        # Determine feature names if not provided
        if self.feature_names is None:
            self.feature_names = list(X.columns)

        # Store other reference data if provided
        if y is not None:
            self.reference_y = y.copy()

        if predictions is not None:
            self.reference_predictions = predictions.copy()

        if timestamps is not None:
            self.reference_timestamps = timestamps.copy()

        # Calculate reference performance metrics if possible
        if y is not None and predictions is not None:
            self._calculate_reference_performance()

        # Train models for specific methods
        self._train_reference_models()

        logger.info(
            f"Set reference data with {len(X)} samples and {len(self.feature_names)} features"
        )

    def _calculate_reference_performance(self):
        """Calculate performance metrics on reference data."""
        if self.reference_y is None or self.reference_predictions is None:
            return

        # Calculate performance metrics
        for metric in self.performance_metrics:
            if metric == "auc":
                try:
                    self.reference_performance["auc"] = roc_auc_score(
                        self.reference_y, self.reference_predictions
                    )
                except:
                    logger.warning("Could not calculate AUC on reference data")

            elif metric == "average_precision":
                try:
                    self.reference_performance["average_precision"] = (
                        average_precision_score(
                            self.reference_y, self.reference_predictions
                        )
                    )
                except:
                    logger.warning(
                        "Could not calculate average precision on reference data"
                    )

            elif metric == "f1":
                try:
                    # Convert probabilities to binary predictions
                    binary_preds = (self.reference_predictions > 0.5).astype(int)
                    self.reference_performance["f1"] = f1_score(
                        self.reference_y, binary_preds
                    )
                except:
                    logger.warning("Could not calculate F1 score on reference data")

        logger.info(f"Calculated reference performance: {self.reference_performance}")

    def _train_reference_models(self):
        """Train models on reference data for specific drift detection methods."""
        if self.reference_X is None:
            return

        # Standardize data for some methods
        X_std = StandardScaler().fit_transform(self.reference_X)

        # Train Isolation Forest
        if "isolation_forest" in self.methods:
            self.models["isolation_forest"].fit(X_std)
            logger.info("Trained Isolation Forest on reference data")

        # Train Local Outlier Factor
        if "lof" in self.methods:
            self.models["lof"].fit(X_std)
            logger.info("Trained Local Outlier Factor on reference data")

        # Initialize PCA for dimensionality reduction
        if "pca" not in self.models:
            pca = PCA(n_components=min(10, len(self.feature_names)))
            pca.fit(X_std)
            self.models["pca"] = pca
            logger.info("Trained PCA on reference data")

    def detect_drift(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None,
        predictions: Optional[pd.Series] = None,
        timestamps: Optional[pd.Series] = None,
    ) -> bool:
        """
        Detect concept drift in new data.

        Args:
            X: Feature data
            y: Target labels (optional)
            predictions: Model predictions (optional)
            timestamps: Timestamps for the data (optional)

        Returns:
            True if drift is detected, False otherwise
        """
        if self.reference_X is None:
            raise ValueError("Reference data not set. Call set_reference_data first.")

        # Reset drift detection results
        self.drift_detected = False
        self.drift_features = []
        self.drift_score = 0.0
        self.drift_statistics = {}

        # Apply each drift detection method
        for method in self.methods:
            method_func = getattr(self, f"_detect_drift_{method}")
            method_result = method_func(X, y, predictions, timestamps)

            # Store method results
            self.drift_statistics[method] = method_result

            # Update overall drift detection
            if method_result.get("drift_detected", False):
                self.drift_detected = True
                self.drift_score = max(
                    self.drift_score, method_result.get("drift_score", 0.0)
                )

                # Add detected features
                if "drift_features" in method_result:
                    self.drift_features.extend(method_result["drift_features"])

        # Remove duplicates from drift features
        self.drift_features = list(set(self.drift_features))

        # Update last drift time if drift detected
        if self.drift_detected:
            self.last_drift_time = datetime.now()
            logger.warning(f"Concept drift detected with score {self.drift_score:.4f}")
            if self.drift_features:
                logger.warning(f"Drift detected in features: {self.drift_features}")

        return self.drift_detected

    def _detect_drift_ks_test(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Kolmogorov-Smirnov test.

        The KS test compares the distributions of each feature between
        reference and detection windows.
        """
        result = {
            "method": "ks_test",
            "drift_detected": False,
            "drift_score": 0.0,
            "drift_features": [],
            "statistics": {},
        }

        # Check each feature
        for feature in self.feature_names:
            # Skip categorical features
            if feature in self.categorical_features:
                continue

            # Get feature values
            ref_values = self.reference_X[feature].values
            new_values = X[feature].values

            # Perform KS test
            ks_stat, p_value = stats.ks_2samp(ref_values, new_values)

            # Store statistics
            result["statistics"][feature] = {
                "ks_statistic": ks_stat,
                "p_value": p_value,
            }

            # Check for drift
            if p_value < self.sensitivity:
                result["drift_features"].append(feature)
                result["drift_score"] = max(result["drift_score"], 1 - p_value)

        # Determine overall drift
        if result["drift_features"]:
            result["drift_detected"] = True

        return result

    def _detect_drift_chi_squared(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Chi-squared test.

        The Chi-squared test is used for categorical features to compare
        the distribution of categories between reference and detection windows.
        """
        result = {
            "method": "chi_squared",
            "drift_detected": False,
            "drift_score": 0.0,
            "drift_features": [],
            "statistics": {},
        }

        # Check each categorical feature
        for feature in self.categorical_features:
            if feature not in self.feature_names:
                continue

            # Get feature values
            ref_values = self.reference_X[feature].values
            new_values = X[feature].values

            # Get unique categories
            all_categories = np.unique(np.concatenate([ref_values, new_values]))

            # Count occurrences in each window
            ref_counts = np.array([np.sum(ref_values == cat) for cat in all_categories])
            new_counts = np.array([np.sum(new_values == cat) for cat in all_categories])

            # Add small constant to avoid division by zero
            ref_counts = ref_counts + 0.5
            new_counts = new_counts + 0.5

            # Normalize counts
            ref_probs = ref_counts / np.sum(ref_counts)
            new_probs = new_counts / np.sum(new_counts)

            # Calculate Chi-squared statistic
            chi2_stat = np.sum((ref_probs - new_probs) ** 2 / ref_probs)

            # Calculate p-value (degrees of freedom = num_categories - 1)
            dof = len(all_categories) - 1
            p_value = 1 - stats.chi2.cdf(chi2_stat, dof)

            # Store statistics
            result["statistics"][feature] = {
                "chi2_statistic": chi2_stat,
                "p_value": p_value,
                "dof": dof,
            }

            # Check for drift
            if p_value < self.sensitivity:
                result["drift_features"].append(feature)
                result["drift_score"] = max(result["drift_score"], 1 - p_value)

        # Determine overall drift
        if result["drift_features"]:
            result["drift_detected"] = True

        return result

    def _detect_drift_js_divergence(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Jensen-Shannon divergence.

        JS divergence measures the similarity between two probability distributions.
        """
        result = {
            "method": "js_divergence",
            "drift_detected": False,
            "drift_score": 0.0,
            "drift_features": [],
            "statistics": {},
        }

        # Check each feature
        for feature in self.feature_names:
            # Get feature values
            ref_values = self.reference_X[feature].values
            new_values = X[feature].values

            # For continuous features, bin the values
            if feature not in self.categorical_features:
                # Determine bin edges from combined data
                all_values = np.concatenate([ref_values, new_values])
                bin_edges = np.histogram_bin_edges(all_values, bins="auto")

                # Calculate histograms
                ref_hist, _ = np.histogram(ref_values, bins=bin_edges, density=True)
                new_hist, _ = np.histogram(new_values, bins=bin_edges, density=True)

                # Add small constant to avoid log(0)
                ref_hist = ref_hist + 1e-10
                new_hist = new_hist + 1e-10

                # Normalize
                ref_hist = ref_hist / np.sum(ref_hist)
                new_hist = new_hist / np.sum(new_hist)
            else:
                # For categorical features, count occurrences
                all_categories = np.unique(np.concatenate([ref_values, new_values]))

                ref_hist = np.array(
                    [np.mean(ref_values == cat) for cat in all_categories]
                )
                new_hist = np.array(
                    [np.mean(new_values == cat) for cat in all_categories]
                )

                # Add small constant to avoid log(0)
                ref_hist = ref_hist + 1e-10
                new_hist = new_hist + 1e-10

                # Normalize
                ref_hist = ref_hist / np.sum(ref_hist)
                new_hist = new_hist / np.sum(new_hist)

            # Calculate JS divergence
            m_hist = 0.5 * (ref_hist + new_hist)
            js_div = 0.5 * (
                np.sum(ref_hist * np.log(ref_hist / m_hist))
                + np.sum(new_hist * np.log(new_hist / m_hist))
            )

            # Store statistics
            result["statistics"][feature] = {"js_divergence": js_div}

            # Check for drift
            if js_div > 0.1:  # Threshold for JS divergence
                result["drift_features"].append(feature)
                result["drift_score"] = max(result["drift_score"], js_div)

        # Determine overall drift
        if result["drift_features"]:
            result["drift_detected"] = True

        return result

    def _detect_drift_hellinger(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Hellinger distance.

        Hellinger distance measures the similarity between two probability distributions.
        """
        result = {
            "method": "hellinger",
            "drift_detected": False,
            "drift_score": 0.0,
            "drift_features": [],
            "statistics": {},
        }

        # Check each feature
        for feature in self.feature_names:
            # Get feature values
            ref_values = self.reference_X[feature].values
            new_values = X[feature].values

            # For continuous features, bin the values
            if feature not in self.categorical_features:
                # Determine bin edges from combined data
                all_values = np.concatenate([ref_values, new_values])
                bin_edges = np.histogram_bin_edges(all_values, bins="auto")

                # Calculate histograms
                ref_hist, _ = np.histogram(ref_values, bins=bin_edges, density=True)
                new_hist, _ = np.histogram(new_values, bins=bin_edges, density=True)

                # Add small constant to avoid sqrt(0)
                ref_hist = ref_hist + 1e-10
                new_hist = new_hist + 1e-10

                # Normalize
                ref_hist = ref_hist / np.sum(ref_hist)
                new_hist = new_hist / np.sum(new_hist)
            else:
                # For categorical features, count occurrences
                all_categories = np.unique(np.concatenate([ref_values, new_values]))

                ref_hist = np.array(
                    [np.mean(ref_values == cat) for cat in all_categories]
                )
                new_hist = np.array(
                    [np.mean(new_values == cat) for cat in all_categories]
                )

                # Add small constant to avoid sqrt(0)
                ref_hist = ref_hist + 1e-10
                new_hist = new_hist + 1e-10

                # Normalize
                ref_hist = ref_hist / np.sum(ref_hist)
                new_hist = new_hist / np.sum(new_hist)

            # Calculate Hellinger distance
            hellinger_dist = np.sqrt(
                0.5 * np.sum((np.sqrt(ref_hist) - np.sqrt(new_hist)) ** 2)
            )

            # Store statistics
            result["statistics"][feature] = {"hellinger_distance": hellinger_dist}

            # Check for drift
            if hellinger_dist > 0.2:  # Threshold for Hellinger distance
                result["drift_features"].append(feature)
                result["drift_score"] = max(result["drift_score"], hellinger_dist)

        # Determine overall drift
        if result["drift_features"]:
            result["drift_detected"] = True

        return result

    def _detect_drift_psi(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Population Stability Index (PSI).

        PSI measures the change in distribution between two populations.
        """
        result = {
            "method": "psi",
            "drift_detected": False,
            "drift_score": 0.0,
            "drift_features": [],
            "statistics": {},
        }

        # Check each feature
        for feature in self.feature_names:
            # Get feature values
            ref_values = self.reference_X[feature].values
            new_values = X[feature].values

            # For continuous features, bin the values
            if feature not in self.categorical_features:
                # Determine bin edges from reference data
                bin_edges = np.histogram_bin_edges(ref_values, bins=10)

                # Calculate histograms
                ref_hist, _ = np.histogram(ref_values, bins=bin_edges)
                new_hist, _ = np.histogram(new_values, bins=bin_edges)

                # Add small constant to avoid division by zero
                ref_hist = ref_hist + 1
                new_hist = new_hist + 1

                # Normalize
                ref_hist = ref_hist / np.sum(ref_hist)
                new_hist = new_hist / np.sum(new_hist)
            else:
                # For categorical features, count occurrences
                all_categories = np.unique(np.concatenate([ref_values, new_values]))

                ref_hist = np.array(
                    [np.sum(ref_values == cat) for cat in all_categories]
                )
                new_hist = np.array(
                    [np.sum(new_values == cat) for cat in all_categories]
                )

                # Add small constant to avoid division by zero
                ref_hist = ref_hist + 1
                new_hist = new_hist + 1

                # Normalize
                ref_hist = ref_hist / np.sum(ref_hist)
                new_hist = new_hist / np.sum(new_hist)

            # Calculate PSI
            psi = np.sum((new_hist - ref_hist) * np.log(new_hist / ref_hist))

            # Store statistics
            result["statistics"][feature] = {"psi": psi}

            # Check for drift
            if psi > 0.2:  # Threshold for PSI
                result["drift_features"].append(feature)
                result["drift_score"] = max(
                    result["drift_score"], psi / 2
                )  # Normalize to [0, 1]

        # Determine overall drift
        if result["drift_features"]:
            result["drift_detected"] = True

        return result

    def _detect_drift_adwin(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Adaptive Windowing (ADWIN).

        ADWIN maintains a variable-length window of recent examples and
        detects changes by comparing the means of two sub-windows.
        """
        result = {
            "method": "adwin",
            "drift_detected": False,
            "drift_score": 0.0,
            "statistics": {},
        }

        # Use predictions if available, otherwise use first feature
        if predictions is not None:
            values = predictions.values
        else:
            values = X.iloc[:, 0].values

        # Update ADWIN statistics
        for value in values:
            self.adwin_sum += value
            self.adwin_n += 1

            # Calculate mean and variance
            mean = self.adwin_sum / self.adwin_n
            self.adwin_variance = (
                self.adwin_n * self.adwin_variance + (value - mean) ** 2
            ) / (self.adwin_n + 1)

            # Check for drift
            if self.adwin_n > 10:
                # Calculate threshold
                delta = 0.002
                epsilon = np.sqrt(
                    2 * self.adwin_variance * np.log(1 / delta) / self.adwin_n
                )

                # Detect drift if mean change exceeds threshold
                if (
                    np.abs(mean - (self.adwin_sum - value) / (self.adwin_n - 1))
                    > epsilon
                ):
                    result["drift_detected"] = True
                    result["drift_score"] = 1.0
                    break

        # Store statistics
        result["statistics"] = {
            "adwin_mean": self.adwin_sum / self.adwin_n if self.adwin_n > 0 else 0,
            "adwin_variance": self.adwin_variance,
            "adwin_n": self.adwin_n,
        }

        return result

    def _detect_drift_page_hinkley(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Page-Hinkley test.

        The Page-Hinkley test is designed to detect changes in the average of a
        Gaussian signal.
        """
        result = {
            "method": "page_hinkley",
            "drift_detected": False,
            "drift_score": 0.0,
            "statistics": {},
        }

        # Use predictions if available, otherwise use first feature
        if predictions is not None:
            values = predictions.values
        else:
            values = X.iloc[:, 0].values

        # Update Page-Hinkley statistics
        for value in values:
            # Update mean
            if self.ph_mean == 0:
                self.ph_mean = value
            else:
                self.ph_mean = self.ph_mean + self.ph_alpha * (value - self.ph_mean)

            # Calculate deviation from mean
            deviation = value - self.ph_mean - self.ph_lambda

            # Update sum
            self.ph_sum = max(0, self.ph_sum + deviation)

            # Check for drift
            if self.ph_sum > self.ph_threshold:
                result["drift_detected"] = True
                result["drift_score"] = min(1.0, self.ph_sum / (2 * self.ph_threshold))
                break

        # Store statistics
        result["statistics"] = {"ph_mean": self.ph_mean, "ph_sum": self.ph_sum}

        return result

    def _detect_drift_ddm(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Drift Detection Method (DDM).

        DDM monitors the error rate of the model and signals drift when the
        error rate increases beyond a threshold.
        """
        result = {
            "method": "ddm",
            "drift_detected": False,
            "drift_score": 0.0,
            "statistics": {},
        }

        # Need both predictions and actual values
        if predictions is None or y is None:
            return result

        # Calculate errors
        errors = (predictions.values > 0.5).astype(int) != y.values

        # Update DDM statistics
        for error in errors:
            # Update error rate and standard deviation
            error_rate = error
            self.ddm_p = (
                self.ddm_p + (error_rate - self.ddm_p) / self.adwin_n
                if self.adwin_n > 0
                else error_rate
            )
            self.ddm_s = (
                np.sqrt(self.ddm_p * (1 - self.ddm_p) / self.adwin_n)
                if self.adwin_n > 0
                else 0
            )

            # Update minimum values
            if self.ddm_p + self.ddm_s < self.ddm_p_min + self.ddm_s_min:
                self.ddm_p_min = self.ddm_p
                self.ddm_s_min = self.ddm_s

            # Check for warning level
            if (
                self.ddm_p + self.ddm_s
                > self.ddm_p_min + self.ddm_warning_level * self.ddm_s_min
            ):
                result["statistics"]["warning"] = True

            # Check for drift level
            if (
                self.ddm_p + self.ddm_s
                > self.ddm_p_min + self.ddm_drift_level * self.ddm_s_min
            ):
                result["drift_detected"] = True
                result["drift_score"] = min(
                    1.0,
                    (self.ddm_p + self.ddm_s - self.ddm_p_min)
                    / (self.ddm_drift_level * self.ddm_s_min),
                )
                break

        # Store statistics
        result["statistics"] = {
            "ddm_p": self.ddm_p,
            "ddm_s": self.ddm_s,
            "ddm_p_min": self.ddm_p_min,
            "ddm_s_min": self.ddm_s_min,
        }

        return result

    def _detect_drift_eddm(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Early Drift Detection Method (EDDM).

        EDDM monitors the distance between errors and signals drift when the
        distance decreases beyond a threshold.
        """
        result = {
            "method": "eddm",
            "drift_detected": False,
            "drift_score": 0.0,
            "statistics": {},
        }

        # Need both predictions and actual values
        if predictions is None or y is None:
            return result

        # Calculate errors
        errors = (predictions.values > 0.5).astype(int) != y.values

        # Find indices of errors
        error_indices = np.where(errors)[0]

        # Calculate distances between errors
        if len(error_indices) > 1:
            distances = error_indices[1:] - error_indices[:-1]

            # Calculate mean and standard deviation of distances
            mean_distance = np.mean(distances)
            std_distance = np.std(distances)

            # Calculate EDDM statistic
            eddm_stat = mean_distance + 2 * std_distance

            # Store maximum statistic
            if not hasattr(self, "eddm_max"):
                self.eddm_max = eddm_stat
            else:
                self.eddm_max = max(self.eddm_max, eddm_stat)

            # Check for warning level
            if eddm_stat < 0.95 * self.eddm_max:
                result["statistics"]["warning"] = True

            # Check for drift level
            if eddm_stat < 0.90 * self.eddm_max:
                result["drift_detected"] = True
                result["drift_score"] = min(
                    1.0, (self.eddm_max - eddm_stat) / (0.1 * self.eddm_max)
                )

            # Store statistics
            result["statistics"] = {"eddm_stat": eddm_stat, "eddm_max": self.eddm_max}

        return result

    def _detect_drift_isolation_forest(
        self, X, y=None, predictions=None, timestamps=None
    ):
        """
        Detect drift using Isolation Forest.

        Isolation Forest is used to detect anomalies in the feature space.
        """
        result = {
            "method": "isolation_forest",
            "drift_detected": False,
            "drift_score": 0.0,
            "statistics": {},
        }

        # Standardize data
        X_std = StandardScaler().fit_transform(X)

        # Get anomaly scores
        anomaly_scores = -self.models["isolation_forest"].score_samples(X_std)

        # Calculate drift score as proportion of anomalies
        anomaly_threshold = np.percentile(anomaly_scores, 95)
        drift_score = np.mean(anomaly_scores > anomaly_threshold)

        # Store statistics
        result["statistics"] = {
            "mean_anomaly_score": np.mean(anomaly_scores),
            "max_anomaly_score": np.max(anomaly_scores),
            "anomaly_threshold": anomaly_threshold,
            "anomaly_rate": drift_score,
        }

        # Check for drift
        if drift_score > 0.1:  # Threshold for anomaly rate
            result["drift_detected"] = True
            result["drift_score"] = drift_score

        return result

    def _detect_drift_lof(self, X, y=None, predictions=None, timestamps=None):
        """
        Detect drift using Local Outlier Factor.

        LOF is used to detect local anomalies in the feature space.
        """
        result = {
            "method": "lof",
            "drift_detected": False,
            "drift_score": 0.0,
            "statistics": {},
        }

        # Standardize data
        X_std = StandardScaler().fit_transform(X)

        # Get anomaly scores
        anomaly_scores = -self.models["lof"].score_samples(X_std)

        # Calculate drift score as proportion of anomalies
        anomaly_threshold = np.percentile(anomaly_scores, 95)
        drift_score = np.mean(anomaly_scores > anomaly_threshold)

        # Store statistics
        result["statistics"] = {
            "mean_anomaly_score": np.mean(anomaly_scores),
            "max_anomaly_score": np.max(anomaly_scores),
            "anomaly_threshold": anomaly_threshold,
            "anomaly_rate": drift_score,
        }

        # Check for drift
        if drift_score > 0.1:  # Threshold for anomaly rate
            result["drift_detected"] = True
            result["drift_score"] = drift_score

        return result

    def _detect_drift_performance_drop(
        self, X, y=None, predictions=None, timestamps=None
    ):
        """
        Detect drift by monitoring performance metrics.

        This method detects drift when performance metrics drop significantly.
        """
        result = {
            "method": "performance_drop",
            "drift_detected": False,
            "drift_score": 0.0,
            "statistics": {},
        }

        # Need both predictions and actual values
        if predictions is None or y is None:
            return result

        # Need reference performance metrics
        if not self.reference_performance:
            return result

        # Calculate current performance metrics
        current_performance = {}

        for metric in self.performance_metrics:
            if metric == "auc":
                try:
                    current_performance["auc"] = roc_auc_score(y, predictions)
                except:
                    logger.warning("Could not calculate AUC on current data")

            elif metric == "average_precision":
                try:
                    current_performance["average_precision"] = average_precision_score(
                        y, predictions
                    )
                except:
                    logger.warning(
                        "Could not calculate average precision on current data"
                    )

            elif metric == "f1":
                try:
                    # Convert probabilities to binary predictions
                    binary_preds = (predictions > 0.5).astype(int)
                    current_performance["f1"] = f1_score(y, binary_preds)
                except:
                    logger.warning("Could not calculate F1 score on current data")

        # Store statistics
        result["statistics"] = {
            "reference_performance": self.reference_performance,
            "current_performance": current_performance,
        }

        # Check for performance drop
        for metric, ref_value in self.reference_performance.items():
            if metric in current_performance:
                current_value = current_performance[metric]
                relative_drop = (ref_value - current_value) / ref_value

                # Store relative drop
                result["statistics"][f"{metric}_relative_drop"] = relative_drop

                # Check for significant drop
                if relative_drop > self.performance_threshold:
                    result["drift_detected"] = True
                    result["drift_score"] = max(result["drift_score"], relative_drop)

        return result

    def plot_drift_statistics(self, feature=None, method=None, ax=None):
        """
        Plot drift statistics for visualization.

        Args:
            feature: Feature to plot statistics for (optional)
            method: Method to plot statistics for (optional)
            ax: Matplotlib axis to plot on (optional)

        Returns:
            Matplotlib axis
        """
        if not self.drift_statistics:
            raise ValueError("No drift statistics available. Run detect_drift first.")

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        # Plot based on method
        if method is not None:
            if method not in self.drift_statistics:
                raise ValueError(f"Method {method} not found in drift statistics")

            method_stats = self.drift_statistics[method]

            if method in [
                "ks_test",
                "chi_squared",
                "js_divergence",
                "hellinger",
                "psi",
            ]:
                # Plot feature-based statistics
                if feature is not None:
                    if feature not in method_stats["statistics"]:
                        raise ValueError(
                            f"Feature {feature} not found in {method} statistics"
                        )

                    feature_stats = method_stats["statistics"][feature]

                    # Plot based on statistic type
                    if "p_value" in feature_stats:
                        ax.bar(["p-value"], [feature_stats["p_value"]])
                        ax.axhline(
                            y=self.sensitivity,
                            color="r",
                            linestyle="--",
                            label=f"Threshold ({self.sensitivity})",
                        )
                        ax.set_ylabel("p-value")
                    elif "js_divergence" in feature_stats:
                        ax.bar(["JS Divergence"], [feature_stats["js_divergence"]])
                        ax.axhline(
                            y=0.1, color="r", linestyle="--", label="Threshold (0.1)"
                        )
                        ax.set_ylabel("JS Divergence")
                    elif "hellinger_distance" in feature_stats:
                        ax.bar(
                            ["Hellinger Distance"],
                            [feature_stats["hellinger_distance"]],
                        )
                        ax.axhline(
                            y=0.2, color="r", linestyle="--", label="Threshold (0.2)"
                        )
                        ax.set_ylabel("Hellinger Distance")
                    elif "psi" in feature_stats:
                        ax.bar(["PSI"], [feature_stats["psi"]])
                        ax.axhline(
                            y=0.2, color="r", linestyle="--", label="Threshold (0.2)"
                        )
                        ax.set_ylabel("Population Stability Index")

                    ax.set_title(f"{method} Statistics for {feature}")
                else:
                    # Plot all features
                    features = list(method_stats["statistics"].keys())

                    if not features:
                        ax.text(
                            0.5,
                            0.5,
                            f"No feature statistics available for {method}",
                            ha="center",
                            va="center",
                            transform=ax.transAxes,
                        )
                    else:
                        # Determine statistic to plot
                        stat_key = None
                        for key in [
                            "p_value",
                            "js_divergence",
                            "hellinger_distance",
                            "psi",
                        ]:
                            if key in method_stats["statistics"][features[0]]:
                                stat_key = key
                                break

                        if stat_key:
                            values = [
                                method_stats["statistics"][f].get(stat_key, 0)
                                for f in features
                            ]
                            ax.bar(features, values)

                            # Add threshold line
                            threshold = (
                                0.05
                                if stat_key == "p_value"
                                else 0.1 if stat_key == "js_divergence" else 0.2
                            )
                            ax.axhline(
                                y=threshold,
                                color="r",
                                linestyle="--",
                                label=f"Threshold ({threshold})",
                            )

                            ax.set_ylabel(stat_key)
                            ax.set_title(f"{method} Statistics for All Features")
                            ax.tick_params(axis="x", rotation=45)
            else:
                # Plot method-specific statistics
                stats = method_stats["statistics"]

                if method == "adwin":
                    ax.bar(
                        ["Mean", "Variance"],
                        [stats["adwin_mean"], stats["adwin_variance"]],
                    )
                    ax.set_title("ADWIN Statistics")
                elif method == "page_hinkley":
                    ax.bar(["Mean", "Sum"], [stats["ph_mean"], stats["ph_sum"]])
                    ax.axhline(
                        y=self.ph_threshold,
                        color="r",
                        linestyle="--",
                        label=f"Threshold ({self.ph_threshold})",
                    )
                    ax.set_title("Page-Hinkley Statistics")
                elif method in ["ddm", "eddm"]:
                    ax.bar(list(stats.keys()), list(stats.values()))
                    ax.set_title(f"{method.upper()} Statistics")
                    ax.tick_params(axis="x", rotation=45)
                elif method in ["isolation_forest", "lof"]:
                    ax.bar(
                        ["Mean Score", "Max Score", "Threshold", "Anomaly Rate"],
                        [
                            stats["mean_anomaly_score"],
                            stats["max_anomaly_score"],
                            stats["anomaly_threshold"],
                            stats["anomaly_rate"],
                        ],
                    )
                    ax.set_title(f"{method} Statistics")
                elif method == "performance_drop":
                    # Plot performance comparison
                    metrics = list(
                        set(stats["reference_performance"].keys())
                        & set(stats["current_performance"].keys())
                    )

                    if metrics:
                        ref_values = [
                            stats["reference_performance"][m] for m in metrics
                        ]
                        cur_values = [stats["current_performance"][m] for m in metrics]

                        x = np.arange(len(metrics))
                        width = 0.35

                        ax.bar(x - width / 2, ref_values, width, label="Reference")
                        ax.bar(x + width / 2, cur_values, width, label="Current")

                        ax.set_xticks(x)
                        ax.set_xticklabels(metrics)
                        ax.set_ylabel("Performance")
                        ax.set_title("Performance Comparison")
                        ax.legend()
        else:
            # Plot overall drift scores
            methods = list(self.drift_statistics.keys())
            drift_scores = [
                self.drift_statistics[m].get("drift_score", 0) for m in methods
            ]

            ax.bar(methods, drift_scores)
            ax.axhline(y=0.5, color="r", linestyle="--", label="Threshold (0.5)")
            ax.set_ylabel("Drift Score")
            ax.set_title("Drift Scores by Method")
            ax.tick_params(axis="x", rotation=45)

        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax

    def get_drift_report(self) -> Dict:
        """
        Generate a comprehensive drift report.

        Returns:
            Dictionary containing drift detection results and statistics
        """
        if not self.drift_statistics:
            raise ValueError("No drift statistics available. Run detect_drift first.")

        report = {
            "drift_detected": self.drift_detected,
            "drift_score": self.drift_score,
            "drift_features": self.drift_features,
            "last_drift_time": self.last_drift_time,
            "methods": {},
            "feature_statistics": {},
        }

        # Add method-specific results
        for method, stats in self.drift_statistics.items():
            report["methods"][method] = {
                "drift_detected": stats.get("drift_detected", False),
                "drift_score": stats.get("drift_score", 0.0),
            }

            # Add method-specific statistics
            if "statistics" in stats:
                report["methods"][method]["statistics"] = stats["statistics"]

            # Add feature-specific statistics
            if "drift_features" in stats:
                for feature in stats.get("drift_features", []):
                    if feature not in report["feature_statistics"]:
                        report["feature_statistics"][feature] = {}

                    if method in stats["statistics"] and feature in stats["statistics"]:
                        report["feature_statistics"][feature][method] = stats[
                            "statistics"
                        ][feature]

        return report
