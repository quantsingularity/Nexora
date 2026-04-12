"""
FHIR Operations Module for Nexora

This module provides operations on FHIR resources, including transformation
to OMOP CDM format and validation.
"""

import logging
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

try:
    from fhir.resources.bundle import Bundle as _FHIRBundle

    _FHIR_AVAILABLE = True
except ImportError:
    _FHIR_AVAILABLE = False
    _FHIRBundle = None  # type: ignore

# Public alias so callers can do `from utils.fhir_ops import Bundle`
Bundle = _FHIRBundle


class FHIRValidationError(Exception):
    """Exception raised when FHIR validation fails."""


class FHIRDataError(Exception):
    """Exception raised for FHIR data processing errors."""


class FHIRClinicalConnector:
    """
    Connector for FHIR clinical data operations.

    This class provides methods for retrieving and validating FHIR bundles,
    and transforming them to other formats like OMOP CDM.
    """

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
        )
        logger.info(f"Initialized FHIRClinicalConnector with base_url={base_url}")

    def get_patient_bundle(self, patient_id: str) -> Any:
        """
        Retrieve a complete patient bundle using the $everything operation.

        Args:
            patient_id: ID of the patient

        Returns:
            Validated FHIR Bundle (or raw dict if fhir.resources not installed)

        Raises:
            FHIRDataError: If the request fails or data is invalid
        """
        url = f"{self.base_url}/Patient/{patient_id}/$everything"
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            bundle_data = response.json()
        except requests.RequestException as e:
            raise FHIRDataError(f"Failed to fetch patient bundle: {e}") from e

        if _FHIR_AVAILABLE and _FHIRBundle is not None:
            try:
                return _FHIRBundle(**bundle_data)
            except Exception as e:
                raise FHIRValidationError(f"FHIR bundle validation failed: {e}") from e
        return bundle_data

    def validate_bundle(self, bundle: Any) -> bool:
        """
        Validate a FHIR bundle.

        Args:
            bundle: FHIR Bundle to validate

        Returns:
            True if valid, raises FHIRValidationError otherwise
        """
        if (
            _FHIR_AVAILABLE
            and _FHIRBundle is not None
            and isinstance(bundle, _FHIRBundle)
        ):
            return True
        if isinstance(bundle, dict):
            if bundle.get("resourceType") != "Bundle":
                raise FHIRValidationError("Resource type must be 'Bundle'")
            return True
        raise FHIRValidationError("Invalid bundle type")

    def bundle_to_dataframe(self, bundle: Any) -> "Any":
        """Convert a FHIR bundle to a pandas DataFrame."""
        import pandas as pd

        entries = []
        if (
            _FHIR_AVAILABLE
            and _FHIRBundle is not None
            and isinstance(bundle, _FHIRBundle)
        ):
            raw_entries = bundle.entry or []
            for entry in raw_entries:
                resource = entry.resource
                if resource:
                    entries.append(resource.dict())
        elif isinstance(bundle, dict):
            for entry in bundle.get("entry", []):
                resource = entry.get("resource", {})
                if resource:
                    entries.append(resource)
        return pd.DataFrame(entries)

    def fhir_to_omop(self, bundle: Any) -> Dict[str, Any]:
        """
        Transform a FHIR bundle to OMOP CDM format (simplified mapping).

        Args:
            bundle: FHIR Bundle

        Returns:
            Dictionary with OMOP CDM tables as keys and lists of records as values
        """
        omop: Dict[str, Any] = {
            "person": [],
            "condition_occurrence": [],
            "drug_exposure": [],
            "observation": [],
        }

        entries = []
        if (
            _FHIR_AVAILABLE
            and _FHIRBundle is not None
            and isinstance(bundle, _FHIRBundle)
        ):
            entries = [e.resource.dict() for e in (bundle.entry or []) if e.resource]
        elif isinstance(bundle, dict):
            entries = [e.get("resource", {}) for e in bundle.get("entry", [])]

        for resource in entries:
            rtype = resource.get("resourceType")
            if rtype == "Patient":
                omop["person"].append(
                    {
                        "person_id": resource.get("id"),
                        "gender_concept_id": (
                            8507 if resource.get("gender") == "male" else 8532
                        ),
                        "birth_datetime": resource.get("birthDate"),
                    }
                )
            elif rtype == "Condition":
                coding = resource.get("code", {}).get("coding", [{}])[0]
                omop["condition_occurrence"].append(
                    {
                        "condition_source_value": coding.get("code"),
                        "condition_start_date": resource.get("onsetDateTime")
                        or resource.get("recordedDate"),
                    }
                )
            elif rtype == "MedicationRequest":
                med_coding = resource.get("medicationCodeableConcept", {}).get(
                    "coding", [{}]
                )[0]
                omop["drug_exposure"].append(
                    {
                        "drug_source_value": med_coding.get("code"),
                        "drug_source_concept_id": med_coding.get("code"),
                    }
                )
            elif rtype == "Observation":
                obs_coding = resource.get("code", {}).get("coding", [{}])[0]
                omop["observation"].append(
                    {
                        "observation_source_value": obs_coding.get("code"),
                        "value_as_number": resource.get("valueQuantity", {}).get(
                            "value"
                        ),
                        "observation_date": resource.get("effectiveDateTime"),
                    }
                )

        return omop
