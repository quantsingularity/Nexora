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
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class FHIRConnector:
    """
    A class for connecting to and interacting with FHIR servers.

    This connector handles authentication, resource operations, and
    conversion between FHIR resources and pandas DataFrames.
    """

    # FHIR resource types
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
    ):
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
        # Ensure base URL ends with a slash
        self.base_url = base_url if base_url.endswith("/") else base_url + "/"

        # Authentication settings
        self.auth_type = auth_type.lower()
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = token
        self.username = username
        self.password = password
        self.token_url = token_url
        self.scope = scope

        # Request settings
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.page_size = page_size

        # Token management
        self.token_expiry = None
        self.refresh_token = None

        # Initialize session
        self.session = requests.Session()
        self.session.verify = verify_ssl

        # Set up authentication
        self._setup_auth()

        logger.info(
            f"Initialized FHIR connector for {base_url} with {auth_type} authentication"
        )

    def _setup_auth(self):
        """Set up authentication for the FHIR server."""
        if self.auth_type == "none":
            # No authentication
            pass

        elif self.auth_type == "basic":
            # Basic authentication
            if not self.username or not self.password:
                raise ValueError(
                    "Username and password are required for basic authentication"
                )

            self.session.auth = (self.username, self.password)
            logger.info("Set up basic authentication")

        elif self.auth_type == "token":
            # Token-based authentication
            if not self.token:
                raise ValueError("Token is required for token authentication")

            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            logger.info("Set up token authentication")

        elif self.auth_type == "oauth2":
            # OAuth2 authentication
            if not self.client_id or not self.client_secret:
                raise ValueError(
                    "Client ID and client secret are required for OAuth2 authentication"
                )

            if not self.token_url:
                # Try to discover token URL from metadata
                self.token_url = self._discover_token_url()

            if not self.token_url:
                raise ValueError("Token URL is required for OAuth2 authentication")

            # Get initial token
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

            # Look for token URL in security extensions
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

    def _refresh_oauth2_token(self):
        """Refresh the OAuth2 token."""
        try:
            # Prepare token request
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }

            if self.scope:
                data["scope"] = self.scope

            # Request token
            response = requests.post(
                self.token_url, data=data, verify=self.verify_ssl, timeout=self.timeout
            )
            response.raise_for_status()

            # Parse response
            token_data = response.json()
            self.token = token_data.get("access_token")

            if not self.token:
                raise ValueError("No access token in response")

            # Set token expiry
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now() + timedelta(
                seconds=expires_in - 60
            )  # Buffer of 60 seconds

            # Store refresh token if provided
            self.refresh_token = token_data.get("refresh_token")

            # Update session headers
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})

            logger.info(f"Refreshed OAuth2 token, expires in {expires_in} seconds")

        except Exception as e:
            logger.error(f"Failed to refresh OAuth2 token: {str(e)}")
            raise

    def _check_token_expiry(self):
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
        # Check token expiry for OAuth2
        self._check_token_expiry()

        # Prepare request
        url = urljoin(self.base_url, endpoint)
        request_headers = {"Accept": "application/fhir+json"}

        if data:
            request_headers["Content-Type"] = "application/fhir+json"

        if headers:
            request_headers.update(headers)

        # Retry logic
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

                # Check for rate limiting
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

                # Check for server errors
                if response.status_code >= 500:
                    logger.warning(f"Server error {response.status_code}, retrying")
                    time.sleep(self.retry_delay)
                    retries += 1
                    continue

                # Check for authentication errors
                if response.status_code == 401 and self.auth_type == "oauth2":
                    logger.warning("Authentication error, refreshing token")
                    self._refresh_oauth2_token()
                    retries += 1
                    continue

                # Raise for other errors
                response.raise_for_status()

                return response

            except requests.exceptions.RequestException as e:
                if retries < self.max_retries:
                    logger.warning(
                        f"Request failed: {str(e)}, retrying ({retries+1}/{self.max_retries})"
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

        # Initialize parameters
        search_params = params.copy() if params else {}
        search_params["_count"] = (
            min(self.page_size, max_count) if max_count else self.page_size
        )

        # Initialize results
        all_resources = []

        # Make initial request
        response = self._make_request("GET", resource_type, params=search_params)
        bundle = response.json()

        # Extract resources
        if "entry" in bundle:
            resources = [entry["resource"] for entry in bundle["entry"]]
            all_resources.extend(resources)

        # Check if we need to paginate
        while "link" in bundle:
            next_link = None
            for link in bundle["link"]:
                if link.get("relation") == "next":
                    next_link = link.get("url")
                    break

            if not next_link or (max_count and len(all_resources) >= max_count):
                break

            # Extract query parameters from next link
            parsed_url = urlparse(next_link)
            next_params = parse_qs(parsed_url.query)

            # Convert list values to single values
            next_params = {k: v[0] for k, v in next_params.items()}

            # Make next request
            response = self._make_request("GET", resource_type, params=next_params)
            bundle = response.json()

            # Extract resources
            if "entry" in bundle:
                resources = [entry["resource"] for entry in bundle["entry"]]
                all_resources.extend(resources)

        # Truncate if max_count is specified
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
            # Extract basic information
            patient_id = patient.get("id", "")

            # Extract name
            name = patient.get("name", [{}])[0]
            family = name.get("family", "")
            given = " ".join(name.get("given", []))

            # Extract other fields
            gender = patient.get("gender", "")
            birth_date = patient.get("birthDate", "")

            # Extract address
            address = patient.get("address", [{}])[0]
            address_line = ", ".join(address.get("line", []))
            city = address.get("city", "")
            state = address.get("state", "")
            postal_code = address.get("postalCode", "")
            country = address.get("country", "")

            # Extract contact information
            telecom = patient.get("telecom", [])
            phone = next(
                (t.get("value", "") for t in telecom if t.get("system") == "phone"), ""
            )
            email = next(
                (t.get("value", "") for t in telecom if t.get("system") == "email"), ""
            )

            # Extract identifiers
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

            # Create row
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
            # Extract basic information
            obs_id = obs.get("id", "")
            patient_id = (
                obs.get("subject", {}).get("reference", "").replace("Patient/", "")
            )

            # Extract date
            effective_date = obs.get("effectiveDateTime", "")
            if not effective_date:
                effective_period = obs.get("effectivePeriod", {})
                effective_date = effective_period.get("start", "")

            # Extract code
            coding = obs.get("code", {}).get("coding", [{}])[0]
            code = coding.get("code", "")
            system = coding.get("system", "")
            display = coding.get("display", "")

            # Extract value
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
                # Handle component-based observations separately
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

                # Skip the main row for component-based observations
                continue

            # Create row
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
            # Extract basic information
            condition_id = condition.get("id", "")
            patient_id = (
                condition.get("subject", {})
                .get("reference", "")
                .replace("Patient/", "")
            )

            # Extract dates
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

            # Extract code
            coding = condition.get("code", {}).get("coding", [{}])[0]
            code = coding.get("code", "")
            system = coding.get("system", "")
            display = coding.get("display", "")

            # Extract severity
            severity_coding = condition.get("severity", {}).get("coding", [{}])[0]
            severity = severity_coding.get("display", "")

            # Extract category
            category_coding = condition.get("category", [{}])[0].get("coding", [{}])[0]
            category = category_coding.get("display", "")

            # Create row
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
            # Extract basic information
            procedure_id = procedure.get("id", "")
            patient_id = (
                procedure.get("subject", {})
                .get("reference", "")
                .replace("Patient/", "")
            )

            # Extract date
            performed_date = ""
            if "performedDateTime" in procedure:
                performed_date = procedure["performedDateTime"]
            elif "performedPeriod" in procedure:
                performed_date = procedure["performedPeriod"].get("start", "")

            # Extract code
            coding = procedure.get("code", {}).get("coding", [{}])[0]
            code = coding.get("code", "")
            system = coding.get("system", "")
            display = coding.get("display", "")

            # Extract category
            category_coding = procedure.get("category", {}).get("coding", [{}])[0]
            category = category_coding.get("display", "")

            # Extract performer
            performer = (
                procedure.get("performer", [{}])[0].get("actor", {}).get("display", "")
            )

            # Create row
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
            # Extract basic information
            med_id = med.get("id", "")
            patient_id = (
                med.get("subject", {}).get("reference", "").replace("Patient/", "")
            )

            # Extract dates
            authored_date = med.get("authoredOn", "")

            # Extract medication
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

            # Extract dosage
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

            # Create row
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
            # Extract basic information
            encounter_id = encounter.get("id", "")
            patient_id = (
                encounter.get("subject", {})
                .get("reference", "")
                .replace("Patient/", "")
            )

            # Extract dates
            period = encounter.get("period", {})
            start_date = period.get("start", "")
            end_date = period.get("end", "")

            # Extract type
            type_coding = encounter.get("type", [{}])[0].get("coding", [{}])[0]
            type_code = type_coding.get("code", "")
            type_display = type_coding.get("display", "")

            # Extract class
            class_code = encounter.get("class", {}).get("code", "")
            class_display = encounter.get("class", {}).get("display", "")

            # Extract location
            location = (
                encounter.get("location", [{}])[0]
                .get("location", {})
                .get("display", "")
            )

            # Extract service provider
            service_provider = encounter.get("serviceProvider", {}).get("display", "")

            # Create row
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
            # Create basic structure
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

            # Add telecom
            if row.get("phone"):
                patient["telecom"].append(
                    {"system": "phone", "value": row.get("phone", "")}
                )

            if row.get("email"):
                patient["telecom"].append(
                    {"system": "email", "value": row.get("email", "")}
                )

            # Add identifiers
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
            # Create basic structure
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

            # Add value based on type
            value_type = row.get("value_type", "")
            value = row.get("value", "")
            unit = row.get("unit", "")

            if value_type == "quantity":
                observation["valueQuantity"] = {
                    "value": float(value) if value and not pd.isna(value) else None,
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
                    bool(value) if value and not pd.isna(value) else None
                )
            elif value_type == "integer":
                observation["valueInteger"] = (
                    int(value) if value and not pd.isna(value) else None
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
            # Create basic structure
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

            # Add clinical status
            if row.get("clinical_status"):
                condition["clinicalStatus"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": row.get("clinical_status", ""),
                        }
                    ]
                }

            # Add verification status
            if row.get("verification_status"):
                condition["verificationStatus"] = {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            "code": row.get("verification_status", ""),
                        }
                    ]
                }

            # Add category
            if row.get("category"):
                condition["category"] = [
                    {"coding": [{"display": row.get("category", "")}]}
                ]

            # Add severity
            if row.get("severity"):
                condition["severity"] = {
                    "coding": [{"display": row.get("severity", "")}]
                }

            # Add onset date
            if row.get("onset_date"):
                condition["onsetDateTime"] = row.get("onset_date", "")

            # Add abatement date
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
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Initialize result
        result = {}

        # Export each resource type
        for resource_type in resource_types:
            # Search for resources
            resources = self.search(resource_type)

            if not resources:
                logger.warning(f"No {resource_type} resources found")
                continue

            # Determine file path
            file_path = os.path.join(output_dir, f"{resource_type}.{format_type}")

            # Write to file
            if format_type == "json":
                # Write as JSON array
                with open(file_path, "w") as f:
                    json.dump(resources, f, indent=2)

            elif format_type == "ndjson":
                # Write as newline-delimited JSON
                with open(file_path, "w") as f:
                    for resource in resources:
                        f.write(json.dumps(resource) + "\n")

            else:
                raise ValueError(f"Unsupported format type: {format_type}")

            # Add to result
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
        # Initialize statistics
        stats = {"total": 0, "created": 0, "updated": 0, "failed": 0}

        # Determine file format
        if file_path.endswith(".json"):
            # Read JSON array
            with open(file_path, "r") as f:
                resources = json.load(f)

                if not isinstance(resources, list):
                    resources = [resources]

        elif file_path.endswith(".ndjson"):
            # Read newline-delimited JSON
            resources = []
            with open(file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        resources.append(json.loads(line))

        else:
            raise ValueError(f"Unsupported file format: {file_path}")

        # Update statistics
        stats["total"] = len(resources)

        # Process resources
        for resource in resources:
            try:
                resource_type = resource.get("resourceType")
                resource_id = resource.get("id")

                if not resource_type:
                    logger.warning("Resource missing resourceType, skipping")
                    stats["failed"] += 1
                    continue

                if resource_id and update_if_exists:
                    # Check if resource exists
                    try:
                        self.get(resource_type, resource_id)

                        # Update existing resource
                        self.update(resource)
                        stats["updated"] += 1

                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            # Resource doesn't exist, create it
                            self.create(resource)
                            stats["created"] += 1
                        else:
                            raise

                else:
                    # Create new resource
                    self.create(resource)
                    stats["created"] += 1

            except Exception as e:
                logger.error(f"Failed to import resource: {str(e)}")
                stats["failed"] += 1

        logger.info(f"Import statistics: {stats}")
        return stats
