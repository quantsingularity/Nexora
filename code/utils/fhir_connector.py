"""
FHIR Connector Module for Nexora

This module provides functionality for connecting to and interacting with FHIR
(Fast Healthcare Interoperability Resources) servers. It includes utilities for
querying, creating, updating, and deleting FHIR resources, as well as handling
authentication and pagination.
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urljoin, urlparse
from typing import Dict, Any, List, Optional
import pandas as pd
import requests

logger = logging.getLogger(__name__)


class FHIRConnector:
    """
    A class for connecting to and interacting with FHIR servers.

    This connector handles authentication, resource operations, and
    conversion between FHIR resources and pandas DataFrames.
    """

    RESOURCE_TYPES = [
        "Patient",
        "Observation",
        "Condition",
        "Procedure",
        "MedicationRequest",
        "MedicationAdministration",
        "AllergyIntolerance",
        "DiagnosticReport",
        "Encounter",
        "Immunization",
        "CarePlan",
        "Goal",
        "Device",
        "Organization",
        "Practitioner",
        "Location",
        "Claim",
        "ExplanationOfBenefit",
    ]

    def __init__(
        self,
        base_url: str,
        auth_type: str = "none",
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token_url: Optional[str] = None,
        scope: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: int = 2,
        page_size: int = 100,
    ) -> None:
        """
        Initialize the FHIR connector.

        Args:
            base_url: Base URL of the FHIR server
            auth_type: Authentication type ('none', 'basic', 'token', 'oauth2')
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            token: Authentication token for token-based auth
            username: Username for basic auth
            password: Password for basic auth
            token_url: URL for obtaining OAuth2 tokens
            scope: OAuth2 scope
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            page_size: Number of resources to request per page
        """
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"
        self.auth_type = auth_type.lower()
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token
        self.username = username
        self.password = password
        self.token_url = token_url
        self.scope = scope
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.page_size = page_size
        self.token_expiry: Optional[datetime] = None
        self.refresh_token: Optional[str] = None
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self._setup_auth()
        logger.info(
            f"Initialized FHIR connector for {base_url} with {auth_type} authentication"
        )

    def _setup_auth(self) -> None:
        """Set up authentication for the FHIR server."""
        if self.auth_type == "none":
            pass
        elif self.auth_type == "basic":
            if not self.username or not self.password:
                raise ValueError(
                    "Username and password are required for basic authentication"
                )
            self.session.auth = (self.username, self.password)
            logger.info("Set up basic authentication")
        elif self.auth_type == "token":
            if not self.token:
                raise ValueError("Token is required for token authentication")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            logger.info("Set up token authentication")
        elif self.auth_type == "oauth2":
            if not self.client_id or not self.client_secret:
                raise ValueError(
                    "Client ID and client secret are required for OAuth2 authentication"
                )
            if not self.token_url:
                self.token_url = self._discover_token_url()
            if not self.token_url:
                raise ValueError("Token URL is required for OAuth2 authentication")
            self._refresh_oauth2_token()
            logger.info("Set up OAuth2 authentication")
        else:
            raise ValueError(f"Unsupported authentication type: {self.auth_type}")

    def _discover_token_url(self) -> Optional[str]:
        """
        Discover the token URL from the FHIR server's metadata.

        Returns:
            Token URL or None if not found
        """
        try:
            response = requests.get(
                urljoin(self.base_url, "metadata"),
                verify=self.verify_ssl,
                timeout=self.timeout,
            )
            response.raise_for_status()
            metadata = response.json()
            if "rest" in metadata:
                for rest in metadata["rest"]:
                    if "security" in rest and "extension" in rest["security"]:
                        for ext in rest["security"]["extension"]:
                            if (
                                ext.get("url")
                                == "http://fhir-registry.smarthealthit.org/StructureDefinition/oauth-uris"
                            ):
                                for uri_ext in ext.get("extension", []):
                                    if uri_ext.get("url") == "token":
                                        return uri_ext.get("valueUri")
            return None
        except Exception as e:
            logger.warning(f"Failed to discover token URL: {str(e)}")
            return None

    def _refresh_oauth2_token(self) -> None:
        """Refresh the OAuth2 token."""
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
            if self.scope:
                data["scope"] = self.scope
            response = requests.post(
                self.token_url, data=data, verify=self.verify_ssl, timeout=self.timeout
            )
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get("access_token")
            if not self.token:
                raise ValueError("No access token in response")
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)
            self.refresh_token = token_data.get("refresh_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            logger.info(f"Refreshed OAuth2 token, expires in {expires_in} seconds")
        except Exception as e:
            logger.error(f"Failed to refresh OAuth2 token: {str(e)}")
            raise

    def _check_token_expiry(self) -> None:
        """Check if the OAuth2 token needs to be refreshed."""
        if self.auth_type != "oauth2":
            return
        if not self.token_expiry or datetime.now() >= self.token_expiry:
            logger.info("OAuth2 token expired, refreshing")
            self._refresh_oauth2_token()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
    ) -> requests.Response:
        """
        Make a request to the FHIR server with retry logic.

        Args:
            method: HTTP method ('GET', 'POST', 'PUT', 'DELETE')
            endpoint: API endpoint (relative to base URL)
            params: Query parameters
            data: Request data
            headers: Additional headers

        Returns:
            Response object
        """
        self._check_token_expiry()
        url = urljoin(self.base_url, endpoint)
        request_headers = {"Accept": "application/fhir+json"}
        if data:
            request_headers["Content-Type"] = "application/fhir+json"
        if headers:
            request_headers.update(headers)
        retries = 0
        while retries <= self.max_retries:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                if response.status_code == 429:
                    retry_after = int(
                        response.headers.get("Retry-After", self.retry_delay)
                    )
                    logger.warning(
                        f"Rate limited, retrying after {retry_after} seconds"
                    )
                    time.sleep(retry_after)
                    retries += 1
                    continue
                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, retrying")
                    time.sleep(self.retry_delay)
                    retries += 1
                    continue
                if response.status_code == 401 and self.auth_type == "oauth2":
                    logger.warning("Authentication error, refreshing token")
                    self._refresh_oauth2_token()
                    retries += 1
                    continue
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if retries < self.max_retries:
                    logger.warning(
                        f"Request failed: {str(e)}, retrying ({retries + 1}/{self.max_retries})"
                    )
                    time.sleep(self.retry_delay)
                    retries += 1
                else:
                    logger.error(
                        f"Request failed after {self.max_retries} retries: {str(e)}"
                    )
                    raise

    def get_capability_statement(self) -> Dict:
        """
        Get the FHIR server's capability statement (metadata).

        Returns:
            Capability statement as a dictionary
        """
        response = self._make_request("GET", "metadata")
        return response.json()

    def search(
        self,
        resource_type: str,
        params: Optional[Dict] = None,
        max_count: Optional[int] = None,
    ) -> List[Dict]:
        """
        Search for FHIR resources.

        Args:
            resource_type: Type of resource to search for
            params: Search parameters
            max_count: Maximum number of resources to return

        Returns:
            List of resources
        """
        if resource_type not in self.RESOURCE_TYPES:
            logger.warning(f"Unknown resource type: {resource_type}")
        search_params = params.copy() if params else {}
        search_params["_count"] = (
            min(self.page_size, max_count) if max_count else self.page_size
        )
        all_resources = []
        response = self._make_request("GET", resource_type, params=search_params)
        bundle = response.json()
        if "entry" in bundle:
            resources = [entry["resource"] for entry in bundle["entry"]]
            all_resources.extend(resources)
        while "link" in bundle:
            next_link = None
            for link in bundle["link"]:
                if link.get("relation") == "next":
                    next_link = link.get("url")
                    break
            if not next_link or (max_count and len(all_resources) >= max_count):
                break
            parsed_url = urlparse(next_link)
            next_params = parse_qs(parsed_url.query)
            next_params = {k: v[0] for k, v in next_params.items()}
            response = self._make_request("GET", resource_type, params=next_params)
            bundle = response.json()
            if "entry" in bundle:
                resources = [entry["resource"] for entry in bundle["entry"]]
                all_resources.extend(resources)
        if max_count and len(all_resources) > max_count:
            all_resources = all_resources[:max_count]
        logger.info(f"Retrieved {len(all_resources)} {resource_type} resources")
        return all_resources

    def get(self, resource_type: str, resource_id: str) -> Dict:
        """
        Get a specific FHIR resource by ID.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource

        Returns:
            Resource as a dictionary
        """
        if resource_type not in self.RESOURCE_TYPES:
            logger.warning(f"Unknown resource type: {resource_type}")
        endpoint = f"{resource_type}/{resource_id}"
        response = self._make_request("GET", endpoint)
        return response.json()

    def create(self, resource: Dict) -> Dict:
        """
        Create a new FHIR resource.

        Args:
            resource: Resource data

        Returns:
            Created resource as a dictionary
        """
        resource_type = resource.get("resourceType")
        if not resource_type:
            raise ValueError("Resource must have a resourceType")
        if resource_type not in self.RESOURCE_TYPES:
            logger.warning(f"Unknown resource type: {resource_type}")
        response = self._make_request("POST", resource_type, data=resource)
        return response.json()

    def update(self, resource: Dict) -> Dict:
        """
        Update an existing FHIR resource.

        Args:
            resource: Resource data

        Returns:
            Updated resource as a dictionary
        """
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not resource_type or not resource_id:
            raise ValueError("Resource must have resourceType and id")
        if resource_type not in self.RESOURCE_TYPES:
            logger.warning(f"Unknown resource type: {resource_type}")
        endpoint = f"{resource_type}/{resource_id}"
        response = self._make_request("PUT", endpoint, data=resource)
        return response.json()

    def delete(self, resource_type: str, resource_id: str) -> None:
        """
        Delete a FHIR resource.

        Args:
            resource_type: Type of resource
            resource_id: ID of the resource
        """
        if resource_type not in self.RESOURCE_TYPES:
            logger.warning(f"Unknown resource type: {resource_type}")
        endpoint = f"{resource_type}/{resource_id}"
        self._make_request("DELETE", endpoint)
        logger.info(f"Deleted {resource_type}/{resource_id}")

    def execute_batch(self, bundle: Dict) -> Dict:
        """
        Execute a batch or transaction bundle.

        Args:
            bundle: Bundle resource

        Returns:
            Response bundle
        """
        if bundle.get("resourceType") != "Bundle":
            raise ValueError("Resource must be a Bundle")
        if bundle.get("type") not in ["batch", "transaction"]:
            raise ValueError("Bundle type must be 'batch' or 'transaction'")
        response = self._make_request("POST", "", data=bundle)
        return response.json()

    def patients_to_dataframe(self, patients: List[Dict]) -> pd.DataFrame:
        """
        Convert a list of Patient resources to a pandas DataFrame.

        Args:
            patients: List of Patient resources

        Returns:
            DataFrame with patient data
        """
        data = []
        for patient in patients:
            patient_id = patient.get("id", "")
            name = patient.get("name", [{}])[0]
            family = name.get("family", "")
            given = " ".join(name.get("given", []))
            gender = patient.get("gender", "")
            birth_date = patient.get("birthDate", "")
            address = patient.get("address", [{}])[0]
            address_line = ", ".join(address.get("line", []))
            city = address.get("city", "")
            state = address.get("state", "")
            postal_code = address.get("postalCode", "")
            country = address.get("country", "")
            telecom = patient.get("telecom", [])
            phone = next(
                (t.get("value", "") for t in telecom if t.get("system") == "phone"), ""
            )
            email = next(
                (t.get("value", "") for t in telecom if t.get("system") == "email"), ""
            )
            identifiers = patient.get("identifier", [])
            mrn = next(
                (
                    i.get("value", "")
                    for i in identifiers
                    if i.get("type", {}).get("coding", [{}])[0].get("code") == "MR"
                ),
                "",
            )
            ssn = next(
                (
                    i.get("value", "")
                    for i in identifiers
                    if i.get("system") == "http://hl7.org/fhir/sid/us-ssn"
                ),
                "",
            )
            row = {
                "patient_id": patient_id,
                "family_name": family,
                "given_name": given,
                "gender": gender,
                "birth_date": birth_date,
                "address_line": address_line,
                "city": city,
                "state": state,
                "postal_code": postal_code,
                "country": country,
                "phone": phone,
                "email": email,
                "mrn": mrn,
                "ssn": ssn,
            }
            data.append(row)
        return pd.DataFrame(data)

    def observations_to_dataframe(self, observations: List[Dict]) -> pd.DataFrame:
        """
        Convert a list of Observation resources to a pandas DataFrame.

        Args:
            observations: List of Observation resources

        Returns:
            DataFrame with observation data
        """
        data = []
        for obs in observations:
            obs_id = obs.get("id", "")
            patient_id = (
                obs.get("subject", {}).get("reference", "").replace("Patient/", "")
            )
            effective_date = obs.get("effectiveDateTime", "")
            if not effective_date:
                effective_period = obs.get("effectivePeriod", {})
                effective_date = effective_period.get("start", "")
            coding = obs.get("code", {}).get("coding", [{}])[0]
            code = coding.get("code", "")
            system = coding.get("system", "")
            display = coding.get("display", "")
            value = None
            value_type = None
            if "valueQuantity" in obs:
                value = obs["valueQuantity"].get("value", "")
                value_type = "quantity"
                unit = obs["valueQuantity"].get("unit", "")
            elif "valueCodeableConcept" in obs:
                value_coding = obs["valueCodeableConcept"].get("coding", [{}])[0]
                value = value_coding.get("code", "")
                value_type = "code"
                unit = value_coding.get("display", "")
            elif "valueString" in obs:
                value = obs["valueString"]
                value_type = "string"
                unit = ""
            elif "valueBoolean" in obs:
                value = obs["valueBoolean"]
                value_type = "boolean"
                unit = ""
            elif "valueInteger" in obs:
                value = obs["valueInteger"]
                value_type = "integer"
                unit = ""
            elif "valueRange" in obs:
                low = obs["valueRange"].get("low", {}).get("value", "")
                high = obs["valueRange"].get("high", {}).get("value", "")
                value = f"{low}-{high}"
                value_type = "range"
                unit = obs["valueRange"].get("low", {}).get("unit", "")
            elif "valueRatio" in obs:
                numerator = obs["valueRatio"].get("numerator", {}).get("value", "")
                denominator = obs["valueRatio"].get("denominator", {}).get("value", "")
                value = f"{numerator}/{denominator}"
                value_type = "ratio"
                unit = obs["valueRatio"].get("numerator", {}).get("unit", "")
            elif "component" in obs:
                for component in obs["component"]:
                    comp_coding = component.get("code", {}).get("coding", [{}])[0]
                    comp_code = comp_coding.get("code", "")
                    comp_display = comp_coding.get("display", "")
                    comp_value = None
                    comp_value_type = None
                    comp_unit = ""
                    if "valueQuantity" in component:
                        comp_value = component["valueQuantity"].get("value", "")
                        comp_value_type = "quantity"
                        comp_unit = component["valueQuantity"].get("unit", "")
                    elif "valueCodeableConcept" in component:
                        comp_value_coding = component["valueCodeableConcept"].get(
                            "coding", [{}]
                        )[0]
                        comp_value = comp_value_coding.get("code", "")
                        comp_value_type = "code"
                        comp_unit = comp_value_coding.get("display", "")
                    if comp_value is not None:
                        comp_row = {
                            "observation_id": obs_id,
                            "patient_id": patient_id,
                            "date": effective_date,
                            "code": f"{code}.{comp_code}",
                            "system": system,
                            "display": f"{display} - {comp_display}",
                            "value": comp_value,
                            "value_type": comp_value_type,
                            "unit": comp_unit,
                            "status": obs.get("status", ""),
                        }
                        data.append(comp_row)
                continue
            row = {
                "observation_id": obs_id,
                "patient_id": patient_id,
                "date": effective_date,
                "code": code,
                "system": system,
                "display": display,
                "value": value,
                "value_type": value_type,
                "unit": unit,
                "status": obs.get("status", ""),
            }
            data.append(row)
        return pd.DataFrame(data)

    def conditions_to_dataframe(self, conditions: List[Dict]) -> pd.DataFrame:
        """
        Convert a list of Condition resources to a pandas DataFrame.

        Args:
            conditions: List of Condition resources

        Returns:
            DataFrame with condition data
        """
        data = []
        for condition in conditions:
            condition_id = condition.get("id", "")
            patient_id = (
                condition.get("subject", {})
                .get("reference", "")
                .replace("Patient/", "")
            )
            onset_date = ""
            if "onsetDateTime" in condition:
                onset_date = condition["onsetDateTime"]
            elif "onsetPeriod" in condition:
                onset_date = condition["onsetPeriod"].get("start", "")
            abatement_date = ""
            if "abatementDateTime" in condition:
                abatement_date = condition["abatementDateTime"]
            elif "abatementPeriod" in condition:
                abatement_date = condition["abatementPeriod"].get("end", "")
            coding = condition.get("code", {}).get("coding", [{}])[0]
            code = coding.get("code", "")
            system = coding.get("system", "")
            display = coding.get("display", "")
            severity_coding = condition.get("severity", {}).get("coding", [{}])[0]
            severity = severity_coding.get("display", "")
            category_coding = condition.get("category", [{}])[0].get("coding", [{}])[0]
            category = category_coding.get("display", "")
            row = {
                "condition_id": condition_id,
                "patient_id": patient_id,
                "onset_date": onset_date,
                "abatement_date": abatement_date,
                "code": code,
                "system": system,
                "display": display,
                "severity": severity,
                "category": category,
                "clinical_status": condition.get("clinicalStatus", {})
                .get("coding", [{}])[0]
                .get("code", ""),
                "verification_status": condition.get("verificationStatus", {})
                .get("coding", [{}])[0]
                .get("code", ""),
            }
            data.append(row)
        return pd.DataFrame(data)

    def procedures_to_dataframe(self, procedures: List[Dict]) -> pd.DataFrame:
        """
        Convert a list of Procedure resources to a pandas DataFrame.

        Args:
            procedures: List of Procedure resources

        Returns:
            DataFrame with procedure data
        """
        data = []
        for procedure in procedures:
            procedure_id = procedure.get("id", "")
            patient_id = (
                procedure.get("subject", {})
                .get("reference", "")
                .replace("Patient/", "")
            )
            performed_date = ""
            if "performedDateTime" in procedure:
                performed_date = procedure["performedDateTime"]
            elif "performedPeriod" in procedure:
                performed_date = procedure["performedPeriod"].get("start", "")
            coding = procedure.get("code", {}).get("coding", [{}])[0]
            code = coding.get("code", "")
            system = coding.get("system", "")
            display = coding.get("display", "")
            category_coding = procedure.get("category", {}).get("coding", [{}])[0]
            category = category_coding.get("display", "")
            performer = (
                procedure.get("performer", [{}])[0].get("actor", {}).get("display", "")
            )
            row = {
                "procedure_id": procedure_id,
                "patient_id": patient_id,
                "performed_date": performed_date,
                "code": code,
                "system": system,
                "display": display,
                "category": category,
                "performer": performer,
                "status": procedure.get("status", ""),
            }
            data.append(row)
        return pd.DataFrame(data)

    def medications_to_dataframe(self, medications: List[Dict]) -> pd.DataFrame:
        """
        Convert a list of MedicationRequest resources to a pandas DataFrame.

        Args:
            medications: List of MedicationRequest resources

        Returns:
            DataFrame with medication data
        """
        data = []
        for med in medications:
            med_id = med.get("id", "")
            patient_id = (
                med.get("subject", {}).get("reference", "").replace("Patient/", "")
            )
            authored_date = med.get("authoredOn", "")
            medication_reference = med.get("medicationReference", {}).get(
                "reference", ""
            )
            medication_display = med.get("medicationReference", {}).get("display", "")
            if not medication_display and "medicationCodeableConcept" in med:
                medication_coding = med["medicationCodeableConcept"].get(
                    "coding", [{}]
                )[0]
                medication_display = medication_coding.get("display", "")
                code = medication_coding.get("code", "")
                system = medication_coding.get("system", "")
            else:
                code = ""
                system = ""
            dosage = med.get("dosageInstruction", [{}])[0]
            text = dosage.get("text", "")
            dose = ""
            if "doseAndRate" in dosage:
                dose_quantity = dosage["doseAndRate"][0].get("doseQuantity", {})
                dose = (
                    f"{dose_quantity.get('value', '')} {dose_quantity.get('unit', '')}"
                )
            frequency = ""
            if "timing" in dosage:
                timing_repeat = dosage["timing"].get("repeat", {})
                frequency = f"{timing_repeat.get('frequency', '')} times per {timing_repeat.get('period', '')} {timing_repeat.get('periodUnit', '')}"
            route = dosage.get("route", {}).get("coding", [{}])[0].get("display", "")
            row = {
                "medication_id": med_id,
                "patient_id": patient_id,
                "authored_date": authored_date,
                "medication_reference": medication_reference,
                "medication_display": medication_display,
                "code": code,
                "system": system,
                "dosage_text": text,
                "dose": dose,
                "frequency": frequency,
                "route": route,
                "status": med.get("status", ""),
            }
            data.append(row)
        return pd.DataFrame(data)

    def encounters_to_dataframe(self, encounters: List[Dict]) -> pd.DataFrame:
        """
        Convert a list of Encounter resources to a pandas DataFrame.

        Args:
            encounters: List of Encounter resources

        Returns:
            DataFrame with encounter data
        """
        data = []
        for encounter in encounters:
            encounter_id = encounter.get("id", "")
            patient_id = (
                encounter.get("subject", {})
                .get("reference", "")
                .replace("Patient/", "")
            )
            period = encounter.get("period", {})
            start_date = period.get("start", "")
            end_date = period.get("end", "")
            type_coding = encounter.get("type", [{}])[0].get("coding", [{}])[0]
            type_code = type_coding.get("code", "")
            type_display = type_coding.get("display", "")
            class_code = encounter.get("class", {}).get("code", "")
            class_display = encounter.get("class", {}).get("display", "")
            location = (
                encounter.get("location", [{}])[0]
                .get("location", {})
                .get("display", "")
            )
            service_provider = encounter.get("serviceProvider", {}).get("display", "")
            row = {
                "encounter_id": encounter_id,
                "patient_id": patient_id,
                "start_date": start_date,
                "end_date": end_date,
                "type_code": type_code,
                "type_display": type_display,
                "class_code": class_code,
                "class_display": class_display,
                "location": location,
                "service_provider": service_provider,
                "status": encounter.get("status", ""),
            }
            data.append(row)
        return pd.DataFrame(data)

    def dataframe_to_patients(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert a pandas DataFrame to a list of Patient resources.

        Args:
            df: DataFrame with patient data

        Returns:
            List of Patient resources
        """
        patients = []
        for _, row in df.iterrows():
            patient = {
                "resourceType": "Patient",
                "id": row.get("patient_id", ""),
                "name": [
                    {
                        "family": row.get("family_name", ""),
                        "given": (
                            row.get("given_name", "").split()
                            if row.get("given_name")
                            else []
                        ),
                    }
                ],
                "gender": row.get("gender", ""),
                "birthDate": row.get("birth_date", ""),
                "address": [
                    {
                        "line": (
                            [row.get("address_line", "")]
                            if row.get("address_line")
                            else []
                        ),
                        "city": row.get("city", ""),
                        "state": row.get("state", ""),
                        "postalCode": row.get("postal_code", ""),
                        "country": row.get("country", ""),
                    }
                ],
                "telecom": [],
                "identifier": [],
            }
            if row.get("phone"):
                patient["telecom"].append(
                    {"system": "phone", "value": row.get("phone", "")}
                )
            if row.get("email"):
                patient["telecom"].append(
                    {"system": "email", "value": row.get("email", "")}
                )
            if row.get("mrn"):
                patient["identifier"].append(
                    {
                        "type": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                    "code": "MR",
                                    "display": "Medical Record Number",
                                }
                            ]
                        },
                        "value": row.get("mrn", ""),
                    }
                )
            if row.get("ssn"):
                patient["identifier"].append(
                    {
                        "system": "http://hl7.org/fhir/sid/us-ssn",
                        "value": row.get("ssn", ""),
                    }
                )
            patients.append(patient)
        return patients

    def dataframe_to_observations(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert a pandas DataFrame to a list of Observation resources.

        Args:
            df: DataFrame with observation data

        Returns:
            List of Observation resources
        """
        observations = []
        for _, row in df.iterrows():
            observation = {
                "resourceType": "Observation",
                "id": row.get("observation_id", ""),
                "status": row.get("status", "final"),
                "code": {
                    "coding": [
                        {
                            "system": row.get("system", ""),
                            "code": row.get("code", ""),
                            "display": row.get("display", ""),
                        }
                    ]
                },
                "subject": {"reference": f"Patient/{row.get('patient_id', '')}"},
                "effectiveDateTime": row.get("date", ""),
            }
            value_type = row.get("value_type", "")
            value = row.get("value", "")
            unit = row.get("unit", "")
            if value_type == "quantity":
                observation["valueQuantity"] = {
                    "value": float(value) if value and (not pd.isna(value)) else None,
                    "unit": unit,
                    "system": "http://unitsofmeasure.org",
                    "code": unit,
                }
            elif value_type == "code":
                observation["valueCodeableConcept"] = {
                    "coding": [{"code": value, "display": unit}]
                }
            elif value_type == "string":
                observation["valueString"] = value
            elif value_type == "boolean":
                observation["valueBoolean"] = (
                    bool(value) if value and (not pd.isna(value)) else None
                )
            elif value_type == "integer":
                observation["valueInteger"] = (
                    int(value) if value and (not pd.isna(value)) else None
                )
            observations.append(observation)
        return observations

    def dataframe_to_conditions(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert a pandas DataFrame to a list of Condition resources.

        Args:
            df: DataFrame with condition data

        Returns:
            List of Condition resources
        """
        conditions = []
        for _, row in df.iterrows():
            condition = {
                "resourceType": "Condition",
                "id": row.get("condition_id", ""),
                "subject": {"reference": f"Patient/{row.get('patient_id', '')}"},
                "code": {
                    "coding": [
                        {
                            "system": row.get("system", ""),
                            "code": row.get("code", ""),
                            "display": row.get("display", ""),
                        }
                    ]
                },
            }
            if row.get("clinical_status"):
                condition["clinicalStatus"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": row.get("clinical_status", ""),
                        }
                    ]
                }
            if row.get("verification_status"):
                condition["verificationStatus"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            "code": row.get("verification_status", ""),
                        }
                    ]
                }
            if row.get("category"):
                condition["category"] = [
                    {"coding": [{"display": row.get("category", "")}]}
                ]
            if row.get("severity"):
                condition["severity"] = {
                    "coding": [{"display": row.get("severity", "")}]
                }
            if row.get("onset_date"):
                condition["onsetDateTime"] = row.get("onset_date", "")
            if row.get("abatement_date"):
                condition["abatementDateTime"] = row.get("abatement_date", "")
            conditions.append(condition)
        return conditions

    def bulk_export(
        self, resource_types: List[str], output_dir: str, format_type: str = "json"
    ) -> Dict[str, str]:
        """
        Export FHIR resources in bulk.

        Args:
            resource_types: List of resource types to export
            output_dir: Directory to save exported files
            format_type: Export format ('json' or 'ndjson')

        Returns:
            Dictionary mapping resource types to file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        result = {}
        for resource_type in resource_types:
            resources = self.search(resource_type)
            if not resources:
                logger.warning(f"No {resource_type} resources found")
                continue
            file_path = os.path.join(output_dir, f"{resource_type}.{format_type}")
            if format_type == "json":
                with open(file_path, "w") as f:
                    json.dump(resources, f, indent=2)
            elif format_type == "ndjson":
                with open(file_path, "w") as f:
                    for resource in resources:
                        f.write(json.dumps(resource) + "\n")
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
            result[resource_type] = file_path
            logger.info(
                f"Exported {len(resources)} {resource_type} resources to {file_path}"
            )
        return result

    def bulk_import(
        self, file_path: str, update_if_exists: bool = False
    ) -> Dict[str, int]:
        """
        Import FHIR resources in bulk.

        Args:
            file_path: Path to file containing resources
            update_if_exists: Whether to update resources if they already exist

        Returns:
            Dictionary with import statistics
        """
        stats = {"total": 0, "created": 0, "updated": 0, "failed": 0}
        if file_path.endswith(".json"):
            with open(file_path, "r") as f:
                resources = json.load(f)
                if not isinstance(resources, list):
                    resources = [resources]
        elif file_path.endswith(".ndjson"):
            resources = []
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        resources.append(json.loads(line))
        else:
            raise ValueError(f"Unsupported file format: {file_path}")
        stats["total"] = len(resources)
        for resource in resources:
            try:
                resource_type = resource.get("resourceType")
                resource_id = resource.get("id")
                if not resource_type:
                    logger.warning("Resource missing resourceType, skipping")
                    stats["failed"] += 1
                    continue
                if resource_id and update_if_exists:
                    try:
                        self.get(resource_type, resource_id)
                        self.update(resource)
                        stats["updated"] += 1
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            self.create(resource)
                            stats["created"] += 1
                        else:
                            raise
                else:
                    self.create(resource)
                    stats["created"] += 1
            except Exception as e:
                logger.error(f"Failed to import resource: {str(e)}")
                stats["failed"] += 1
        logger.info(f"Import statistics: {stats}")
        return stats

    def get_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """
        Retrieves a FHIR Bundle containing all relevant clinical data for a patient
        and formats it into the PatientData structure expected by the prediction API.

        Args:
            patient_id: The unique identifier for the patient.

        Returns:
            A dictionary representing the PatientData structure.
        """
        logger.info(f"Fetching and formatting data for patient ID: {patient_id}")
        try:
            patient_resource = self.get("Patient", patient_id)
        except Exception as e:
            raise ValueError(f"Patient {patient_id} not found or error: {e}")
        search_params = {"patient": patient_id}
        observations = self.search("Observation", params=search_params)
        conditions = self.search("Condition", params=search_params)
        medication_requests = self.search("MedicationRequest", params=search_params)
        demographics = {
            "gender": patient_resource.get("gender"),
            "birthDate": patient_resource.get("birthDate"),
            "maritalStatus": patient_resource.get("maritalStatus", {}).get("text"),
        }
        clinical_events = []
        for condition in conditions:
            clinical_events.append(
                {
                    "type": "diagnosis",
                    "date": condition.get("onsetDateTime")
                    or condition.get("recordedDate"),
                    "code": condition.get("code", {})
                    .get("coding", [{}])[0]
                    .get("code"),
                    "description": condition.get("code", {}).get("text"),
                }
            )
        lab_results = []
        for obs in observations:
            if (
                obs.get("category", [{}])[0].get("coding", [{}])[0].get("code")
                == "laboratory"
            ):
                lab_results.append(
                    {
                        "name": obs.get("code", {}).get("text"),
                        "value": obs.get("valueQuantity", {}).get("value"),
                        "unit": obs.get("valueQuantity", {}).get("unit"),
                        "date": obs.get("effectiveDateTime"),
                    }
                )
        medications = []
        for med_req in medication_requests:
            medications.append(
                {
                    "name": med_req.get("medicationCodeableConcept", {}).get("text"),
                    "dosage": med_req.get("dosage", [{}])[0].get("text"),
                    "status": med_req.get("status"),
                }
            )
        patient_data = {
            "patient_id": patient_id,
            "demographics": demographics,
            "clinical_events": clinical_events,
            "lab_results": lab_results,
            "medications": medications,
        }
        return patient_data
