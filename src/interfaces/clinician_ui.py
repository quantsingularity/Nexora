import logging
from typing import Dict, Any
import pandas as pd
from datetime import datetime

from ..model_factory.model_registry import ModelRegistry
from ..utils.fhir_connector import FHIRConnector
from ..monitoring.clinical_metrics import ClinicalMetrics
from ..monitoring.adverse_event_reporting import AdverseEventReporter

logger = logging.getLogger(__name__)


class ClinicianUIBackend:
    """
    Backend logic for the Clinician User Interface.

    This class aggregates data from various services (FHIR, Model Registry, Monitoring)
    to provide a comprehensive view for a clinician.
    """

    def __init__(self):
        # Initialize components
        # Note: FHIRConnector is initialized with a mock URL, assuming it handles the mock data
        self.fhir_connector = FHIRConnector(base_url="http://mock-fhir-server/R4")
        self.model_registry = ModelRegistry()

        # Mock implementations for monitoring components
        self.metrics_calculator = ClinicalMetrics()
        self.event_reporter = AdverseEventReporter()
        logger.info("ClinicianUIBackend initialized.")

    def get_patient_summary(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieves a summary of a patient's clinical data.
        """
        try:
            # 1. Get raw patient data (FHIR-like structure)
            # The FHIRConnector.get_patient_data is implemented to return a PatientData dict
            patient_data = self.fhir_connector.get_patient_data(patient_id)

            # 2. Get latest predictions from all models
            predictions = self.get_all_model_predictions(patient_id, patient_data)

            # 3. Calculate mock clinical metrics (e.g., readmission risk)
            mock_metrics = self.metrics_calculator.calculate_mock_patient_metrics(
                patient_id
            )

            summary = {
                "patient_id": patient_id,
                "demographics": patient_data.get("demographics", {}),
                "latest_events": patient_data.get("clinical_events", [])[
                    -3:
                ],  # Last 3 events
                "predictions": predictions,
                "clinical_metrics": mock_metrics,
                "last_updated": datetime.now().isoformat(),
            }
            return summary

        except Exception as e:
            logger.error(f"Error getting patient summary for {patient_id}: {e}")
            return {"error": str(e)}

    def get_all_model_predictions(
        self, patient_id: str, patient_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Runs all registered models for a given patient.
        """
        all_predictions = {}
        model_metadata = self.model_registry.list_models()

        for model_name in model_metadata.keys():
            try:
                # Get the latest version of the model
                model = self.model_registry.get_model(model_name, version="latest")

                # Prepare data for prediction (mock conversion for SurvivalAnalysisModel)
                if model_name == "survival_analysis":
                    # Mock a single-row DataFrame for the survival model
                    # This is a simplification; a real system would need proper feature engineering
                    data_for_survival = pd.DataFrame(
                        {
                            "age": [patient_data["demographics"].get("age", 50)],
                            "gender_male": [
                                (
                                    1
                                    if patient_data["demographics"].get("gender")
                                    == "male"
                                    else 0
                                )
                            ],
                            "event_occurred": [
                                0
                            ],  # Required by the model's internal logic
                            "time_to_event": [
                                365
                            ],  # Required by the model's internal logic
                        }
                    )
                    prediction = model.predict(data_for_survival)
                    explanation = model.explain(data_for_survival)
                else:
                    # DeepFM and Transformer expect the patient_data dict
                    prediction = model.predict(patient_data)
                    explanation = model.explain(patient_data)

                all_predictions[model_name] = {
                    "version": model.version,
                    "prediction": prediction,
                    "explanation": explanation,
                }
            except Exception as e:
                logger.warning(
                    f"Could not run model {model_name} for patient {patient_id}: {e}"
                )
                all_predictions[model_name] = {"error": f"Prediction failed: {str(e)}"}

        return all_predictions

    def report_adverse_event(
        self, patient_id: str, event_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handles the reporting of an adverse event via the UI.
        """
        event_id = self.event_reporter.report_event(patient_id, event_details)
        return {
            "status": "success",
            "event_id": event_id,
            "message": "Adverse event reported successfully.",
        }

    # --- New Feature: Cohort Analysis ---
    def get_cohort_analysis(self, cohort_name: str) -> Dict[str, Any]:
        """
        Provides a summary of a specific patient cohort for the clinician.

        This is a new feature to enhance the UI's analytical capabilities.
        """
        logger.info(f"Generating cohort analysis for: {cohort_name}")

        # Mock data for a cohort
        if cohort_name == "Hypertension_HighRisk":
            data = {
                "size": 450,
                "average_risk_score": 0.78,
                "top_risk_factors": ["Age > 65", "High Creatinine", "Diabetes"],
                "model_performance": {
                    "DeepFM": {"AUC": 0.85, "C-Index": "N/A"},
                    "SurvivalAnalysis": {"AUC": "N/A", "C-Index": 0.72},
                },
                "concept_drift_status": "Stable",
            }
        else:
            data = {"size": 0, "message": f"Cohort '{cohort_name}' not found."}

        return data
