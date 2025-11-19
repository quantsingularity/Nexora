"""
Automated validation module for the readmission prediction pipeline.

This module provides utilities for validating both the functionality
and HIPAA compliance of the readmission prediction pipeline.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from ..hipaa_compliance.deidentifier import DeidentificationConfig, PHIDeidentifier
from ..hipaa_compliance.phi_detector import PHIDetector

logger = logging.getLogger(__name__)


class PipelineValidator:
    """
    Validator for the readmission prediction pipeline.

    This class provides methods for validating both the functionality
    and HIPAA compliance of the readmission prediction pipeline.
    """

    def __init__(
        self,
        output_dir: str = "validation_results",
        test_data_ratio: float = 0.2,
        random_seed: int = 42,
    ):
        """
        Initialize the pipeline validator.

        Args:
            output_dir: Directory for validation results
            test_data_ratio: Ratio of data to use for testing
            random_seed: Random seed for reproducibility
        """
        self.output_dir = output_dir
        self.test_data_ratio = test_data_ratio
        self.random_seed = random_seed
        self.phi_detector = PHIDetector()

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def validate_pipeline(
        self,
        data_path: str,
        model_path: str,
        patient_id_col: str = "patient_id",
        target_col: str = "readmission_risk",
        deidentification_config: Optional[DeidentificationConfig] = None,
    ) -> Dict[str, Any]:
        """
        Validate the entire readmission prediction pipeline.

        Args:
            data_path: Path to input data
            model_path: Path to trained model
            patient_id_col: Column name for patient ID
            target_col: Column name for target variable
            deidentification_config: Configuration for de-identification

        Returns:
            Dictionary containing validation results
        """
        # Load data
        data = self._load_data(data_path)

        # Split data into train and test sets
        train_data, test_data = train_test_split(
            data, test_size=self.test_data_ratio, random_state=self.random_seed
        )

        # Validate de-identification
        deidentification_results = self.validate_deidentification(
            test_data, deidentification_config
        )

        # Validate model performance
        model_results = self.validate_model_performance(
            test_data, model_path, patient_id_col, target_col
        )

        # Validate data pipeline
        pipeline_results = self.validate_data_pipeline(test_data, patient_id_col)

        # Combine results
        results = {
            "deidentification": deidentification_results,
            "model_performance": model_results,
            "data_pipeline": pipeline_results,
            "overall_status": (
                "pass"
                if all(
                    [
                        deidentification_results["status"] == "pass",
                        model_results["status"] == "pass",
                        pipeline_results["status"] == "pass",
                    ]
                )
                else "fail"
            ),
        }

        # Save results
        self._save_results(results, "pipeline_validation_results.json")

        return results

    def validate_deidentification(
        self, data: pd.DataFrame, config: Optional[DeidentificationConfig] = None
    ) -> Dict[str, Any]:
        """
        Validate de-identification of PHI.

        Args:
            data: Data to validate
            config: Configuration for de-identification

        Returns:
            Dictionary containing validation results
        """
        # Create de-identifier
        deidentifier = PHIDeidentifier(config if config else DeidentificationConfig())

        # Detect PHI in original data
        original_phi_report = self.phi_detector.generate_phi_report(data)

        # De-identify data
        deidentified_data = deidentifier.deidentify_dataframe(data)

        # Detect PHI in de-identified data
        deidentified_phi_report = self.phi_detector.generate_phi_report(
            deidentified_data
        )

        # Check if de-identification was successful
        phi_removed = len(deidentified_phi_report["summary"]["phi_columns"]) == 0

        # If PHI was not completely removed, check which columns still contain PHI
        remaining_phi = {}
        if not phi_removed:
            for col, details in deidentified_phi_report["column_details"].items():
                if details["risk_level"] in ["high", "medium"]:
                    remaining_phi[col] = details

        # Prepare results
        results = {
            "original_phi_columns": len(original_phi_report["summary"]["phi_columns"]),
            "remaining_phi_columns": len(
                deidentified_phi_report["summary"]["phi_columns"]
            ),
            "phi_types_detected": list(
                original_phi_report["summary"]["phi_types_detected"]
            ),
            "phi_types_remaining": (
                list(deidentified_phi_report["summary"]["phi_types_detected"])
                if "phi_types_detected" in deidentified_phi_report["summary"]
                else []
            ),
            "remaining_phi_details": remaining_phi,
            "status": "pass" if phi_removed else "fail",
        }

        # Save results
        self._save_results(results, "deidentification_validation_results.json")

        return results

    def validate_model_performance(
        self,
        data: pd.DataFrame,
        model_path: str,
        patient_id_col: str = "patient_id",
        target_col: str = "readmission_risk",
    ) -> Dict[str, Any]:
        """
        Validate model performance.

        Args:
            data: Data to validate
            model_path: Path to trained model
            patient_id_col: Column name for patient ID
            target_col: Column name for target variable

        Returns:
            Dictionary containing validation results
        """
        try:
            # Load model
            model = self._load_model(model_path)

            # Prepare features and target
            X, y = self._prepare_data_for_model(data, target_col)

            # Get predictions
            y_pred = model.predict(X)

            # Calculate metrics
            metrics = self._calculate_metrics(y, y_pred)

            # Check if model performance is acceptable
            auc_threshold = 0.7  # Minimum acceptable AUC
            precision_threshold = 0.6  # Minimum acceptable precision
            recall_threshold = 0.5  # Minimum acceptable recall

            performance_acceptable = (
                metrics["auc"] >= auc_threshold
                and metrics["precision"] >= precision_threshold
                and metrics["recall"] >= recall_threshold
            )

            # Prepare results
            results = {
                "metrics": metrics,
                "thresholds": {
                    "auc": auc_threshold,
                    "precision": precision_threshold,
                    "recall": recall_threshold,
                },
                "status": "pass" if performance_acceptable else "fail",
            }

            # Save results
            self._save_results(results, "model_performance_validation_results.json")

            return results

        except Exception as e:
            logger.error(f"Error validating model performance: {e}")

            # Return error results
            results = {"error": str(e), "status": "fail"}

            # Save results
            self._save_results(results, "model_performance_validation_results.json")

            return results

    def validate_data_pipeline(
        self, data: pd.DataFrame, patient_id_col: str = "patient_id"
    ) -> Dict[str, Any]:
        """
        Validate the data pipeline.

        Args:
            data: Data to validate
            patient_id_col: Column name for patient ID

        Returns:
            Dictionary containing validation results
        """
        # Check for missing values
        missing_values = data.isnull().sum().to_dict()

        # Check for duplicates
        duplicates = data.duplicated().sum()

        # Check data types
        data_types = {col: str(dtype) for col, dtype in data.dtypes.items()}

        # Check for outliers in numeric columns
        outliers = {}
        for col in data.select_dtypes(include=["number"]).columns:
            q1 = data[col].quantile(0.25)
            q3 = data[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers[col] = (
                (data[col] < lower_bound) | (data[col] > upper_bound)
            ).sum()

        # Check for consistency in categorical columns
        categorical_consistency = {}
        for col in data.select_dtypes(include=["object", "category"]).columns:
            value_counts = data[col].value_counts()
            categorical_consistency[col] = {
                "unique_values": len(value_counts),
                "top_value": value_counts.index[0] if not value_counts.empty else None,
                "top_value_count": (
                    value_counts.iloc[0] if not value_counts.empty else 0
                ),
            }

        # Check if data pipeline validation is acceptable
        missing_threshold = 0.1  # Maximum acceptable fraction of missing values
        duplicate_threshold = 0.05  # Maximum acceptable fraction of duplicates
        outlier_threshold = 0.1  # Maximum acceptable fraction of outliers

        missing_acceptable = all(
            count / len(data) <= missing_threshold for count in missing_values.values()
        )
        duplicate_acceptable = duplicates / len(data) <= duplicate_threshold
        outlier_acceptable = all(
            count / len(data) <= outlier_threshold for count in outliers.values()
        )

        pipeline_acceptable = (
            missing_acceptable and duplicate_acceptable and outlier_acceptable
        )

        # Prepare results
        results = {
            "missing_values": missing_values,
            "duplicates": duplicates,
            "data_types": data_types,
            "outliers": outliers,
            "categorical_consistency": categorical_consistency,
            "thresholds": {
                "missing": missing_threshold,
                "duplicates": duplicate_threshold,
                "outliers": outlier_threshold,
            },
            "status": "pass" if pipeline_acceptable else "fail",
        }

        # Save results
        self._save_results(results, "data_pipeline_validation_results.json")

        return results

    def _load_data(self, data_path: str) -> pd.DataFrame:
        """
        Load data from file.

        Args:
            data_path: Path to data file

        Returns:
            Loaded data as DataFrame
        """
        # Determine file type from extension
        _, ext = os.path.splitext(data_path)

        if ext.lower() == ".csv":
            return pd.read_csv(data_path)
        elif ext.lower() == ".parquet":
            return pd.read_parquet(data_path)
        elif ext.lower() in [".xls", ".xlsx"]:
            return pd.read_excel(data_path)
        elif ext.lower() == ".json":
            return pd.read_json(data_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _load_model(self, model_path: str) -> Any:
        """
        Load model from file.

        Args:
            model_path: Path to model file

        Returns:
            Loaded model
        """
        # Determine model type from extension
        _, ext = os.path.splitext(model_path)

        if ext.lower() == ".pkl":
            import joblib

            return joblib.load(model_path)
        elif ext.lower() == ".h5":
            from tensorflow import keras

            return keras.models.load_model(model_path)
        elif ext.lower() == ".pt":
            import torch

            return torch.load(model_path)
        else:
            raise ValueError(f"Unsupported model format: {ext}")

    def _prepare_data_for_model(
        self, data: pd.DataFrame, target_col: str
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare data for model prediction.

        Args:
            data: Data to prepare
            target_col: Column name for target variable

        Returns:
            Tuple of features and target
        """
        # Separate features and target
        X = data.drop(columns=[target_col])
        y = data[target_col]

        return X, y

    def _calculate_metrics(
        self, y_true: pd.Series, y_pred: np.ndarray
    ) -> Dict[str, float]:
        """
        Calculate performance metrics.

        Args:
            y_true: True target values
            y_pred: Predicted target values

        Returns:
            Dictionary of metrics
        """
        # For binary classification
        if len(np.unique(y_true)) == 2:
            # Calculate AUC
            auc = roc_auc_score(y_true, y_pred)

            # Calculate precision-recall curve
            precision, recall, thresholds = precision_recall_curve(y_true, y_pred)

            # Calculate average precision
            ap = average_precision_score(y_true, y_pred)

            # Calculate F1 score at optimal threshold
            f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
            optimal_idx = np.argmax(f1_scores)
            optimal_threshold = (
                thresholds[optimal_idx] if optimal_idx < len(thresholds) else 0.5
            )
            optimal_precision = precision[optimal_idx]
            optimal_recall = recall[optimal_idx]
            optimal_f1 = f1_scores[optimal_idx]

            return {
                "auc": float(auc),
                "average_precision": float(ap),
                "optimal_threshold": float(optimal_threshold),
                "precision": float(optimal_precision),
                "recall": float(optimal_recall),
                "f1": float(optimal_f1),
            }

        # For regression
        else:
            from sklearn.metrics import (
                mean_absolute_error,
                mean_squared_error,
                r2_score,
            )

            # Calculate MSE
            mse = mean_squared_error(y_true, y_pred)

            # Calculate RMSE
            rmse = np.sqrt(mse)

            # Calculate MAE
            mae = mean_absolute_error(y_true, y_pred)

            # Calculate R^2
            r2 = r2_score(y_true, y_pred)

            return {
                "mse": float(mse),
                "rmse": float(rmse),
                "mae": float(mae),
                "r2": float(r2),
            }

    def _save_results(self, results: Dict[str, Any], filename: str) -> None:
        """
        Save validation results to file.

        Args:
            results: Results to save
            filename: Name of output file
        """
        output_path = os.path.join(self.output_dir, filename)

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Saved validation results to {output_path}")


class AutomatedValidator:
    """
    Automated validator for the readmission prediction pipeline.

    This class provides methods for automating the validation process
    for the readmission prediction pipeline.
    """

    def __init__(
        self,
        data_dir: str = "data",
        model_dir: str = "models",
        output_dir: str = "validation_results",
        config_path: Optional[str] = None,
    ):
        """
        Initialize the automated validator.

        Args:
            data_dir: Directory containing data files
            model_dir: Directory containing model files
            output_dir: Directory for validation results
            config_path: Path to configuration file
        """
        self.data_dir = data_dir
        self.model_dir = model_dir
        self.output_dir = output_dir
        self.config_path = config_path

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Load configuration if provided
        self.config = self._load_config() if config_path else {}

        # Create validator
        self.validator = PipelineValidator(output_dir=output_dir)

    def run_automated_validation(self) -> Dict[str, Any]:
        """
        Run automated validation of the readmission prediction pipeline.

        Returns:
            Dictionary containing validation results
        """
        # Find data files
        data_files = self._find_data_files()

        # Find model files
        model_files = self._find_model_files()

        # Create de-identification config
        deidentification_config = self._create_deidentification_config()

        # Run validation for each data and model combination
        results = {}

        for data_file in data_files:
            data_name = os.path.basename(data_file)
            results[data_name] = {}

            for model_file in model_files:
                model_name = os.path.basename(model_file)

                logger.info(f"Validating {model_name} on {data_name}")

                try:
                    # Run validation
                    validation_result = self.validator.validate_pipeline(
                        data_path=data_file,
                        model_path=model_file,
                        patient_id_col=self.config.get("patient_id_col", "patient_id"),
                        target_col=self.config.get("target_col", "readmission_risk"),
                        deidentification_config=deidentification_config,
                    )

                    results[data_name][model_name] = validation_result

                except Exception as e:
                    logger.error(f"Error validating {model_name} on {data_name}: {e}")
                    results[data_name][model_name] = {"error": str(e), "status": "fail"}

        # Save overall results
        self._save_overall_results(results)

        return results

    def _find_data_files(self) -> List[str]:
        """
        Find data files in the data directory.

        Returns:
            List of paths to data files
        """
        data_files = []

        for root, _, files in os.walk(self.data_dir):
            for file in files:
                if file.endswith((".csv", ".parquet", ".xls", ".xlsx", ".json")):
                    data_files.append(os.path.join(root, file))

        return data_files

    def _find_model_files(self) -> List[str]:
        """
        Find model files in the model directory.

        Returns:
            List of paths to model files
        """
        model_files = []

        for root, _, files in os.walk(self.model_dir):
            for file in files:
                if file.endswith((".pkl", ".h5", ".pt")):
                    model_files.append(os.path.join(root, file))

        return model_files

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if not self.config_path:
            return {}

        with open(self.config_path, "r") as f:
            return json.load(f)

    def _create_deidentification_config(self) -> DeidentificationConfig:
        """
        Create de-identification configuration.

        Returns:
            De-identification configuration
        """
        if "deidentification" not in self.config:
            return DeidentificationConfig()

        deidentification_config = self.config["deidentification"]

        return DeidentificationConfig(
            hash_patient_ids=deidentification_config.get("hash_patient_ids", True),
            remove_names=deidentification_config.get("remove_names", True),
            remove_addresses=deidentification_config.get("remove_addresses", True),
            remove_dates_of_birth=deidentification_config.get(
                "remove_dates_of_birth", True
            ),
            remove_contact_info=deidentification_config.get(
                "remove_contact_info", True
            ),
            remove_mrns=deidentification_config.get("remove_mrns", True),
            remove_ssn=deidentification_config.get("remove_ssn", True),
            remove_device_ids=deidentification_config.get("remove_device_ids", True),
            age_threshold=deidentification_config.get("age_threshold", 89),
            salt=deidentification_config.get("salt"),
            shift_dates=deidentification_config.get("shift_dates", True),
            date_shift_strategy=deidentification_config.get(
                "date_shift_strategy", "patient"
            ),
            max_date_shift_days=deidentification_config.get("max_date_shift_days", 365),
            k_anonymity_threshold=deidentification_config.get(
                "k_anonymity_threshold", 5
            ),
        )

    def _save_overall_results(self, results: Dict[str, Any]) -> None:
        """
        Save overall validation results to file.

        Args:
            results: Results to save
        """
        output_path = os.path.join(self.output_dir, "overall_validation_results.json")

        # Calculate overall status
        overall_status = "pass"

        for data_name, data_results in results.items():
            for model_name, model_results in data_results.items():
                if model_results.get("status", "fail") == "fail":
                    overall_status = "fail"
                    break

        # Add overall status to results
        overall_results = {"results": results, "overall_status": overall_status}

        with open(output_path, "w") as f:
            json.dump(overall_results, f, indent=2, default=str)

        logger.info(f"Saved overall validation results to {output_path}")


# Command-line interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate readmission prediction pipeline"
    )
    parser.add_argument(
        "--data-dir", type=str, default="data", help="Directory containing data files"
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models",
        help="Directory containing model files",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="validation_results",
        help="Directory for validation results",
    )
    parser.add_argument("--config", type=str, help="Path to configuration file")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create validator
    validator = AutomatedValidator(
        data_dir=args.data_dir,
        model_dir=args.model_dir,
        output_dir=args.output_dir,
        config_path=args.config,
    )

    # Run validation
    results = validator.run_automated_validation()

    # Print overall status
    overall_status = "pass"

    for data_name, data_results in results.items():
        for model_name, model_results in data_results.items():
            if model_results.get("status", "fail") == "fail":
                overall_status = "fail"
                break

    print(f"Overall validation status: {overall_status}")
