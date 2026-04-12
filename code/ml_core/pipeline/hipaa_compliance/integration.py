"""
Integration module for HIPAA compliance in the clinical data pipeline.

This module provides utilities for integrating HIPAA-compliant
de-identification into the existing clinical data pipeline.
"""

import logging
from typing import Any, Dict, List, Optional

from ml_core.pipeline.hipaa_compliance.deidentifier import (
    DeidentificationConfig,
    PHIDeidentifier,
)
from ml_core.pipeline.hipaa_compliance.phi_detector import PHIDetector

logger = logging.getLogger(__name__)

# Lazy import apache_beam so the module can be loaded without it installed
try:
    import apache_beam as beam

    _BEAM_AVAILABLE = True
except ImportError:
    _BEAM_AVAILABLE = False
    beam = None  # type: ignore


def _beam_dofn_base():
    """Return beam.DoFn if available, else a no-op base class."""
    if _BEAM_AVAILABLE:
        return beam.DoFn

    class _Stub:
        pass

    return _Stub


def _beam_ptransform_base():
    if _BEAM_AVAILABLE:
        return beam.PTransform

    class _Stub:
        pass

    return _Stub


class DeidentifyFHIRDoFn(_beam_dofn_base()):
    """Apache Beam DoFn for de-identifying FHIR bundles."""

    def __init__(self, config: Optional[DeidentificationConfig] = None) -> None:
        if _BEAM_AVAILABLE:
            super().__init__()
        self.config = config if config else DeidentificationConfig()

    def setup(self) -> None:
        self.deidentifier = PHIDeidentifier(self.config)

    def process(self, element: Any):
        if not hasattr(self, "deidentifier"):
            self.setup()
        try:
            deidentified = self.deidentifier.deidentify_fhir_bundle(element)
            yield deidentified
        except Exception as e:
            logger.error(f"Error de-identifying FHIR bundle: {e}")
            yield element


class DeidentifyDataFrameDoFn(_beam_dofn_base()):
    """Apache Beam DoFn for de-identifying pandas DataFrames."""

    def __init__(
        self,
        config: Optional[DeidentificationConfig] = None,
        patient_id_col: Optional[str] = None,
        phi_cols: Optional[List[str]] = None,
    ) -> None:
        if _BEAM_AVAILABLE:
            super().__init__()
        self.config = config if config else DeidentificationConfig()
        self.patient_id_col = patient_id_col
        self.phi_cols = phi_cols

    def setup(self) -> None:
        self.deidentifier = PHIDeidentifier(self.config)

    def process(self, element: Any):
        if not hasattr(self, "deidentifier"):
            self.setup()
        try:
            deidentified = self.deidentifier.deidentify_dataframe(
                element, patient_id_col=self.patient_id_col, phi_cols=self.phi_cols
            )
            yield deidentified
        except Exception as e:
            logger.error(f"Error de-identifying DataFrame: {e}")
            yield element


class HIPAACompliantHealthcareETL(_beam_ptransform_base()):
    """HIPAA-compliant version of the HealthcareETL PTransform."""

    def __init__(
        self,
        pipeline_config: Dict[str, Any],
        deidentification_config: Optional[DeidentificationConfig] = None,
        patient_id_col: Optional[str] = None,
        phi_cols: Optional[List[str]] = None,
    ) -> None:
        if _BEAM_AVAILABLE:
            super().__init__()
        self.pipeline_config = pipeline_config
        self.deidentification_config = (
            deidentification_config
            if deidentification_config
            else DeidentificationConfig()
        )
        self.patient_id_col = patient_id_col
        self.phi_cols = phi_cols

    def expand(self, pcoll: Any) -> Any:
        if not _BEAM_AVAILABLE:
            raise RuntimeError("apache_beam is not installed.")
        return (
            pcoll
            | "DeidentifyFHIR"
            >> beam.ParDo(DeidentifyFHIRDoFn(self.deidentification_config))
            | "DeidentifyFeatures"
            >> beam.ParDo(
                DeidentifyDataFrameDoFn(
                    self.deidentification_config, self.patient_id_col, self.phi_cols
                )
            )
        )


def create_hipaa_compliant_etl(
    pipeline_config: Optional[Dict[str, Any]] = None,
    deidentification_config: Optional[DeidentificationConfig] = None,
    patient_id_col: Optional[str] = None,
    phi_cols: Optional[List[str]] = None,
) -> "HIPAACompliantHealthcareETL":
    cfg = pipeline_config or {
        "coding_systems": ["ICD10", "SNOMED-CT", "LOINC"],
        "feature_store": "nexora_feature_store",
        "entity_map": {"patient_id": "patient"},
    }
    return HIPAACompliantHealthcareETL(
        pipeline_config=cfg,
        deidentification_config=deidentification_config,
        patient_id_col=patient_id_col,
        phi_cols=phi_cols,
    )


def detect_phi_in_pipeline_data(data_sample: Any) -> Dict[str, Any]:
    detector = PHIDetector()
    return detector.generate_phi_report(data_sample)
