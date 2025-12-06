import pandas as pd
from lifelines import CoxPHFitter
import os
import pickle
from typing import Dict, Any, Optional
import logging
import os
import pickle

from .base_model import BaseModel

logger = logging.getLogger(__name__)


class SurvivalAnalysisModel(BaseModel):
    """
    Survival Analysis Model (Cox Proportional Hazards) for time-to-event prediction.
    Commonly used for predicting time to readmission, time to adverse event, etc.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.cph = CoxPHFitter()
        self.duration_col = config.get("duration_col", "time_to_event")
        self.event_col = config.get("event_col", "event_occurred")
        self.model_path = config.get(
            "model_path", f"models/{self.name}_{self.version}.pkl"
        )

    def train(
        self, train_data: pd.DataFrame, validation_data: Optional[pd.DataFrame] = None
    ):
        """
        Trains the Cox Proportional Hazards model.

        Args:
            train_data: DataFrame containing duration, event, and feature columns.
            validation_data: Optional DataFrame for validation (not directly used by lifelines CPH).
        """
        logger.info(f"Training Survival Analysis model {self.name} v{self.version}...")

        # Ensure required columns are present
        required_cols = [self.duration_col, self.event_col]
        if not all(col in train_data.columns for col in required_cols):
            raise ValueError(f"Training data must contain columns: {required_cols}")

        # Select feature columns (all others)
        feature_cols = [col for col in train_data.columns if col not in required_cols]

        # Fit the model
        # The formula argument is for more complex models, but we'll use the default fit method
        # which expects the dataframe to contain only the duration, event, and feature columns.
        fit_data = train_data[[self.duration_col, self.event_col] + feature_cols]
        self.cph.fit(fit_data, duration_col=self.duration_col, event_col=self.event_col)

        logger.info("Survival Analysis training complete.")
        # print(self.cph.print_summary())

    def predict(self, patient_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates survival function and median survival time predictions.

        Args:
            patient_data: DataFrame containing patient features (one row per patient).

        Returns:
            A dictionary with prediction results.
        """
        if patient_data.shape[0] != 1:
            raise ValueError(
                "Prediction expects a single patient record (one row DataFrame)."
            )

        # Predict the survival function (probability of survival over time)
        survival_function = self.cph.predict_survival_function(patient_data)

        # Predict the median survival time
        median_survival_time = self.cph.predict_median(patient_data).iloc[0]

        # Convert survival function to a serializable format (e.g., list of time/probability pairs)
        time_points = survival_function.index.tolist()
        probabilities = survival_function.iloc[:, 0].tolist()

        return {
            "median_survival_time": float(median_survival_time),
            "survival_function": {"time": time_points, "probability": probabilities},
            "risk_score": float(self.cph.predict_partial_hazard(patient_data).iloc[0]),
        }

    def save(self, path: Optional[str] = None):
        """Saves the model to the specified path."""
        save_path = path or self.model_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        # Use pickle for saving the lifelines model object
        with open(save_path, "wb") as f:
            pickle.dump(self.cph, f)
        logger.info(f"Survival Analysis model saved to {save_path}")

    def load(self, path: Optional[str] = None):
        """Loads the model from the specified path."""
        load_path = path or self.model_path
        # Use pickle for loading the lifelines model object
        with open(load_path, "rb") as f:
            self.cph = pickle.load(f)
        logger.info(f"Survival Analysis model loaded from {load_path}")

    def explain(self, patient_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Generates explanations based on the CoxPH model's coefficients.
        """
        # Get the coefficients (log-hazard ratios)
        summary = self.cph.summary

        # Sort by absolute coefficient value to find most influential features
        summary["abs_coef"] = summary["coef"].abs()
        top_features = summary.sort_values(by="abs_coef", ascending=False).head(5)

        explanation = {
            "explanation_method": "CoxPH Coefficients",
            "top_features": [
                {
                    "feature": row.name,
                    "log_hazard_ratio": row["coef"],
                    "p_value": row["p"],
                    "hazard_ratio": row["exp(coef)"],
                }
                for index, row in top_features.iterrows()
            ],
            "details": "Positive log-hazard ratio increases the risk (shortens survival time), negative decreases it.",
        }
        return explanation
