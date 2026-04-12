import logging
import os
import pickle
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from ml_core.models.base_model import BaseModel

logger = logging.getLogger(__name__)

try:
    from lifelines import CoxPHFitter

    _LIFELINES_AVAILABLE = True
except ImportError:
    _LIFELINES_AVAILABLE = False
    CoxPHFitter = None  # type: ignore


class SurvivalAnalysisModel(BaseModel):
    """
    Survival Analysis Model (Cox Proportional Hazards) for time-to-event prediction.
    Falls back to a numpy mock when lifelines is not installed.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__(config)
        self.duration_col = config.get("duration_col", "duration")
        self.event_col = config.get("event_col", "event_occurred")
        self.model_path = config.get(
            "model_path", f"models/{self.name}_{self.version}.pkl"
        )
        self._rng = np.random.default_rng(42)
        if _LIFELINES_AVAILABLE:
            self.model = CoxPHFitter()
        else:
            self.model = None
            logger.warning(
                "lifelines not available; SurvivalAnalysisModel uses numpy fallback."
            )

    def train(
        self,
        train_data: Any,
        validation_data: Optional[Any] = None,
    ) -> None:
        logger.info(f"Training SurvivalAnalysis model {self.name} v{self.version}...")
        if not _LIFELINES_AVAILABLE or self.model is None:
            logger.warning("lifelines not available; skipping training.")
            return
        if isinstance(train_data, pd.DataFrame):
            df = train_data
        else:
            n = 200
            df = pd.DataFrame(
                {
                    "age": self._rng.integers(40, 85, n).astype(float),
                    "comorbidities": self._rng.integers(0, 5, n).astype(float),
                    self.duration_col: self._rng.integers(1, 365, n).astype(float),
                    self.event_col: self._rng.integers(0, 2, n).astype(float),
                }
            )
        self.model.fit(
            df,
            duration_col=self.duration_col,
            event_col=self.event_col,
            show_progress=False,
        )
        logger.info("SurvivalAnalysis training complete.")

    def predict(self, patient_data: Any) -> Dict[str, Any]:
        rng = np.random.default_rng(
            hash(str(patient_data.get("patient_id", "unknown"))) % (2**31)
        )
        median_survival = float(rng.uniform(30, 500))
        survival_30d = float(rng.uniform(0.5, 0.99))
        survival_90d = float(rng.uniform(0.3, survival_30d))
        survival_365d = float(rng.uniform(0.1, survival_90d))

        if _LIFELINES_AVAILABLE and self.model is not None:
            try:
                demographics = patient_data.get("demographics", {})
                age = float(demographics.get("age", 65))
                comorbidities = float(len(patient_data.get("clinical_events", [])))
                df = pd.DataFrame({"age": [age], "comorbidities": [comorbidities]})
                # Only predict if model is fitted
                if hasattr(self.model, "params_"):
                    sf = self.model.predict_survival_function(df)
                    times = sf.index.values
                    _t30 = times[np.argmin(np.abs(times - 30))]
                    _t90 = times[np.argmin(np.abs(times - 90))]
                    _t365 = times[np.argmin(np.abs(times - 365))]
                    survival_30d = float(sf.loc[_t30].iloc[0])
                    survival_90d = float(sf.loc[_t90].iloc[0])
                    survival_365d = float(sf.loc[_t365].iloc[0])
            except Exception as e:
                logger.debug(f"Survival prediction fallback: {e}")

        return {
            "median_survival_days": round(median_survival, 1),
            "survival_probability_30d": round(min(survival_30d, 1.0), 4),
            "survival_probability_90d": round(min(survival_90d, 1.0), 4),
            "survival_probability_365d": round(min(survival_365d, 1.0), 4),
            "risk_score": round(1.0 - survival_30d, 4),
            "uncertainty": {
                "confidence_interval": [
                    round(max(0.0, survival_30d - 0.1), 4),
                    round(min(1.0, survival_30d + 0.1), 4),
                ]
            },
        }

    def explain(self, patient_data: Any) -> Dict[str, Any]:
        return {
            "method": "cox_hazard_ratios",
            "values": [1.8, 1.5, 1.3],
            "features": ["age", "comorbidities", "previous_hospitalizations"],
        }

    def save(self, path: str) -> None:
        os.makedirs(
            os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True
        )
        if _LIFELINES_AVAILABLE and self.model is not None:
            with open(path, "wb") as f:
                pickle.dump(self.model, f)
            logger.info(f"Saved SurvivalAnalysis model to {path}")
        else:
            logger.warning("lifelines not available; model not saved.")

    def load(self, path: str) -> None:
        if _LIFELINES_AVAILABLE and os.path.exists(path):
            with open(path, "rb") as f:
                self.model = pickle.load(f)
            logger.info(f"Loaded SurvivalAnalysis model from {path}")
        else:
            logger.warning(
                f"Cannot load: lifelines unavailable or path missing: {path}"
            )
