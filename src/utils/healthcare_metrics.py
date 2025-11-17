"""
Healthcare Metrics Module for Nexora

This module provides functionality for calculating and analyzing healthcare-specific
metrics and indicators, including risk scores, quality measures, and clinical outcomes.
It implements standard healthcare metrics such as readmission rates, mortality indices,
length of stay analysis, and various risk adjustment methodologies.
"""

import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.calibration import calibration_curve
from sklearn.metrics import (average_precision_score, precision_recall_curve,
                             roc_auc_score)

logger = logging.getLogger(__name__)


class HealthcareMetrics:
    """
    A class for calculating and analyzing healthcare-specific metrics.

    This class provides methods for evaluating clinical prediction models,
    calculating quality measures, and analyzing patient outcomes.
    """

    def __init__(
        self,
        patient_id_column: str = "patient_id",
        encounter_id_column: Optional[str] = "encounter_id",
        admission_date_column: Optional[str] = "admission_date",
        discharge_date_column: Optional[str] = "discharge_date",
        mortality_column: Optional[str] = "mortality",
        readmission_column: Optional[str] = "readmission",
        complication_column: Optional[str] = "complication",
        prediction_column: Optional[str] = "prediction",
        expected_column: Optional[str] = "expected",
    ):
        """
        Initialize the healthcare metrics calculator.

        Args:
            patient_id_column: Column name for patient identifiers
            encounter_id_column: Column name for encounter identifiers
            admission_date_column: Column name for admission dates
            discharge_date_column: Column name for discharge dates
            mortality_column: Column name for mortality indicators
            readmission_column: Column name for readmission indicators
            complication_column: Column name for complication indicators
            prediction_column: Column name for model predictions
            expected_column: Column name for expected outcomes
        """
        self.patient_id_column = patient_id_column
        self.encounter_id_column = encounter_id_column
        self.admission_date_column = admission_date_column
        self.discharge_date_column = discharge_date_column
        self.mortality_column = mortality_column
        self.readmission_column = readmission_column
        self.complication_column = complication_column
        self.prediction_column = prediction_column
        self.expected_column = expected_column

        logger.info("Initialized HealthcareMetrics calculator")

    def calculate_length_of_stay(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate length of stay for each encounter.

        Args:
            df: DataFrame with admission and discharge dates

        Returns:
            Series with length of stay in days
        """
        if self.admission_date_column not in df.columns:
            raise ValueError(
                f"Admission date column '{self.admission_date_column}' not found"
            )

        if self.discharge_date_column not in df.columns:
            raise ValueError(
                f"Discharge date column '{self.discharge_date_column}' not found"
            )

        # Ensure dates are datetime
        admission_dates = pd.to_datetime(df[self.admission_date_column])
        discharge_dates = pd.to_datetime(df[self.discharge_date_column])

        # Calculate length of stay in days
        los = (discharge_dates - admission_dates).dt.total_seconds() / (24 * 3600)

        return los

    def calculate_readmission_rate(
        self,
        df: pd.DataFrame,
        window_days: int = 30,
        condition_column: Optional[str] = None,
        condition_value: Optional[str] = None,
    ) -> float:
        """
        Calculate readmission rate within a specified time window.

        Args:
            df: DataFrame with patient encounters
            window_days: Time window in days for readmission
            condition_column: Column name for filtering condition
            condition_value: Value for filtering condition

        Returns:
            Readmission rate as a proportion
        """
        if self.patient_id_column not in df.columns:
            raise ValueError(f"Patient ID column '{self.patient_id_column}' not found")

        if self.discharge_date_column not in df.columns:
            raise ValueError(
                f"Discharge date column '{self.discharge_date_column}' not found"
            )

        if self.admission_date_column not in df.columns:
            raise ValueError(
                f"Admission date column '{self.admission_date_column}' not found"
            )

        # Apply condition filter if specified
        if condition_column and condition_value:
            if condition_column not in df.columns:
                raise ValueError(f"Condition column '{condition_column}' not found")

            filtered_df = df[df[condition_column] == condition_value].copy()
        else:
            filtered_df = df.copy()

        # Ensure dates are datetime
        filtered_df[self.discharge_date_column] = pd.to_datetime(
            filtered_df[self.discharge_date_column]
        )
        filtered_df[self.admission_date_column] = pd.to_datetime(
            filtered_df[self.admission_date_column]
        )

        # Sort by patient ID and admission date
        filtered_df = filtered_df.sort_values(
            [self.patient_id_column, self.admission_date_column]
        )

        # Initialize readmission indicator
        filtered_df["is_readmission"] = False

        # Calculate readmissions
        readmissions = 0
        total_discharges = 0

        # Group by patient
        for patient_id, patient_df in filtered_df.groupby(self.patient_id_column):
            # Skip patients with only one encounter
            if len(patient_df) <= 1:
                total_discharges += 1
                continue

            # Get sorted encounters
            encounters = patient_df.sort_values(self.admission_date_column).reset_index(
                drop=True
            )

            # Check each discharge
            for i in range(len(encounters) - 1):
                discharge_date = encounters.iloc[i][self.discharge_date_column]
                next_admission_date = encounters.iloc[i + 1][self.admission_date_column]

                # Calculate days between discharge and next admission
                days_between = (
                    next_admission_date - discharge_date
                ).total_seconds() / (24 * 3600)

                # Check if readmission is within window
                if 0 <= days_between <= window_days:
                    readmissions += 1
                    filtered_df.loc[encounters.iloc[i + 1].name, "is_readmission"] = (
                        True
                    )

                total_discharges += 1

        # Calculate readmission rate
        readmission_rate = (
            readmissions / total_discharges if total_discharges > 0 else 0
        )

        logger.info(
            f"Calculated {window_days}-day readmission rate: {readmission_rate:.4f}"
        )
        return readmission_rate

    def calculate_mortality_index(self, df: pd.DataFrame) -> float:
        """
        Calculate mortality index (observed/expected mortality).

        Args:
            df: DataFrame with mortality indicators and expected mortality

        Returns:
            Mortality index
        """
        if self.mortality_column not in df.columns:
            raise ValueError(f"Mortality column '{self.mortality_column}' not found")

        if self.expected_column not in df.columns:
            raise ValueError(f"Expected column '{self.expected_column}' not found")

        # Calculate observed mortality
        observed_mortality = df[self.mortality_column].mean()

        # Calculate expected mortality
        expected_mortality = df[self.expected_column].mean()

        # Calculate mortality index
        mortality_index = (
            observed_mortality / expected_mortality
            if expected_mortality > 0
            else np.nan
        )

        logger.info(f"Calculated mortality index: {mortality_index:.4f}")
        return mortality_index

    def calculate_complication_rate(
        self, df: pd.DataFrame, complication_type: Optional[str] = None
    ) -> float:
        """
        Calculate complication rate.

        Args:
            df: DataFrame with complication indicators
            complication_type: Specific complication type to calculate

        Returns:
            Complication rate as a proportion
        """
        if self.complication_column not in df.columns:
            raise ValueError(
                f"Complication column '{self.complication_column}' not found"
            )

        # Filter by complication type if specified
        if complication_type:
            if isinstance(df[self.complication_column].iloc[0], str):
                # Complication column contains string values
                complication_rate = (
                    df[self.complication_column] == complication_type
                ).mean()
            else:
                # Complication column contains boolean or numeric values
                complication_rate = df[self.complication_column].mean()
        else:
            # Calculate overall complication rate
            complication_rate = df[self.complication_column].mean()

        logger.info(f"Calculated complication rate: {complication_rate:.4f}")
        return complication_rate

    def calculate_standardized_mortality_ratio(
        self, df: pd.DataFrame, groupby_column: Optional[str] = None
    ) -> Union[float, pd.Series]:
        """
        Calculate standardized mortality ratio (SMR).

        Args:
            df: DataFrame with mortality indicators and expected mortality
            groupby_column: Column to group by for stratified SMR

        Returns:
            SMR as a float or Series if groupby_column is specified
        """
        if self.mortality_column not in df.columns:
            raise ValueError(f"Mortality column '{self.mortality_column}' not found")

        if self.expected_column not in df.columns:
            raise ValueError(f"Expected column '{self.expected_column}' not found")

        if groupby_column:
            if groupby_column not in df.columns:
                raise ValueError(f"Groupby column '{groupby_column}' not found")

            # Calculate SMR for each group
            grouped = df.groupby(groupby_column)
            observed = grouped[self.mortality_column].sum()
            expected = grouped[self.expected_column].sum()

            # Calculate SMR
            smr = observed / expected

            # Calculate confidence intervals
            smr_ci_lower = pd.Series(index=smr.index, dtype=float)
            smr_ci_upper = pd.Series(index=smr.index, dtype=float)

            for group in smr.index:
                obs = observed[group]
                exp = expected[group]

                # Calculate 95% confidence interval
                if obs > 0:
                    ci_lower = (obs / exp) * np.exp(-1.96 * np.sqrt(1 / obs))
                    ci_upper = (obs / exp) * np.exp(1.96 * np.sqrt(1 / obs))
                else:
                    ci_lower = 0
                    ci_upper = 3.69 / exp  # 95% CI for 0 observed events

                smr_ci_lower[group] = ci_lower
                smr_ci_upper[group] = ci_upper

            # Create result DataFrame
            result = pd.DataFrame(
                {
                    "observed": observed,
                    "expected": expected,
                    "smr": smr,
                    "ci_lower": smr_ci_lower,
                    "ci_upper": smr_ci_upper,
                }
            )

            return result

        else:
            # Calculate overall SMR
            observed = df[self.mortality_column].sum()
            expected = df[self.expected_column].sum()

            # Calculate SMR
            smr = observed / expected if expected > 0 else np.nan

            # Calculate 95% confidence interval
            if observed > 0:
                ci_lower = smr * np.exp(-1.96 * np.sqrt(1 / observed))
                ci_upper = smr * np.exp(1.96 * np.sqrt(1 / observed))
            else:
                ci_lower = 0
                ci_upper = (
                    3.69 / expected if expected > 0 else np.nan
                )  # 95% CI for 0 observed events

            logger.info(
                f"Calculated SMR: {smr:.4f} (95% CI: {ci_lower:.4f}-{ci_upper:.4f})"
            )

            return {
                "smr": smr,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
                "observed": observed,
                "expected": expected,
            }

    def calculate_risk_adjusted_readmission(
        self,
        df: pd.DataFrame,
        window_days: int = 30,
        groupby_column: Optional[str] = None,
    ) -> Union[float, pd.Series]:
        """
        Calculate risk-adjusted readmission rate.

        Args:
            df: DataFrame with readmission indicators and expected readmission
            window_days: Time window in days for readmission
            groupby_column: Column to group by for stratified rates

        Returns:
            Risk-adjusted readmission rate as a float or Series if groupby_column is specified
        """
        # First calculate raw readmission indicators if not present
        if self.readmission_column not in df.columns:
            logger.info(
                f"Readmission column not found, calculating {window_days}-day readmissions"
            )
            readmission_rate = self.calculate_readmission_rate(df, window_days)
            df = df.copy()
            df["is_readmission"] = False

            # Group by patient
            for patient_id, patient_df in df.groupby(self.patient_id_column):
                # Skip patients with only one encounter
                if len(patient_df) <= 1:
                    continue

                # Get sorted encounters
                encounters = patient_df.sort_values(
                    self.admission_date_column
                ).reset_index(drop=True)

                # Check each discharge
                for i in range(len(encounters) - 1):
                    discharge_date = pd.to_datetime(
                        encounters.iloc[i][self.discharge_date_column]
                    )
                    next_admission_date = pd.to_datetime(
                        encounters.iloc[i + 1][self.admission_date_column]
                    )

                    # Calculate days between discharge and next admission
                    days_between = (
                        next_admission_date - discharge_date
                    ).total_seconds() / (24 * 3600)

                    # Check if readmission is within window
                    if 0 <= days_between <= window_days:
                        df.loc[encounters.iloc[i + 1].name, "is_readmission"] = True

            self.readmission_column = "is_readmission"

        # Check for expected column
        if self.expected_column not in df.columns:
            raise ValueError(f"Expected column '{self.expected_column}' not found")

        if groupby_column:
            if groupby_column not in df.columns:
                raise ValueError(f"Groupby column '{groupby_column}' not found")

            # Calculate for each group
            grouped = df.groupby(groupby_column)
            observed = grouped[self.readmission_column].sum()
            expected = grouped[self.expected_column].sum()

            # Calculate risk-adjusted rate
            risk_adjusted = observed / expected if (expected > 0).all() else np.nan

            return risk_adjusted

        else:
            # Calculate overall risk-adjusted rate
            observed = df[self.readmission_column].sum()
            expected = df[self.expected_column].sum()

            # Calculate risk-adjusted rate
            risk_adjusted = observed / expected if expected > 0 else np.nan

            logger.info(
                f"Calculated risk-adjusted readmission rate: {risk_adjusted:.4f}"
            )
            return risk_adjusted

    def calculate_hospital_los_index(self, df: pd.DataFrame) -> float:
        """
        Calculate hospital length of stay index (observed/expected LOS).

        Args:
            df: DataFrame with admission and discharge dates and expected LOS

        Returns:
            LOS index
        """
        # Calculate observed LOS
        observed_los = self.calculate_length_of_stay(df)

        # Check for expected LOS column
        if self.expected_column not in df.columns:
            raise ValueError(f"Expected LOS column '{self.expected_column}' not found")

        # Calculate LOS index
        los_index = observed_los.mean() / df[self.expected_column].mean()

        logger.info(f"Calculated LOS index: {los_index:.4f}")
        return los_index

    def evaluate_clinical_model(
        self,
        df: pd.DataFrame,
        outcome_column: str,
        prediction_column: Optional[str] = None,
    ) -> Dict:
        """
        Evaluate a clinical prediction model.

        Args:
            df: DataFrame with outcomes and predictions
            outcome_column: Column name for actual outcomes
            prediction_column: Column name for model predictions

        Returns:
            Dictionary with evaluation metrics
        """
        if outcome_column not in df.columns:
            raise ValueError(f"Outcome column '{outcome_column}' not found")

        if prediction_column is None:
            prediction_column = self.prediction_column

        if prediction_column not in df.columns:
            raise ValueError(f"Prediction column '{prediction_column}' not found")

        # Calculate AUC
        try:
            auc = roc_auc_score(df[outcome_column], df[prediction_column])
        except:
            auc = np.nan
            logger.warning("Could not calculate AUC")

        # Calculate average precision
        try:
            ap = average_precision_score(df[outcome_column], df[prediction_column])
        except:
            ap = np.nan
            logger.warning("Could not calculate average precision")

        # Calculate calibration metrics
        try:
            prob_true, prob_pred = calibration_curve(
                df[outcome_column], df[prediction_column], n_bins=10
            )
            calibration_slope, calibration_intercept = np.polyfit(
                prob_pred, prob_true, 1
            )
        except:
            prob_true, prob_pred = np.array([]), np.array([])
            calibration_slope, calibration_intercept = np.nan, np.nan
            logger.warning("Could not calculate calibration metrics")

        # Calculate Brier score
        try:
            brier = np.mean((df[prediction_column] - df[outcome_column]) ** 2)
        except:
            brier = np.nan
            logger.warning("Could not calculate Brier score")

        # Calculate sensitivity and specificity at different thresholds
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
        sensitivity = {}
        specificity = {}
        ppv = {}
        npv = {}

        for threshold in thresholds:
            try:
                # Convert predictions to binary at threshold
                binary_preds = (df[prediction_column] >= threshold).astype(int)

                # Calculate metrics
                tp = np.sum((binary_preds == 1) & (df[outcome_column] == 1))
                tn = np.sum((binary_preds == 0) & (df[outcome_column] == 0))
                fp = np.sum((binary_preds == 1) & (df[outcome_column] == 0))
                fn = np.sum((binary_preds == 0) & (df[outcome_column] == 1))

                sens = tp / (tp + fn) if (tp + fn) > 0 else np.nan
                spec = tn / (tn + fp) if (tn + fp) > 0 else np.nan
                pos_pred_val = tp / (tp + fp) if (tp + fp) > 0 else np.nan
                neg_pred_val = tn / (tn + fn) if (tn + fn) > 0 else np.nan

                sensitivity[threshold] = sens
                specificity[threshold] = spec
                ppv[threshold] = pos_pred_val
                npv[threshold] = neg_pred_val
            except:
                sensitivity[threshold] = np.nan
                specificity[threshold] = np.nan
                ppv[threshold] = np.nan
                npv[threshold] = np.nan

        # Compile results
        results = {
            "auc": auc,
            "average_precision": ap,
            "calibration_slope": calibration_slope,
            "calibration_intercept": calibration_intercept,
            "brier_score": brier,
            "sensitivity": sensitivity,
            "specificity": specificity,
            "ppv": ppv,
            "npv": npv,
            "calibration_data": {
                "prob_true": prob_true.tolist(),
                "prob_pred": prob_pred.tolist(),
            },
        }

        logger.info(
            f"Model evaluation results: AUC={auc:.4f}, AP={ap:.4f}, Brier={brier:.4f}"
        )
        return results

    def plot_model_performance(
        self,
        evaluation_results: Dict,
        title: str = "Model Performance",
        figsize: Tuple[int, int] = (15, 10),
    ) -> plt.Figure:
        """
        Plot model performance metrics.

        Args:
            evaluation_results: Results from evaluate_clinical_model
            title: Plot title
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle(title, fontsize=16)

        # Plot calibration curve
        ax1 = axes[0, 0]
        prob_true = evaluation_results["calibration_data"]["prob_true"]
        prob_pred = evaluation_results["calibration_data"]["prob_pred"]

        if len(prob_true) > 0 and len(prob_pred) > 0:
            ax1.plot(prob_pred, prob_true, "s-", label="Calibration curve")
            ax1.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")

            # Add calibration metrics
            slope = evaluation_results["calibration_slope"]
            intercept = evaluation_results["calibration_intercept"]
            ax1.text(
                0.1,
                0.9,
                f"Slope: {slope:.2f}\nIntercept: {intercept:.2f}",
                transform=ax1.transAxes,
                bbox=dict(facecolor="white", alpha=0.8),
            )

        ax1.set_xlabel("Mean predicted probability")
        ax1.set_ylabel("Fraction of positives")
        ax1.set_title("Calibration Curve")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot sensitivity/specificity vs threshold
        ax2 = axes[0, 1]
        thresholds = sorted(evaluation_results["sensitivity"].keys())
        sensitivity = [evaluation_results["sensitivity"][t] for t in thresholds]
        specificity = [evaluation_results["specificity"][t] for t in thresholds]

        ax2.plot(thresholds, sensitivity, "o-", label="Sensitivity")
        ax2.plot(thresholds, specificity, "s-", label="Specificity")
        ax2.set_xlabel("Threshold")
        ax2.set_ylabel("Value")
        ax2.set_title("Sensitivity and Specificity vs Threshold")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        # Plot PPV/NPV vs threshold
        ax3 = axes[1, 0]
        ppv = [evaluation_results["ppv"][t] for t in thresholds]
        npv = [evaluation_results["npv"][t] for t in thresholds]

        ax3.plot(thresholds, ppv, "o-", label="PPV")
        ax3.plot(thresholds, npv, "s-", label="NPV")
        ax3.set_xlabel("Threshold")
        ax3.set_ylabel("Value")
        ax3.set_title("PPV and NPV vs Threshold")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Add summary metrics
        ax4 = axes[1, 1]
        ax4.axis("off")

        metrics_text = (
            f"AUC: {evaluation_results['auc']:.4f}\n"
            f"Average Precision: {evaluation_results['average_precision']:.4f}\n"
            f"Brier Score: {evaluation_results['brier_score']:.4f}\n\n"
            f"At threshold 0.5:\n"
            f"Sensitivity: {evaluation_results['sensitivity'].get(0.5, np.nan):.4f}\n"
            f"Specificity: {evaluation_results['specificity'].get(0.5, np.nan):.4f}\n"
            f"PPV: {evaluation_results['ppv'].get(0.5, np.nan):.4f}\n"
            f"NPV: {evaluation_results['npv'].get(0.5, np.nan):.4f}"
        )

        ax4.text(0.1, 0.5, metrics_text, fontsize=12, va="center")

        plt.tight_layout()
        plt.subplots_adjust(top=0.9)

        return fig

    def calculate_quality_metrics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate a comprehensive set of quality metrics.

        Args:
            df: DataFrame with patient data

        Returns:
            Dictionary with quality metrics
        """
        metrics = {}

        # Calculate length of stay metrics
        try:
            los = self.calculate_length_of_stay(df)
            metrics["mean_los"] = los.mean()
            metrics["median_los"] = los.median()
            metrics["los_std"] = los.std()

            # Calculate LOS index if expected column is available
            if self.expected_column in df.columns:
                metrics["los_index"] = self.calculate_hospital_los_index(df)
        except Exception as e:
            logger.warning(f"Could not calculate LOS metrics: {str(e)}")

        # Calculate readmission metrics
        try:
            metrics["readmission_30day"] = self.calculate_readmission_rate(
                df, window_days=30
            )
            metrics["readmission_7day"] = self.calculate_readmission_rate(
                df, window_days=7
            )

            # Calculate risk-adjusted readmission if expected column is available
            if self.expected_column in df.columns:
                metrics["risk_adjusted_readmission"] = (
                    self.calculate_risk_adjusted_readmission(df)
                )
        except Exception as e:
            logger.warning(f"Could not calculate readmission metrics: {str(e)}")

        # Calculate mortality metrics
        if self.mortality_column in df.columns:
            try:
                metrics["mortality_rate"] = df[self.mortality_column].mean()

                # Calculate mortality index if expected column is available
                if self.expected_column in df.columns:
                    metrics["mortality_index"] = self.calculate_mortality_index(df)
                    metrics["smr"] = self.calculate_standardized_mortality_ratio(df)
            except Exception as e:
                logger.warning(f"Could not calculate mortality metrics: {str(e)}")

        # Calculate complication metrics
        if self.complication_column in df.columns:
            try:
                metrics["complication_rate"] = self.calculate_complication_rate(df)
            except Exception as e:
                logger.warning(f"Could not calculate complication metrics: {str(e)}")

        logger.info(f"Calculated {len(metrics)} quality metrics")
        return metrics

    def calculate_stratified_metrics(
        self, df: pd.DataFrame, stratify_column: str
    ) -> Dict:
        """
        Calculate metrics stratified by a specific column.

        Args:
            df: DataFrame with patient data
            stratify_column: Column to stratify by

        Returns:
            Dictionary with stratified metrics
        """
        if stratify_column not in df.columns:
            raise ValueError(f"Stratify column '{stratify_column}' not found")

        # Get unique values in stratify column
        strata = df[stratify_column].unique()

        # Initialize results
        results = {}

        # Calculate metrics for each stratum
        for stratum in strata:
            stratum_df = df[df[stratify_column] == stratum]

            # Skip if stratum has too few samples
            if len(stratum_df) < 10:
                logger.warning(
                    f"Skipping stratum '{stratum}' with only {len(stratum_df)} samples"
                )
                continue

            # Calculate metrics for this stratum
            stratum_metrics = self.calculate_quality_metrics(stratum_df)

            # Store results
            results[stratum] = stratum_metrics

        logger.info(f"Calculated stratified metrics for {len(results)} strata")
        return results

    def calculate_observed_expected_ratio(
        self,
        df: pd.DataFrame,
        outcome_column: str,
        expected_column: Optional[str] = None,
    ) -> float:
        """
        Calculate the observed to expected ratio for an outcome.

        Args:
            df: DataFrame with outcome data
            outcome_column: Column name for the outcome
            expected_column: Column name for expected outcome probabilities

        Returns:
            O/E ratio
        """
        if outcome_column not in df.columns:
            raise ValueError(f"Outcome column '{outcome_column}' not found")

        if expected_column is None:
            expected_column = self.expected_column

        if expected_column not in df.columns:
            raise ValueError(f"Expected column '{expected_column}' not found")

        # Calculate observed rate
        observed = df[outcome_column].mean()

        # Calculate expected rate
        expected = df[expected_column].mean()

        # Calculate O/E ratio
        oe_ratio = observed / expected if expected > 0 else np.nan

        logger.info(f"Calculated O/E ratio for {outcome_column}: {oe_ratio:.4f}")
        return oe_ratio

    def calculate_risk_adjusted_rate(
        self,
        df: pd.DataFrame,
        outcome_column: str,
        expected_column: Optional[str] = None,
        reference_rate: Optional[float] = None,
    ) -> float:
        """
        Calculate risk-adjusted rate for an outcome.

        Args:
            df: DataFrame with outcome data
            outcome_column: Column name for the outcome
            expected_column: Column name for expected outcome probabilities
            reference_rate: Reference population rate (if None, uses the overall rate)

        Returns:
            Risk-adjusted rate
        """
        if outcome_column not in df.columns:
            raise ValueError(f"Outcome column '{outcome_column}' not found")

        if expected_column is None:
            expected_column = self.expected_column

        if expected_column not in df.columns:
            raise ValueError(f"Expected column '{expected_column}' not found")

        # Calculate O/E ratio
        oe_ratio = self.calculate_observed_expected_ratio(
            df, outcome_column, expected_column
        )

        # Determine reference rate
        if reference_rate is None:
            reference_rate = df[outcome_column].mean()

        # Calculate risk-adjusted rate
        adjusted_rate = oe_ratio * reference_rate

        logger.info(
            f"Calculated risk-adjusted rate for {outcome_column}: {adjusted_rate:.4f}"
        )
        return adjusted_rate

    def calculate_excess_events(
        self,
        df: pd.DataFrame,
        outcome_column: str,
        expected_column: Optional[str] = None,
    ) -> int:
        """
        Calculate excess events (observed - expected).

        Args:
            df: DataFrame with outcome data
            outcome_column: Column name for the outcome
            expected_column: Column name for expected outcome probabilities

        Returns:
            Number of excess events
        """
        if outcome_column not in df.columns:
            raise ValueError(f"Outcome column '{outcome_column}' not found")

        if expected_column is None:
            expected_column = self.expected_column

        if expected_column not in df.columns:
            raise ValueError(f"Expected column '{expected_column}' not found")

        # Calculate observed events
        observed = df[outcome_column].sum()

        # Calculate expected events
        expected = df[expected_column].sum()

        # Calculate excess events
        excess = observed - expected

        logger.info(f"Calculated excess {outcome_column} events: {excess:.1f}")
        return excess

    def plot_quality_dashboard(
        self,
        metrics: Dict,
        title: str = "Quality Metrics Dashboard",
        figsize: Tuple[int, int] = (15, 10),
    ) -> plt.Figure:
        """
        Plot a dashboard of quality metrics.

        Args:
            metrics: Dictionary with quality metrics
            title: Plot title
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=figsize)
        fig.suptitle(title, fontsize=16)

        # Plot length of stay metrics
        ax1 = axes[0, 0]
        los_metrics = {k: v for k, v in metrics.items() if "los" in k.lower()}
        if los_metrics:
            ax1.bar(los_metrics.keys(), los_metrics.values())
            ax1.set_title("Length of Stay Metrics")
            ax1.set_ylabel("Days / Index")
            ax1.tick_params(axis="x", rotation=45)
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, "No LOS metrics available", ha="center", va="center")
            ax1.set_title("Length of Stay Metrics")

        # Plot readmission metrics
        ax2 = axes[0, 1]
        readmission_metrics = {
            k: v for k, v in metrics.items() if "readmission" in k.lower()
        }
        if readmission_metrics:
            ax2.bar(readmission_metrics.keys(), readmission_metrics.values())
            ax2.set_title("Readmission Metrics")
            ax2.set_ylabel("Rate / Index")
            ax2.tick_params(axis="x", rotation=45)
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(
                0.5, 0.5, "No readmission metrics available", ha="center", va="center"
            )
            ax2.set_title("Readmission Metrics")

        # Plot mortality metrics
        ax3 = axes[1, 0]
        mortality_metrics = {
            k: v for k, v in metrics.items() if "mortality" in k.lower() or k == "smr"
        }
        if mortality_metrics:
            ax3.bar(mortality_metrics.keys(), mortality_metrics.values())
            ax3.set_title("Mortality Metrics")
            ax3.set_ylabel("Rate / Index")
            ax3.tick_params(axis="x", rotation=45)
            ax3.grid(True, alpha=0.3)
        else:
            ax3.text(
                0.5, 0.5, "No mortality metrics available", ha="center", va="center"
            )
            ax3.set_title("Mortality Metrics")

        # Plot other metrics
        ax4 = axes[1, 1]
        other_metrics = {
            k: v
            for k, v in metrics.items()
            if "los" not in k.lower()
            and "readmission" not in k.lower()
            and "mortality" not in k.lower()
            and k != "smr"
        }
        if other_metrics:
            ax4.bar(other_metrics.keys(), other_metrics.values())
            ax4.set_title("Other Quality Metrics")
            ax4.set_ylabel("Rate / Index")
            ax4.tick_params(axis="x", rotation=45)
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, "No other metrics available", ha="center", va="center")
            ax4.set_title("Other Quality Metrics")

        plt.tight_layout()
        plt.subplots_adjust(top=0.9)

        return fig

    def plot_stratified_metrics(
        self,
        stratified_metrics: Dict,
        metric_name: str,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 6),
    ) -> plt.Figure:
        """
        Plot a specific metric across different strata.

        Args:
            stratified_metrics: Dictionary with stratified metrics
            metric_name: Name of the metric to plot
            title: Plot title
            figsize: Figure size

        Returns:
            Matplotlib figure
        """
        # Extract values for the specified metric
        strata = []
        values = []

        for stratum, metrics in stratified_metrics.items():
            if metric_name in metrics:
                strata.append(stratum)
                values.append(metrics[metric_name])

        if not strata:
            raise ValueError(f"Metric '{metric_name}' not found in stratified metrics")

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Set title
        if title is None:
            title = f"{metric_name} by Stratum"
        fig.suptitle(title, fontsize=16)

        # Plot bars
        ax.bar(strata, values)

        # Add labels and grid
        ax.set_xlabel("Stratum")
        ax.set_ylabel(metric_name)
        ax.tick_params(axis="x", rotation=45)
        ax.grid(True, alpha=0.3)

        # Add value labels
        for i, v in enumerate(values):
            ax.text(i, v, f"{v:.4f}", ha="center", va="bottom")

        plt.tight_layout()

        return fig
