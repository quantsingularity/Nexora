"""
Survival Analysis Module for Nexora

This module provides functionality for survival analysis in healthcare applications,
including time-to-event modeling, hazard functions, and survival curve estimation.
It extends standard machine learning approaches to handle censored data and
time-dependent covariates common in clinical settings.
"""

import logging
import warnings
from typing import Callable, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter, WeibullAFTFitter
from lifelines.utils import concordance_index
from sklearn.base import BaseEstimator
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class SurvivalAnalysisModel(BaseEstimator):
    """
    A class for survival analysis modeling in healthcare applications.

    This model handles time-to-event data with censoring, common in healthcare
    applications such as predicting time to readmission, mortality, or disease progression.
    """

    SUPPORTED_MODELS = ["cox_ph", "weibull_aft", "kaplan_meier"]

    def __init__(
        self,
        model_type: str = "cox_ph",
        time_column: str = "duration",
        event_column: str = "event",
        alpha: float = 0.05,
        penalizer: float = 0.1,
        l1_ratio: float = 0.0,
        fit_intercept: bool = True,
        normalize_features: bool = True,
        stratified_cv: bool = True,
        random_state: int = 42,
    ):
        """
        Initialize the survival analysis model.

        Args:
            model_type: Type of survival model ('cox_ph', 'weibull_aft', 'kaplan_meier')
            time_column: Column name for time-to-event
            event_column: Column name for event indicator (1 = event occurred, 0 = censored)
            alpha: Significance level for confidence intervals
            penalizer: Regularization strength
            l1_ratio: L1 ratio for elastic net regularization (0 = L2, 1 = L1)
            fit_intercept: Whether to fit an intercept
            normalize_features: Whether to normalize features
            stratified_cv: Whether to use stratified cross-validation
            random_state: Random seed for reproducibility
        """
        if model_type not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Unsupported model type: {model_type}. Supported types: {self.SUPPORTED_MODELS}"
            )

        self.model_type = model_type
        self.time_column = time_column
        self.event_column = event_column
        self.alpha = alpha
        self.penalizer = penalizer
        self.l1_ratio = l1_ratio
        self.fit_intercept = fit_intercept
        self.normalize_features = normalize_features
        self.stratified_cv = stratified_cv
        self.random_state = random_state

        # Initialize model
        self._initialize_model()

        # Initialize scaler if normalization is enabled
        self.scaler = StandardScaler() if normalize_features else None

        # Store feature names
        self.feature_names = None

        logger.info(f"Initialized {model_type} survival analysis model")

    def _initialize_model(self):
        """Initialize the appropriate survival model based on model_type."""
        if self.model_type == "cox_ph":
            self.model = CoxPHFitter(
                alpha=self.alpha, penalizer=self.penalizer, l1_ratio=self.l1_ratio
            )
        elif self.model_type == "weibull_aft":
            self.model = WeibullAFTFitter(
                alpha=self.alpha, penalizer=self.penalizer, l1_ratio=self.l1_ratio
            )
        elif self.model_type == "kaplan_meier":
            self.model = KaplanMeierFitter()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def fit(
        self, X: pd.DataFrame, y: Optional[pd.DataFrame] = None
    ) -> "SurvivalAnalysisModel":
        """
        Fit the survival model to the data.

        Args:
            X: Feature DataFrame, must include time_column and event_column
            y: Not used, included for compatibility with scikit-learn API

        Returns:
            Fitted model instance
        """
        # Validate input
        if self.time_column not in X.columns:
            raise ValueError(
                f"Time column '{self.time_column}' not found in input data"
            )

        if self.event_column not in X.columns:
            raise ValueError(
                f"Event column '{self.event_column}' not found in input data"
            )

        # Store feature names (excluding time and event columns)
        self.feature_names = [
            col for col in X.columns if col not in [self.time_column, self.event_column]
        ]

        # Prepare data
        if self.model_type in ["cox_ph", "weibull_aft"]:
            # For regression models, we need features
            if not self.feature_names:
                raise ValueError("No feature columns found in input data")

            # Create a copy of the data
            df = X.copy()

            # Normalize features if requested
            if self.normalize_features:
                df[self.feature_names] = self.scaler.fit_transform(
                    df[self.feature_names]
                )

            # Fit the model
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                self.model.fit(
                    df, duration_col=self.time_column, event_col=self.event_column
                )

        elif self.model_type == "kaplan_meier":
            # For Kaplan-Meier, we only need time and event data
            self.model.fit(
                durations=X[self.time_column], event_observed=X[self.event_column]
            )

        logger.info(f"Fitted {self.model_type} model with {len(X)} samples")
        return self

    def predict_survival_function(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict the survival function for each sample.

        Args:
            X: Feature DataFrame

        Returns:
            DataFrame with survival probabilities at different time points
        """
        if self.model_type == "kaplan_meier":
            # Kaplan-Meier provides a population-level survival curve
            return self.model.survival_function_

        # Prepare data
        df = X.copy()

        # Ensure we have the right features
        missing_features = [f for f in self.feature_names if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing features in input data: {missing_features}")

        # Normalize features if needed
        if self.normalize_features:
            df[self.feature_names] = self.scaler.transform(df[self.feature_names])

        # Predict survival function
        return self.model.predict_survival_function(df)

    def predict_median_survival_time(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict the median survival time for each sample.

        Args:
            X: Feature DataFrame

        Returns:
            Series with median survival time predictions
        """
        if self.model_type == "kaplan_meier":
            # Kaplan-Meier provides a population-level estimate
            return pd.Series([self.model.median_survival_time_] * len(X))

        # Prepare data
        df = X.copy()

        # Ensure we have the right features
        missing_features = [f for f in self.feature_names if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing features in input data: {missing_features}")

        # Normalize features if needed
        if self.normalize_features:
            df[self.feature_names] = self.scaler.transform(df[self.feature_names])

        # Predict median survival time
        return self.model.predict_median(df)

    def predict_risk_score(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict the risk score for each sample.

        For Cox PH, this is the linear predictor (log hazard ratio).
        For Weibull AFT, this is the negative of the linear predictor.
        Not applicable for Kaplan-Meier.

        Args:
            X: Feature DataFrame

        Returns:
            Series with risk scores (higher = higher risk)
        """
        if self.model_type == "kaplan_meier":
            raise ValueError("Risk scores are not applicable for Kaplan-Meier model")

        # Prepare data
        df = X.copy()

        # Ensure we have the right features
        missing_features = [f for f in self.feature_names if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing features in input data: {missing_features}")

        # Normalize features if needed
        if self.normalize_features:
            df[self.feature_names] = self.scaler.transform(df[self.feature_names])

        if self.model_type == "cox_ph":
            # For Cox PH, the linear predictor is the log hazard ratio
            return self.model.predict_log_partial_hazard(df)
        elif self.model_type == "weibull_aft":
            # For AFT models, lower values of the linear predictor mean higher risk
            # So we negate it to get a risk score where higher = higher risk
            return -self.model.predict_log_partial_hazard(df)

    def predict_survival_probability(
        self, X: pd.DataFrame, time_point: float
    ) -> pd.Series:
        """
        Predict the survival probability at a specific time point.

        Args:
            X: Feature DataFrame
            time_point: Time point at which to predict survival probability

        Returns:
            Series with survival probabilities at the specified time point
        """
        if self.model_type == "kaplan_meier":
            # Kaplan-Meier provides a population-level estimate
            return pd.Series([self.model.predict(time_point)] * len(X))

        # Prepare data
        df = X.copy()

        # Ensure we have the right features
        missing_features = [f for f in self.feature_names if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing features in input data: {missing_features}")

        # Normalize features if needed
        if self.normalize_features:
            df[self.feature_names] = self.scaler.transform(df[self.feature_names])

        # Predict survival probability
        return self.model.predict_survival_function(df).loc[time_point]

    def score(self, X: pd.DataFrame, y: Optional[pd.DataFrame] = None) -> float:
        """
        Calculate the concordance index (C-index) for the model.

        The C-index measures the model's ability to correctly rank survival times.
        It's similar to AUC but accounts for censoring.

        Args:
            X: Feature DataFrame, must include time_column and event_column
            y: Not used, included for compatibility with scikit-learn API

        Returns:
            Concordance index (C-index)
        """
        if self.time_column not in X.columns:
            raise ValueError(
                f"Time column '{self.time_column}' not found in input data"
            )

        if self.event_column not in X.columns:
            raise ValueError(
                f"Event column '{self.event_column}' not found in input data"
            )

        if self.model_type == "kaplan_meier":
            # C-index not applicable for Kaplan-Meier
            logger.warning("C-index not applicable for Kaplan-Meier model")
            return np.nan

        # Get actual times and events
        actual_times = X[self.time_column]
        actual_events = X[self.event_column]

        # Predict risk scores
        predicted_risks = self.predict_risk_score(X)

        # Calculate concordance index
        c_index = concordance_index(actual_times, -predicted_risks, actual_events)

        return c_index

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from the model.

        For Cox PH and Weibull AFT, this returns the coefficients and p-values.
        Not applicable for Kaplan-Meier.

        Returns:
            DataFrame with feature importance metrics
        """
        if self.model_type == "kaplan_meier":
            raise ValueError("Feature importance not applicable for Kaplan-Meier model")

        if not hasattr(self.model, "summary"):
            raise ValueError("Model does not support feature importance")

        # Get model summary
        summary = self.model.summary

        # Extract relevant columns
        importance = summary[["coef", "exp(coef)", "p"]]

        # Rename columns for clarity
        importance = importance.rename(
            columns={"coef": "coefficient", "exp(coef)": "hazard_ratio", "p": "p_value"}
        )

        # Add absolute coefficient as a measure of importance
        importance["importance"] = np.abs(importance["coefficient"])

        # Sort by importance
        importance = importance.sort_values("importance", ascending=False)

        return importance

    def plot_survival_curves(self, X: pd.DataFrame, num_samples: int = 10, ax=None):
        """
        Plot survival curves for a subset of samples.

        Args:
            X: Feature DataFrame
            num_samples: Number of samples to plot
            ax: Matplotlib axis to plot on

        Returns:
            Matplotlib axis
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        if self.model_type == "kaplan_meier":
            # Plot Kaplan-Meier curve
            self.model.plot_survival_function(ax=ax)
            ax.set_title("Kaplan-Meier Survival Curve")
        else:
            # Sample a subset of rows
            if len(X) > num_samples:
                sampled_X = X.sample(num_samples, random_state=self.random_state)
            else:
                sampled_X = X

            # Predict survival functions
            survival_funcs = self.predict_survival_function(sampled_X)

            # Plot each survival curve
            for i, (idx, func) in enumerate(survival_funcs.iteritems()):
                if i < num_samples:  # Limit the number of curves
                    func.plot(ax=ax, label=f"Sample {i+1}")

            ax.set_title(f"{self.model_type.upper()} Survival Curves")

        ax.set_xlabel("Time")
        ax.set_ylabel("Survival Probability")
        ax.grid(True, alpha=0.3)
        ax.legend()

        return ax

    def plot_feature_importance(self, top_n: int = 10, ax=None):
        """
        Plot feature importance.

        Args:
            top_n: Number of top features to plot
            ax: Matplotlib axis to plot on

        Returns:
            Matplotlib axis
        """
        if self.model_type == "kaplan_meier":
            raise ValueError("Feature importance not applicable for Kaplan-Meier model")

        # Get feature importance
        importance = self.get_feature_importance()

        # Select top N features
        if len(importance) > top_n:
            importance = importance.head(top_n)

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))

        # Plot horizontal bar chart
        importance.sort_values("importance").plot(
            kind="barh",
            y="coefficient",
            ax=ax,
            color=importance["coefficient"].apply(lambda x: "red" if x < 0 else "blue"),
        )

        ax.set_title(f"Top {top_n} Feature Coefficients")
        ax.set_xlabel("Coefficient Value")
        ax.grid(True, alpha=0.3)

        return ax


class TimeVaryingSurvivalAnalysis:
    """
    A class for time-varying survival analysis.

    This class handles time-varying covariates in survival analysis by
    creating time-dependent datasets and fitting appropriate models.
    """

    def __init__(
        self,
        id_column: str = "patient_id",
        time_column: str = "time",
        event_column: str = "event",
        start_time_column: str = "start",
        stop_time_column: str = "stop",
        penalizer: float = 0.1,
        alpha: float = 0.05,
    ):
        """
        Initialize the time-varying survival analysis model.

        Args:
            id_column: Column name for subject identifier
            time_column: Column name for time-to-event in non-time-varying data
            event_column: Column name for event indicator
            start_time_column: Column name for interval start in time-varying data
            stop_time_column: Column name for interval stop in time-varying data
            penalizer: Regularization strength
            alpha: Significance level for confidence intervals
        """
        self.id_column = id_column
        self.time_column = time_column
        self.event_column = event_column
        self.start_time_column = start_time_column
        self.stop_time_column = stop_time_column
        self.penalizer = penalizer
        self.alpha = alpha

        # Initialize model
        self.model = CoxPHFitter(penalizer=penalizer, alpha=alpha)

        logger.info("Initialized time-varying survival analysis model")

    def _create_time_intervals(
        self, df: pd.DataFrame, time_points: List[float]
    ) -> pd.DataFrame:
        """
        Create time intervals for time-varying analysis.

        Args:
            df: Input DataFrame with one row per subject
            time_points: List of time points to create intervals

        Returns:
            DataFrame with multiple rows per subject, one for each time interval
        """
        # Validate input
        required_columns = [self.id_column, self.time_column, self.event_column]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Sort time points and ensure they start from 0
        time_points = sorted(time_points)
        if time_points[0] > 0:
            time_points = [0] + time_points

        # Create list to store interval data
        intervals = []

        # Process each subject
        for _, row in df.iterrows():
            subject_id = row[self.id_column]
            event_time = row[self.time_column]
            event_status = row[self.event_column]

            # Create intervals
            for i in range(len(time_points) - 1):
                start = time_points[i]
                stop = time_points[i + 1]

                # Skip if the subject had an event before this interval
                if event_time < start:
                    continue

                # Determine if event occurred in this interval
                if start <= event_time < stop:
                    # Event occurred in this interval
                    interval_event = event_status
                    interval_stop = event_time
                else:
                    # No event in this interval
                    interval_event = 0
                    interval_stop = min(stop, event_time)

                # Create interval record
                interval_data = {
                    self.id_column: subject_id,
                    self.start_time_column: start,
                    self.stop_time_column: interval_stop,
                    self.event_column: interval_event,
                }

                # Add all other columns from the original row
                for col, val in row.items():
                    if col not in [self.time_column] + list(interval_data.keys()):
                        interval_data[col] = val

                intervals.append(interval_data)

            # Add final interval if needed
            if event_time >= time_points[-1]:
                interval_data = {
                    self.id_column: subject_id,
                    self.start_time_column: time_points[-1],
                    self.stop_time_column: event_time,
                    self.event_column: event_status,
                }

                # Add all other columns from the original row
                for col, val in row.items():
                    if col not in [self.time_column] + list(interval_data.keys()):
                        interval_data[col] = val

                intervals.append(interval_data)

        # Convert to DataFrame
        intervals_df = pd.DataFrame(intervals)

        return intervals_df

    def fit_time_varying(
        self, df: pd.DataFrame, time_varying_features: Dict[str, List[float]]
    ) -> "TimeVaryingSurvivalAnalysis":
        """
        Fit a time-varying Cox model.

        Args:
            df: Input DataFrame with one row per subject
            time_varying_features: Dictionary mapping feature names to lists of values at different time points

        Returns:
            Fitted model instance
        """
        # Validate that all time-varying features have the same time points
        time_points_sets = [set(times) for times in time_varying_features.values()]
        if len(time_points_sets) > 1 and not all(
            s == time_points_sets[0] for s in time_points_sets
        ):
            raise ValueError("All time-varying features must have the same time points")

        # Get time points from the first feature
        if time_varying_features:
            feature_name = list(time_varying_features.keys())[0]
            time_points = sorted(time_varying_features[feature_name])
        else:
            raise ValueError("No time-varying features provided")

        # Create time intervals
        intervals_df = self._create_time_intervals(df, time_points)

        # Add time-varying feature values
        for feature_name, feature_values in time_varying_features.items():
            # Sort time points and values together
            time_value_pairs = sorted(zip(time_points, feature_values))
            sorted_times = [pair[0] for pair in time_value_pairs]
            sorted_values = [pair[1] for pair in time_value_pairs]

            # Function to get feature value for a given time
            def get_feature_value(t):
                # Find the index of the largest time point that's <= t
                idx = 0
                while idx < len(sorted_times) - 1 and sorted_times[idx + 1] <= t:
                    idx += 1
                return sorted_values[idx]

            # Add feature values based on start time
            intervals_df[feature_name] = intervals_df[self.start_time_column].apply(
                get_feature_value
            )

        # Fit the model
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model.fit(
                intervals_df,
                duration_col=self.stop_time_column,
                event_col=self.event_column,
                start_col=self.start_time_column,
                id_col=self.id_column,
            )

        logger.info(
            f"Fitted time-varying Cox model with {len(df)} subjects and {len(intervals_df)} intervals"
        )
        return self

    def predict_survival_function(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Predict the survival function for each sample.

        Args:
            X: Feature DataFrame

        Returns:
            DataFrame with survival probabilities at different time points
        """
        return self.model.predict_survival_function(X)

    def predict_median_survival_time(self, X: pd.DataFrame) -> pd.Series:
        """
        Predict the median survival time for each sample.

        Args:
            X: Feature DataFrame

        Returns:
            Series with median survival time predictions
        """
        return self.model.predict_median(X)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get feature importance from the model.

        Returns:
            DataFrame with feature importance metrics
        """
        # Get model summary
        summary = self.model.summary

        # Extract relevant columns
        importance = summary[["coef", "exp(coef)", "p"]]

        # Rename columns for clarity
        importance = importance.rename(
            columns={"coef": "coefficient", "exp(coef)": "hazard_ratio", "p": "p_value"}
        )

        # Add absolute coefficient as a measure of importance
        importance["importance"] = np.abs(importance["coefficient"])

        # Sort by importance
        importance = importance.sort_values("importance", ascending=False)

        return importance
