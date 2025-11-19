import requests
from fhir.resources.bundle import Bundle
from pydantic import ValidationError


class FHIRValidationError(Exception):
    pass


class FHIRDataError(Exception):
    pass


class FHIRClinicalConnector:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/fhir+json"})

    def get_patient_bundle(self, patient_id):
        response = self.session.get(f"{self.base_url}/Patient/{patient_id}/$everything")
        return self._validate_bundle(response.json())

    def _validate_bundle(self, data):
        try:
            bundle = Bundle(**data)
            if bundle.type != "searchset":
                raise FHIRValidationError("Invalid bundle type")
            return bundle
        except ValidationError as e:
            raise FHIRDataError(f"FHIR validation failed: {str(e)}")

    def transform_to_omop(self, bundle):
        """Convert FHIR bundle to OMOP CDM format"""
        return OmopTransformer().transform(bundle)


class OmopTransformer:
    def _map_patient(self, resource):
        """Maps FHIR Patient resource to OMOP Person table fields."""
        # Simple mapping for demonstration. Real-world mapping is complex.
        return {
            "person_id": resource.id,
            "gender_concept_id": 8507 if resource.gender == "male" else 8532,
            "year_of_birth": (
                int(resource.birthDate.split("-")[0]) if resource.birthDate else None
            ),
            "race_concept_id": 0,  # Unknown
            "ethnicity_concept_id": 0,  # Unknown
        }

    def _map_observation(self, resource):
        """Maps FHIR Observation resource to OMOP Observation table fields."""
        # Simple mapping for demonstration. Real-world mapping is complex.
        if resource.resource_type != "Observation":
            return None

        return {
            "observation_id": resource.id,
            "person_id": (
                resource.subject.reference.split("/")[-1] if resource.subject else None
            ),
            "observation_concept_id": 0,  # Placeholder for concept mapping
            "observation_date": (
                resource.effectiveDateTime.split("T")[0]
                if resource.effectiveDateTime
                else None
            ),
            "value_as_number": (
                resource.valueQuantity.value if resource.valueQuantity else None
            ),
            "unit_concept_id": 0,  # Placeholder for unit mapping
        }

    def transform(self, bundle):
        """Implementation of FHIR bundle to OMOP CDM format mapping."""
        return {
            "person": self._map_patient(bundle.entry[0].resource),
            "observations": [
                self._map_observation(entry.resource) for entry in bundle.entry[1:]
            ],
        }
