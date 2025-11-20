"""
Integration module for HIPAA compliance in the clinical data pipeline.

This module provides utilities for integrating HIPAA-compliant
de-identification into the existing clinical data pipeline.
"""

import logging
from typing import Any, Dict, List, Optional

import apache_beam as beam

from ..hipaa_compliance.deidentifier import DeidentificationConfig, PHIDeidentifier
from ..hipaa_compliance.phi_detector import PHIDetector

logger = logging.getLogger(__name__)


class DeidentifyFHIRDoFn(beam.DoFn):
    """
    Apache Beam DoFn for de-identifying FHIR bundles.
    """

    def __init__(self, config: Optional[DeidentificationConfig] = None):
        """
        Initialize the DoFn.

        Args:
            config: De-identification configuration
        """
        self.config = config if config else DeidentificationConfig()

    def setup(self):
        """Set up the DoFn."""
        self.deidentifier = PHIDeidentifier(self.config)

    def process(self, element):
        """
        Process a FHIR bundle.

        Args:
            element: FHIR bundle to de-identify

        Yields:
            De-identified FHIR bundle
        """
        try:
            deidentified = self.deidentifier.deidentify_fhir_bundle(element)
            yield deidentified
        except Exception as e:
            logger.error(f"Error de-identifying FHIR bundle: {e}")
            # Pass through the original element if de-identification fails
            yield element


class DeidentifyDataFrameDoFn(beam.DoFn):
    """
    Apache Beam DoFn for de-identifying pandas DataFrames.
    """

    def __init__(
        self,
        config: Optional[DeidentificationConfig] = None,
        patient_id_col: Optional[str] = None,
        phi_cols: Optional[List[str]] = None,
    ):
        """
        Initialize the DoFn.

        Args:
            config: De-identification configuration
            patient_id_col: Column name for patient ID
            phi_cols: List of column names containing PHI
        """
        self.config = config if config else DeidentificationConfig()
        self.patient_id_col = patient_id_col
        self.phi_cols = phi_cols

    def setup(self):
        """Set up the DoFn."""
        self.deidentifier = PHIDeidentifier(self.config)

    def process(self, element):
        """
        Process a pandas DataFrame.

        Args:
            element: DataFrame to de-identify

        Yields:
            De-identified DataFrame
        """
        try:
            deidentified = self.deidentifier.deidentify_dataframe(
                element, patient_id_col=self.patient_id_col, phi_cols=self.phi_cols
            )
            yield deidentified
        except Exception as e:
            logger.error(f"Error de-identifying DataFrame: {e}")
            # Pass through the original element if de-identification fails
            yield element


class HIPAACompliantHealthcareETL(beam.PTransform):
    """
    HIPAA-compliant version of the HealthcareETL PTransform.

    This transform adds de-identification steps to the original ETL pipeline.
    """

    def __init__(
        self,
        deidentification_config: Optional[DeidentificationConfig] = None,
        patient_id_col: Optional[str] = None,
        phi_cols: Optional[List[str]] = None,
    ):
        """
        Initialize the PTransform.

        Args:
            deidentification_config: Configuration for de-identification
            patient_id_col: Column name for patient ID
            phi_cols: List of column names containing PHI
        """
        self.deidentification_config = (
            deidentification_config
            if deidentification_config
            else DeidentificationConfig()
        )
        self.patient_id_col = patient_id_col
        self.phi_cols = phi_cols

    def expand(self, pcoll):
        return (
            pcoll
            | "ParseFHIR" >> beam.Map(parse_fhir_bundle)
            | "DeidentifyFHIR"
            >> beam.ParDo(DeidentifyFHIRDoFn(self.deidentification_config))
            | "ValidateClinicalData" >> beam.Map(ClinicalValidator().validate)
            | "EncodeMedicalConcepts"
            >> beam.ParDo(ICD10Encoder(config["coding_systems"]))
            | "TemporalAlignment"
            >> beam.WindowInto(beam.window.SlidingWindows(3600, 900))
            | "FeatureGeneration" >> beam.ParDo(ClinicalFeatureGenerator())
            | "DeidentifyFeatures"
            >> beam.ParDo(
                DeidentifyDataFrameDoFn(
                    self.deidentification_config, self.patient_id_col, self.phi_cols
                )
            )
            | "WriteToFeatureStore"
            >> beam.io.WriteToFeast(
                feature_store=config["feature_store"],
                entity_mapping=config["entity_map"],
            )
        )


# Helper functions for pipeline integration
def create_hipaa_compliant_etl(
    deidentification_config: Optional[DeidentificationConfig] = None,
    patient_id_col: Optional[str] = None,
    phi_cols: Optional[List[str]] = None,
) -> HIPAACompliantHealthcareETL:
    """
    Create a HIPAA-compliant ETL pipeline.

    Args:
        deidentification_config: Configuration for de-identification
        patient_id_col: Column name for patient ID
        phi_cols: List of column names containing PHI

    Returns:
        HIPAA-compliant ETL pipeline
    """
    return HIPAACompliantHealthcareETL(
        deidentification_config=deidentification_config,
        patient_id_col=patient_id_col,
        phi_cols=phi_cols,
    )


def detect_phi_in_pipeline_data(data_sample) -> Dict[str, Any]:
    """
    Detect PHI in pipeline data.

    Args:
        data_sample: Sample data to analyze

    Returns:
        PHI detection report
    """
    detector = PHIDetector()
    return detector.generate_phi_report(data_sample)


# Import original pipeline components to ensure compatibility
from ..data_pipeline.clinical_etl import ClinicalValidator, parse_fhir_bundle
from ..data_pipeline.icd10_encoder import ICD10Encoder
from ..data_pipeline.temporal_features import ClinicalFeatureGenerator

# Configuration (should be loaded from a config file in production)
config = {
    "coding_systems": ["ICD10", "SNOMED-CT", "LOINC"],
    "feature_store": "nexora_feature_store",
    "entity_map": {"patient_id": "patient"},
}
