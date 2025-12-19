"""
FHIR Operations Module for Nexora

This module provides operations on FHIR resources, including transformation
to OMOP CDM format and validation.
"""

import logging
from typing import Any, Dict, Optional
import requests
from fhir.resources.bundle import Bundle
from pydantic import ValidationError

logger = logging.getLogger(__name__)


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
        """
        Initialize the FHIR clinical connector.

        Args:
            base_url: Base URL of the FHIR server
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {"Content-Type": "application/fhir+json", "Accept": "application/fhir+json"}
        )
        logger.info(f"Initialized FHIRClinicalConnector with base_url={base_url}")

    def get_patient_bundle(self, patient_id: str) -> Bundle:
        """
        Retrieve a complete patient bundle using the $everything operation.

        Args:
            patient_id: ID of the patient

        Returns:
            Validated FHIR Bundle containing all patient data

        Raises:
            FHIRDataError: If the request fails or data is invalid
        """
        try:
            url = f"{self.base_url}/Patient/{patient_id}/$everything"
            response = self.session.get(url)
            response.raise_for_status()

            bundle_data = response.json()
            return self._validate_bundle(bundle_data)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to retrieve patient bundle: {str(e)}")
            raise FHIRDataError(f"Failed to retrieve patient bundle: {str(e)}")

    def _validate_bundle(self, data: Dict[str, Any]) -> Bundle:
        """
        Validate FHIR bundle data.

        Args:
            data: Raw bundle data dictionary

        Returns:
            Validated Bundle object

        Raises:
            FHIRValidationError: If validation fails
        """
        try:
            bundle = Bundle(**data)

            # Validate bundle type
            if bundle.type not in ["searchset", "collection", "document"]:
                raise FHIRValidationError(
                    f"Invalid bundle type: {bundle.type}. "
                    f"Expected 'searchset', 'collection', or 'document'"
                )

            logger.info(f"Validated FHIR bundle with {len(bundle.entry or [])} entries")
            return bundle

        except ValidationError as e:
            logger.error(f"FHIR validation failed: {str(e)}")
            raise FHIRDataError(f"FHIR validation failed: {str(e)}")

    def transform_to_omop(self, bundle: Bundle) -> Dict[str, Any]:
        """
        Convert FHIR bundle to OMOP CDM format.

        Args:
            bundle: FHIR Bundle to transform

        Returns:
            Dictionary containing OMOP CDM formatted data
        """
        logger.info("Transforming FHIR bundle to OMOP CDM format")

        transformer = OmopTransformer()
        omop_data = transformer.transform(bundle)

        logger.info(
            f"Transformed bundle to OMOP: {len(omop_data.get('observations', []))} observations"
        )
        return omop_data


class OmopTransformer:
    """
    Transformer for converting FHIR resources to OMOP CDM format.

    The OMOP Common Data Model is a standardized format for observational
    health data that enables large-scale analytics.
    """

    def _map_patient(self, resource: Any) -> Dict[str, Any]:
        """
        Maps FHIR Patient resource to OMOP Person table fields.

        Args:
            resource: FHIR Patient resource

        Returns:
            Dictionary with OMOP Person fields
        """
        # Extract gender concept ID (OMOP standard)
        gender_map = {
            "male": 8507,
            "female": 8532,
            "other": 0,
            "unknown": 0,
        }
        gender_concept = gender_map.get(
            getattr(resource, "gender", "unknown").lower(), 0
        )

        # Extract year of birth
        birth_date = getattr(resource, "birthDate", None)
        year_of_birth = int(birth_date.split("-")[0]) if birth_date else None

        return {
            "person_id": getattr(resource, "id", None),
            "gender_concept_id": gender_concept,
            "year_of_birth": year_of_birth,
            "race_concept_id": 0,  # Would need extension data
            "ethnicity_concept_id": 0,  # Would need extension data
            "birth_datetime": birth_date,
        }

    def _map_observation(self, resource: Any) -> Optional[Dict[str, Any]]:
        """
        Maps FHIR Observation resource to OMOP Observation table fields.

        Args:
            resource: FHIR Observation resource

        Returns:
            Dictionary with OMOP Observation fields, or None if not an Observation
        """
        # Check resource type
        resource_type = getattr(resource, "resource_type", None)
        if resource_type != "Observation":
            return None

        # Extract patient reference
        subject = getattr(resource, "subject", None)
        person_id = None
        if subject:
            ref = getattr(subject, "reference", "")
            if "/" in ref:
                person_id = ref.split("/")[-1]

        # Extract observation date
        effective_datetime = getattr(resource, "effectiveDateTime", None)
        observation_date = None
        if effective_datetime:
            observation_date = effective_datetime.split("T")[0]

        # Extract value
        value_as_number = None
        value_quantity = getattr(resource, "valueQuantity", None)
        if value_quantity:
            value_as_number = getattr(value_quantity, "value", None)

        return {
            "observation_id": getattr(resource, "id", None),
            "person_id": person_id,
            "observation_concept_id": 0,  # Would need code mapping
            "observation_date": observation_date,
            "observation_datetime": effective_datetime,
            "value_as_number": value_as_number,
            "unit_concept_id": 0,  # Would need unit mapping
        }

    def _map_condition(self, resource: Any) -> Optional[Dict[str, Any]]:
        """
        Maps FHIR Condition resource to OMOP Condition Occurrence fields.

        Args:
            resource: FHIR Condition resource

        Returns:
            Dictionary with OMOP Condition Occurrence fields
        """
        resource_type = getattr(resource, "resource_type", None)
        if resource_type != "Condition":
            return None

        # Extract patient reference
        subject = getattr(resource, "subject", None)
        person_id = None
        if subject:
            ref = getattr(subject, "reference", "")
            if "/" in ref:
                person_id = ref.split("/")[-1]

        # Extract onset date
        onset_datetime = getattr(resource, "onsetDateTime", None)
        condition_start_date = None
        if onset_datetime:
            condition_start_date = onset_datetime.split("T")[0]

        return {
            "condition_occurrence_id": getattr(resource, "id", None),
            "person_id": person_id,
            "condition_concept_id": 0,  # Would need ICD-10 to OMOP mapping
            "condition_start_date": condition_start_date,
            "condition_start_datetime": onset_datetime,
            "condition_type_concept_id": 32020,  # EHR
        }

    def transform(self, bundle: Bundle) -> Dict[str, Any]:
        """
        Implementation of FHIR bundle to OMOP CDM format mapping.

        Args:
            bundle: FHIR Bundle to transform

        Returns:
            Dictionary with OMOP CDM tables
        """
        omop_data = {
            "person": None,
            "observations": [],
            "conditions": [],
        }

        if not bundle.entry:
            logger.warning("Empty bundle, no entries to transform")
            return omop_data

        for entry in bundle.entry:
            resource = entry.resource
            resource_type = getattr(resource, "resource_type", None)

            if resource_type == "Patient":
                # Map patient to person
                omop_data["person"] = self._map_patient(resource)

            elif resource_type == "Observation":
                # Map observation
                obs = self._map_observation(resource)
                if obs:
                    omop_data["observations"].append(obs)

            elif resource_type == "Condition":
                # Map condition
                condition = self._map_condition(resource)
                if condition:
                    omop_data["conditions"].append(condition)

        logger.info(
            f"Transformed FHIR bundle: "
            f"person={omop_data['person'] is not None}, "
            f"observations={len(omop_data['observations'])}, "
            f"conditions={len(omop_data['conditions'])}"
        )

        return omop_data
