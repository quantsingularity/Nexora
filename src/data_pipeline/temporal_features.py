"""
Temporal Features Module for Nexora

This module provides functionality for extracting and processing temporal features
from clinical time series data. It includes utilities for handling irregular sampling,
missing values, and creating derived features based on temporal patterns.
"""

import logging
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import signal, stats
from sklearn.base import BaseEstimator, TransformerMixin

logger = logging.getLogger(__name__)


class TemporalFeatureExtractor(BaseEstimator, TransformerMixin):
    """
    A class for extracting features from temporal clinical data.

    This extractor handles various types of time series data, including lab values,
    vital signs, and medication administrations, and creates features that capture
    temporal patterns and trends.
    """

    def __init__(
        self,
        time_column: str = "timestamp",
        patient_id_column: str = "patient_id",
        value_column: Optional[str] = "value",
        window_sizes: List[int] = [1, 3, 7, 14, 30],
        aggregation_functions: List[str] = ["mean", "min", "max", "std", "count"],
        include_trends: bool = True,
        handle_missing: str = "interpolate",
        reference_time_column: Optional[str] = None,
    ):
        """
        Initialize the temporal feature extractor.

        Args:
            time_column: Column name containing timestamps
            patient_id_column: Column name for patient ID
            value_column: Column name containing the values to analyze
            window_sizes: List of window sizes in days for feature extraction
            aggregation_functions: List of aggregation functions to apply
            include_trends: Whether to include trend features
            handle_missing: Strategy for handling missing values ('interpolate', 'forward', 'drop')
            reference_time_column: Column name for reference time (e.g., prediction time)
        """
        self.time_column = time_column
        self.patient_id_column = patient_id_column
        self.value_column = value_column
        self.window_sizes = window_sizes
        self.aggregation_functions = aggregation_functions
        self.include_trends = include_trends
        self.handle_missing = handle_missing
        self.reference_time_column = reference_time_column

        # Validate aggregation functions
        valid_aggs = [
            "mean",
            "min",
            "max",
            "median",
            "std",
            "var",
            "count",
            "sum",
            "range",
            "iqr",
            "slope",
        ]
        for agg in self.aggregation_functions:
            if agg not in valid_aggs:
                raise ValueError(
                    f"Unsupported aggregation function: {agg}. Supported functions: {valid_aggs}"
                )

        logger.info(
            f"Initialized TemporalFeatureExtractor with window sizes: {window_sizes}"
        )

    def _validate_dataframe(self, df: pd.DataFrame) -> None:
        """
        Validate that the input DataFrame has the required columns.

        Args:
            df: Input DataFrame

        Raises:
            ValueError: If required columns are missing
        """
        required_columns = [self.time_column, self.patient_id_column]
        if self.value_column:
            required_columns.append(self.value_column)
        if self.reference_time_column:
            required_columns.append(self.reference_time_column)

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

    def _preprocess_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the input DataFrame for feature extraction.

        Args:
            df: Input DataFrame

        Returns:
            Preprocessed DataFrame
        """
        # Make a copy to avoid modifying the original
        df_copy = df.copy()

        # Ensure timestamp column is datetime
        if not pd.api.types.is_datetime64_any_dtype(df_copy[self.time_column]):
            df_copy[self.time_column] = pd.to_datetime(df_copy[self.time_column])

        # Ensure reference time column is datetime if provided
        if self.reference_time_column and not pd.api.types.is_datetime64_any_dtype(
            df_copy[self.reference_time_column]
        ):
            df_copy[self.reference_time_column] = pd.to_datetime(
                df_copy[self.reference_time_column]
            )

        # Sort by patient ID and timestamp
        df_copy = df_copy.sort_values([self.patient_id_column, self.time_column])

        # Handle missing values if value column is provided
        if self.value_column and self.handle_missing != "drop":
            if self.handle_missing == "interpolate":
                # Group by patient and interpolate missing values
                df_copy[self.value_column] = df_copy.groupby(self.patient_id_column)[
                    self.value_column
                ].transform(lambda x: x.interpolate(method="time"))
            elif self.handle_missing == "forward":
                # Group by patient and forward fill missing values
                df_copy[self.value_column] = df_copy.groupby(self.patient_id_column)[
                    self.value_column
                ].transform(lambda x: x.fillna(method="ffill"))

        return df_copy

    def _compute_aggregation(self, series: pd.Series, agg_func: str) -> float:
        """
        Compute aggregation on a series based on the specified function.

        Args:
            series: Input series
            agg_func: Aggregation function name

        Returns:
            Aggregated value
        """
        if series.empty:
            return np.nan

        if agg_func == "mean":
            return series.mean()
        elif agg_func == "min":
            return series.min()
        elif agg_func == "max":
            return series.max()
        elif agg_func == "median":
            return series.median()
        elif agg_func == "std":
            return series.std()
        elif agg_func == "var":
            return series.var()
        elif agg_func == "count":
            return series.count()
        elif agg_func == "sum":
            return series.sum()
        elif agg_func == "range":
            return series.max() - series.min()
        elif agg_func == "iqr":
            q75, q25 = np.percentile(series.dropna(), [75, 25])
            return q75 - q25
        elif agg_func == "slope":
            if len(series) < 2:
                return 0
            # Calculate slope of linear regression
            x = np.arange(len(series))
            slope, _, _, _, _ = stats.linregress(x, series)
            return slope
        else:
            raise ValueError(f"Unsupported aggregation function: {agg_func}")

    def _extract_window_features(
        self, patient_data: pd.DataFrame, reference_time: pd.Timestamp
    ) -> Dict[str, float]:
        """
        Extract features from a patient's data within specified time windows.

        Args:
            patient_data: DataFrame containing a single patient's data
            reference_time: Reference time for window calculation

        Returns:
            Dictionary of extracted features
        """
        features = {}

        # Skip if no value column is provided
        if not self.value_column:
            return features

        # Extract features for each window size
        for window_size in self.window_sizes:
            # Calculate window start time
            window_start = reference_time - pd.Timedelta(days=window_size)

            # Filter data within the window
            window_data = patient_data[
                (patient_data[self.time_column] >= window_start)
                & (patient_data[self.time_column] <= reference_time)
            ]

            # Skip if no data in window
            if window_data.empty:
                for agg_func in self.aggregation_functions:
                    feature_name = f"{self.value_column}_{window_size}d_{agg_func}"
                    features[feature_name] = np.nan
                continue

            # Compute aggregations
            for agg_func in self.aggregation_functions:
                feature_name = f"{self.value_column}_{window_size}d_{agg_func}"
                features[feature_name] = self._compute_aggregation(
                    window_data[self.value_column], agg_func
                )

            # Add trend features if requested
            if self.include_trends and len(window_data) >= 2:
                # Calculate time since first and last measurement
                first_time = window_data[self.time_column].min()
                last_time = window_data[self.time_column].max()

                features[f"{self.value_column}_{window_size}d_time_since_first"] = (
                    reference_time - first_time
                ).total_seconds() / 86400  # days
                features[f"{self.value_column}_{window_size}d_time_since_last"] = (
                    reference_time - last_time
                ).total_seconds() / 86400  # days

                # Calculate trend (slope)
                if len(window_data) >= 3:
                    # Convert timestamps to numeric (days from start)
                    window_data = window_data.copy()
                    window_data["days_from_start"] = (
                        window_data[self.time_column]
                        - window_data[self.time_column].min()
                    ).dt.total_seconds() / 86400

                    # Calculate slope
                    slope, intercept, r_value, p_value, std_err = stats.linregress(
                        window_data["days_from_start"], window_data[self.value_column]
                    )

                    features[f"{self.value_column}_{window_size}d_slope"] = slope
                    features[f"{self.value_column}_{window_size}d_r_squared"] = (
                        r_value**2
                    )
                    features[f"{self.value_column}_{window_size}d_p_value"] = p_value

        return features

    def _extract_frequency_features(
        self, patient_data: pd.DataFrame, reference_time: pd.Timestamp
    ) -> Dict[str, float]:
        """
        Extract frequency-based features from a patient's time series data.

        Args:
            patient_data: DataFrame containing a single patient's data
            reference_time: Reference time for window calculation

        Returns:
            Dictionary of extracted frequency features
        """
        features = {}

        # Skip if no value column is provided or not enough data points
        if not self.value_column or len(patient_data) < 5:
            return features

        # Use the largest window size for frequency analysis
        max_window_size = max(self.window_sizes)
        window_start = reference_time - pd.Timedelta(days=max_window_size)

        # Filter data within the window
        window_data = patient_data[
            (patient_data[self.time_column] >= window_start)
            & (patient_data[self.time_column] <= reference_time)
        ]

        # Skip if not enough data in window
        if len(window_data) < 5:
            return features

        # Resample to regular intervals (daily)
        # First, set timestamp as index
        window_data = window_data.set_index(self.time_column)

        # Resample to daily frequency
        daily_data = window_data[self.value_column].resample("D").mean()

        # Interpolate missing values
        daily_data = daily_data.interpolate(method="linear")

        # Skip if still not enough data
        if len(daily_data) < 5:
            return features

        # Calculate basic frequency features

        # 1. Autocorrelation at different lags
        for lag in [1, 2, 3, 7]:
            if len(daily_data) > lag:
                autocorr = daily_data.autocorr(lag=lag)
                features[f"{self.value_column}_autocorr_lag{lag}"] = autocorr

        # 2. Spectral entropy (measure of signal complexity)
        freqs, psd = signal.welch(
            daily_data.dropna().values, fs=1.0, nperseg=min(len(daily_data), 10)
        )
        psd_norm = psd / psd.sum()
        spectral_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-10))
        features[f"{self.value_column}_spectral_entropy"] = spectral_entropy

        # 3. Dominant frequency
        if len(freqs) > 0 and len(psd) > 0:
            dominant_freq_idx = np.argmax(psd)
            dominant_freq = freqs[dominant_freq_idx]
            features[f"{self.value_column}_dominant_freq"] = dominant_freq
            features[f"{self.value_column}_dominant_freq_power"] = psd[
                dominant_freq_idx
            ]

        return features

    def _extract_event_features(
        self, patient_data: pd.DataFrame, reference_time: pd.Timestamp
    ) -> Dict[str, float]:
        """
        Extract features based on event occurrences (without using value column).

        Args:
            patient_data: DataFrame containing a single patient's data
            reference_time: Reference time for window calculation

        Returns:
            Dictionary of extracted event features
        """
        features = {}

        # Extract features for each window size
        for window_size in self.window_sizes:
            # Calculate window start time
            window_start = reference_time - pd.Timedelta(days=window_size)

            # Filter data within the window
            window_data = patient_data[
                (patient_data[self.time_column] >= window_start)
                & (patient_data[self.time_column] <= reference_time)
            ]

            # Count events in window
            event_count = len(window_data)
            features[f"event_count_{window_size}d"] = event_count

            if event_count > 0:
                # Time since most recent event
                most_recent = window_data[self.time_column].max()
                features[f"days_since_last_event_{window_size}d"] = (
                    reference_time - most_recent
                ).total_seconds() / 86400

                # Average time between events
                if event_count > 1:
                    # Sort timestamps
                    timestamps = sorted(window_data[self.time_column])

                    # Calculate time differences in days
                    time_diffs = [
                        (timestamps[i + 1] - timestamps[i]).total_seconds() / 86400
                        for i in range(len(timestamps) - 1)
                    ]

                    features[f"mean_days_between_events_{window_size}d"] = np.mean(
                        time_diffs
                    )
                    features[f"std_days_between_events_{window_size}d"] = (
                        np.std(time_diffs) if len(time_diffs) > 1 else 0
                    )
                    features[f"max_days_between_events_{window_size}d"] = np.max(
                        time_diffs
                    )
                    features[f"min_days_between_events_{window_size}d"] = np.min(
                        time_diffs
                    )

        return features

    def fit(self, X: pd.DataFrame, y=None):
        """
        Fit the transformer (no-op for this transformer).

        Args:
            X: Input DataFrame
            y: Target variable (not used)

        Returns:
            self
        """
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame by extracting temporal features.

        Args:
            X: Input DataFrame

        Returns:
            DataFrame with extracted features
        """
        # Validate input
        self._validate_dataframe(X)

        # Preprocess DataFrame
        df = self._preprocess_dataframe(X)

        # Initialize results
        all_features = []

        # Group by patient
        patient_groups = df.groupby(self.patient_id_column)

        for patient_id, patient_data in patient_groups:
            # Determine reference times
            if self.reference_time_column:
                # Use provided reference times
                reference_times = patient_data[self.reference_time_column].unique()
            else:
                # Use the latest timestamp as reference
                reference_times = [patient_data[self.time_column].max()]

            # Extract features for each reference time
            for reference_time in reference_times:
                # Initialize patient features
                patient_features = {self.patient_id_column: patient_id}

                if self.reference_time_column:
                    patient_features[self.reference_time_column] = reference_time

                # Extract window-based features if value column is provided
                if self.value_column:
                    window_features = self._extract_window_features(
                        patient_data, reference_time
                    )
                    patient_features.update(window_features)

                    # Extract frequency features
                    freq_features = self._extract_frequency_features(
                        patient_data, reference_time
                    )
                    patient_features.update(freq_features)

                # Extract event-based features
                event_features = self._extract_event_features(
                    patient_data, reference_time
                )
                patient_features.update(event_features)

                all_features.append(patient_features)

        # Convert to DataFrame
        result = pd.DataFrame(all_features)

        # Set index if reference time column is provided
        if self.reference_time_column:
            result = result.set_index(
                [self.patient_id_column, self.reference_time_column]
            )
        else:
            result = result.set_index(self.patient_id_column)

        return result


class MultiVariateTemporalFeatures:
    """
    A class for extracting features from multiple temporal variables.

    This class handles multiple time series variables for each patient and
    combines them into a single feature set.
    """

    def __init__(
        self,
        time_column: str = "timestamp",
        patient_id_column: str = "patient_id",
        variable_column: str = "variable",
        value_column: str = "value",
        window_sizes: List[int] = [1, 3, 7, 14, 30],
        aggregation_functions: List[str] = ["mean", "min", "max", "std", "count"],
        include_trends: bool = True,
        handle_missing: str = "interpolate",
        reference_time_column: Optional[str] = None,
    ):
        """
        Initialize the multivariate temporal feature extractor.

        Args:
            time_column: Column name containing timestamps
            patient_id_column: Column name for patient ID
            variable_column: Column name containing variable names
            value_column: Column name containing the values to analyze
            window_sizes: List of window sizes in days for feature extraction
            aggregation_functions: List of aggregation functions to apply
            include_trends: Whether to include trend features
            handle_missing: Strategy for handling missing values
            reference_time_column: Column name for reference time
        """
        self.time_column = time_column
        self.patient_id_column = patient_id_column
        self.variable_column = variable_column
        self.value_column = value_column
        self.window_sizes = window_sizes
        self.aggregation_functions = aggregation_functions
        self.include_trends = include_trends
        self.handle_missing = handle_missing
        self.reference_time_column = reference_time_column

        logger.info(
            f"Initialized MultiVariateTemporalFeatures with {len(window_sizes)} window sizes"
        )

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform the input DataFrame by extracting temporal features for each variable.

        Args:
            df: Input DataFrame in long format (each row is a measurement)

        Returns:
            DataFrame with extracted features
        """
        # Validate required columns
        required_columns = [
            self.time_column,
            self.patient_id_column,
            self.variable_column,
            self.value_column,
        ]
        if self.reference_time_column:
            required_columns.append(self.reference_time_column)

        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Get unique variables
        variables = df[self.variable_column].unique()

        # Initialize results
        all_features_dfs = []

        # Process each variable separately
        for variable in variables:
            logger.info(f"Processing variable: {variable}")

            # Filter data for this variable
            variable_data = df[df[self.variable_column] == variable].copy()

            # Create a feature extractor for this variable
            extractor = TemporalFeatureExtractor(
                time_column=self.time_column,
                patient_id_column=self.patient_id_column,
                value_column=self.value_column,
                window_sizes=self.window_sizes,
                aggregation_functions=self.aggregation_functions,
                include_trends=self.include_trends,
                handle_missing=self.handle_missing,
                reference_time_column=self.reference_time_column,
            )

            # Extract features
            variable_features = extractor.transform(variable_data)

            # Rename columns to include variable name
            if self.value_column in variable_features.columns:
                # For direct value columns
                variable_features = variable_features.rename(
                    columns={self.value_column: f"{variable}_{self.value_column}"}
                )

            # For derived feature columns
            new_columns = {}
            for col in variable_features.columns:
                if col == self.patient_id_column or col == self.reference_time_column:
                    continue

                if col.startswith(self.value_column):
                    new_col = col.replace(self.value_column, variable)
                    new_columns[col] = new_col
                elif col.startswith("event_count") or col.startswith(
                    "days_since_last_event"
                ):
                    new_col = f"{variable}_{col}"
                    new_columns[col] = new_col

            variable_features = variable_features.rename(columns=new_columns)

            # Add to results
            all_features_dfs.append(variable_features)

        # Combine all features
        if not all_features_dfs:
            return pd.DataFrame()

        # Determine how to join based on index structure
        if self.reference_time_column:
            # Multi-index with patient_id and reference_time
            result = pd.concat(all_features_dfs, axis=1)

            # Remove duplicate columns (patient_id, reference_time)
            result = result.loc[:, ~result.columns.duplicated()]

        else:
            # Single index with patient_id
            result = pd.concat(all_features_dfs, axis=1)

            # Remove duplicate columns
            result = result.loc[:, ~result.columns.duplicated()]

        return result
