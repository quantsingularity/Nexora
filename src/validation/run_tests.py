import unittest
import logging
import os
import sys

# Add the parent directory to the path to allow imports from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Import the necessary components
from src.data_pipeline.clinical_etl import ClinicalETL
from src.model_factory.model_registry import ModelRegistry
from src.utils.fhir_connector import FHIRConnector
from src.compliance.phi_audit_logger import PHIAuditLogger
import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestCoreComponents(unittest.TestCase):
    """
    A comprehensive test suite to validate the core components of Nexora.
    """

    def setUp(self):
        # Mock data for testing
        self.mock_patient_data = {
            "patient_id": "test_patient_123",
            "demographics": {"age": 65, "gender": "male"},
            "clinical_events": [
                {
                    "type": "diagnosis",
                    "date": "2024-11-15",
                    "code": "I10",
                    "description": "Hypertension",
                },
            ],
            "lab_results": [
                {
                    "name": "Creatinine",
                    "value": 1.2,
                    "unit": "mg/dL",
                    "date": "2024-11-01",
                },
            ],
            "medications": [],
        }

        self.mock_survival_data = pd.DataFrame(
            {
                "age": [65],
                "gender_male": [1],
                "event_occurred": [0],
                "time_to_event": [365],
            }
        )

    def test_01_fhir_connector_data_retrieval(self):
        """Test FHIR connector can retrieve and format patient data."""
        logger.info("--- Testing FHIR Connector ---")
        connector = FHIRConnector(base_url="mock")
        patient_data = connector.get_patient_data("patient_mock_123")
        self.assertIn("demographics", patient_data, "FHIR data missing 'demographics'.")
        self.assertIn(
            "clinical_events", patient_data, "FHIR data missing 'clinical_events'."
        )
        logger.info("FHIR Connector data retrieval successful.")

    def test_02_etl_pipeline_run(self):
        """Test the Clinical ETL pipeline can run without crashing."""
        logger.info("--- Testing ETL Pipeline Run ---")
        try:
            etl = ClinicalETL()
            # Use a mock patient ID that the FHIR connector is set up to handle
            patient_ids = ["patient_mock_123", "patient_mock_456"]
            feature_df = etl.run_pipeline(patient_ids)
            self.assertFalse(
                feature_df.empty, "ETL pipeline returned an empty DataFrame."
            )
            self.assertIn(
                "patient_id",
                feature_df.columns,
                "DataFrame missing 'patient_id' column.",
            )
            logger.info(f"ETL successful. DataFrame shape: {feature_df.shape}")
        except Exception as e:
            self.fail(f"ETL pipeline failed with exception: {e}")

    def test_03_model_registry_and_prediction(self):
        """Test model registry loads and models can make predictions."""
        logger.info("--- Testing Model Registry and Prediction ---")
        try:
            registry = ModelRegistry()
            models = registry.list_models()
            self.assertTrue(models, "Model registry is empty.")

            # Test DeepFM and Transformer (expect dict input)
            for model_name in ["deep_fm", "transformer_model"]:
                model = registry.get_model(model_name)
                prediction = model.predict(self.mock_patient_data)
                self.assertIn(
                    "risk_score",
                    prediction,
                    f"Model {model_name} prediction missing 'risk_score'.",
                )
                logger.info(
                    f"Model {model_name} prediction successful. Risk: {prediction['risk_score']:.2f}"
                )

            # Test Survival Analysis (expects DataFrame input)
            model_name = "survival_analysis"
            model = registry.get_model(model_name)
            # Mock a minimal training step to initialize the CPH model
            model.train(self.mock_survival_data)
            prediction = model.predict(
                self.mock_survival_data.drop(
                    columns=["event_occurred", "time_to_event"]
                )
            )
            self.assertIn(
                "median_survival_time",
                prediction,
                f"Model {model_name} prediction missing 'median_survival_time'.",
            )
            logger.info(
                f"Model {model_name} prediction successful. Median Survival: {prediction['median_survival_time']:.2f}"
            )

        except Exception as e:
            self.fail(f"Model registry or prediction failed with exception: {e}")

    def test_04_phi_audit_logger(self):
        """Test PHI Audit Logger functionality."""
        logger.info("--- Testing PHI Audit Logger ---")
        try:
            logger_instance = PHIAuditLogger(db_path="test_audit.db")
            logger_instance.log_prediction_request(
                patient_id="test_patient_456", model_used="deep_fm v1.0.0"
            )
            report = logger_instance.generate_report(
                start_date="2020-01-01", end_date=datetime.now().isoformat()
            )
            self.assertFalse(report.empty, "Audit report is empty.")
            self.assertIn(
                "test_patient_456",
                report["patient"].values,
                "Logged patient ID not found in report.",
            )
            logger.info("PHI Audit Logger test successful.")
        except Exception as e:
            self.fail(f"PHI Audit Logger failed with exception: {e}")


def run_all_tests():
    """Runs all tests in the suite."""
    # Create a test suite
    suite = unittest.TestSuite()

    # Add tests from TestCoreComponents
    suite.addTest(unittest.makeSuite(TestCoreComponents))

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    if result.wasSuccessful():
        logger.info("\n*** ALL CORE COMPONENT TESTS PASSED SUCCESSFULLY ***")
    else:
        logger.error("\n*** SOME CORE COMPONENT TESTS FAILED ***")


if __name__ == "__main__":
    run_all_tests()
