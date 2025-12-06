"""
Batch Scoring Script for Nexora Clinical Models

This script handles batch prediction processes for clinical models in the Nexora platform.
It loads patient data from various sources, applies preprocessing, runs predictions through
deployed models, and outputs results to specified destinations.

Usage:
    python batch_scoring.py --model-id <model_id> --input-path <input_path> --output-path <output_path>
"""

import argparse
import logging
import os
import sys
import time
from typing import Optional
import pandas as pd
import requests

sys.path.append(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
)
from data.clinical_data_loader import ClinicalDataLoader
from data_pipeline.feature_engineering import FeatureEngineer
from serving.model_registry import ModelRegistry
from utils.config_loader import ConfigLoader
from utils.logging_utils import setup_logging

logger = logging.getLogger(__name__)


class BatchScorer:
    """Handles batch scoring for clinical prediction models"""

    def __init__(self, model_id: str, config_path: Optional[str] = None) -> Any:
        """
        Initialize the batch scorer

        Args:
            model_id: Identifier for the model to use for scoring
            config_path: Path to configuration file (optional)
        """
        self.model_id = model_id
        setup_logging()
        self.config = (
            ConfigLoader(config_path).load_config()
            if config_path
            else ConfigLoader().load_config()
        )
        self.batch_config = self.config.get("batch_scoring", {})
        self.model_registry = ModelRegistry(self.config.get("model_registry", {}))
        self.model, self.model_metadata = self.model_registry.load_model(model_id)
        logger.info(f"Initialized batch scorer for model: {model_id}")
        logger.info(f"Model metadata: {self.model_metadata}")
        self.feature_engineer = FeatureEngineer(
            self.config.get("feature_engineering", {})
        )

    def load_data(self, input_path: str) -> pd.DataFrame:
        """
        Load data from the specified input path

        Args:
            input_path: Path to input data (CSV, parquet, or FHIR server URL)

        Returns:
            DataFrame containing patient data
        """
        logger.info(f"Loading data from {input_path}")
        data_loader = ClinicalDataLoader(self.config.get("data_sources", {}))
        if input_path.startswith("fhir://"):
            data = data_loader.load_from_fhir(input_path)
        elif input_path.endswith(".csv"):
            data = data_loader.load_from_csv(input_path)
        elif input_path.endswith(".parquet"):
            data = data_loader.load_from_parquet(input_path)
        else:
            raise ValueError(f"Unsupported input format: {input_path}")
        logger.info(f"Loaded {len(data)} records")
        return data

    def preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess data for model input

        Args:
            data: Raw input data

        Returns:
            Preprocessed data ready for model input
        """
        logger.info("Preprocessing data")
        processed_data = self.feature_engineer.transform(data)
        required_features = self.model_metadata.get("features", [])
        missing_features = [
            f for f in required_features if f not in processed_data.columns
        ]
        if missing_features:
            logger.warning(f"Missing required features: {missing_features}")
            for feature in missing_features:
                processed_data[feature] = 0
        model_features = processed_data[required_features]
        logger.info(f"Preprocessed data shape: {model_features.shape}")
        return model_features

    def score_batch(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Generate predictions for the preprocessed features

        Args:
            features: Preprocessed features ready for model input

        Returns:
            DataFrame with original data and predictions
        """
        logger.info("Generating predictions")
        start_time = time.time()
        if self.batch_config.get("use_api", False):
            api_url = self.batch_config.get("api_endpoint")
            logger.info(f"Using API endpoint for predictions: {api_url}")
            batch_size = self.batch_config.get("api_batch_size", 1000)
            results = []
            for i in range(0, len(features), batch_size):
                batch = features.iloc[i : i + batch_size]
                payload = batch.to_dict(orient="records")
                response = requests.post(
                    api_url,
                    json={"instances": payload},
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code != 200:
                    logger.error(f"API request failed: {response.text}")
                    raise RuntimeError(
                        f"API request failed with status {response.status_code}"
                    )
                batch_results = response.json()["predictions"]
                results.extend(batch_results)
            predictions = pd.DataFrame(results)
        else:
            predictions = pd.DataFrame(
                self.model.predict_proba(features),
                columns=(
                    [f"prob_{i}" for i in range(self.model.n_classes_)]
                    if hasattr(self.model, "n_classes_")
                    else ["probability"]
                ),
            )
            if hasattr(self.model, "predict"):
                predictions["prediction"] = self.model.predict(features)
        if "patient_id" in features.index.names:
            predictions.index = features.index
        end_time = time.time()
        logger.info(
            f"Generated predictions for {len(features)} records in {end_time - start_time:.2f} seconds"
        )
        return predictions

    def save_results(self, predictions: pd.DataFrame, output_path: str) -> Any:
        """
        Save prediction results to the specified output path

        Args:
            predictions: DataFrame containing predictions
            output_path: Path to save results
        """
        logger.info(f"Saving results to {output_path}")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        if output_path.endswith(".csv"):
            predictions.to_csv(output_path, index=True)
        elif output_path.endswith(".parquet"):
            predictions.to_parquet(output_path, index=True)
        elif output_path.endswith(".json"):
            predictions.to_json(output_path, orient="records", lines=True)
        else:
            raise ValueError(f"Unsupported output format: {output_path}")
        logger.info(f"Results saved successfully")

    def run(self, input_path: str, output_path: str) -> Any:
        """
        Run the full batch scoring pipeline

        Args:
            input_path: Path to input data
            output_path: Path to save results
        """
        logger.info(f"Starting batch scoring run for model {self.model_id}")
        try:
            data = self.load_data(input_path)
            features = self.preprocess_data(data)
            predictions = self.score_batch(features)
            self.save_results(predictions, output_path)
            logger.info("Batch scoring completed successfully")
        except Exception as e:
            logger.error(f"Batch scoring failed: {str(e)}", exc_info=True)
            raise


def parse_args() -> Any:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Batch scoring for clinical prediction models"
    )
    parser.add_argument("--model-id", required=True, help="Model identifier")
    parser.add_argument("--input-path", required=True, help="Path to input data")
    parser.add_argument("--output-path", required=True, help="Path to save results")
    parser.add_argument("--config", help="Path to configuration file")
    return parser.parse_args()


def main() -> Any:
    """Main entry point"""
    args = parse_args()
    try:
        scorer = BatchScorer(args.model_id, args.config)
        scorer.run(args.input_path, args.output_path)
        return 0
    except Exception as e:
        logger.error(f"Error in batch scoring: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
