"""
PHI De-identification module for HIPAA compliance.

This module implements the Safe Harbor method for de-identification of PHI
as specified in the HIPAA Privacy Rule (45 CFR 164.514(b)(2)).
"""

import hashlib
import re
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


class DeidentificationConfig:
    """Configuration for PHI de-identification."""

    def __init__(
        self,
        hash_patient_ids: bool = True,
        remove_names: bool = True,
        remove_addresses: bool = True,
        remove_dates_of_birth: bool = True,
        remove_contact_info: bool = True,
        remove_mrns: bool = True,
        remove_ssn: bool = True,
        remove_device_ids: bool = True,
        age_threshold: int = 89,
        salt: Optional[str] = None,
        shift_dates: bool = True,
        date_shift_strategy: str = "patient",
        max_date_shift_days: int = 365,
        k_anonymity_threshold: int = 5,
    ):
        """
        Initialize de-identification configuration.

        Args:
            hash_patient_ids: Whether to hash patient IDs
            remove_names: Whether to remove patient names
            remove_addresses: Whether to remove addresses
            remove_dates_of_birth: Whether to remove dates of birth
            remove_contact_info: Whether to remove contact information
            remove_mrns: Whether to remove medical record numbers
            remove_ssn: Whether to remove social security numbers
            remove_device_ids: Whether to remove device identifiers
            age_threshold: Age threshold for age truncation (HIPAA requires 89+)
            salt: Salt for hashing (if None, a random salt will be generated)
            shift_dates: Whether to shift dates
            date_shift_strategy: Strategy for date shifting ('patient' or 'global')
            max_date_shift_days: Maximum number of days to shift dates
            k_anonymity_threshold: Minimum group size for k-anonymity
        """
        self.hash_patient_ids = hash_patient_ids
        self.remove_names = remove_names
        self.remove_addresses = remove_addresses
        self.remove_dates_of_birth = remove_dates_of_birth
        self.remove_contact_info = remove_contact_info
        self.remove_mrns = remove_mrns
        self.remove_ssn = remove_ssn
        self.remove_device_ids = remove_device_ids
        self.age_threshold = age_threshold
        self.salt = salt if salt else str(uuid.uuid4())
        self.shift_dates = shift_dates
        self.date_shift_strategy = date_shift_strategy
        self.max_date_shift_days = max_date_shift_days
        self.k_anonymity_threshold = k_anonymity_threshold


class PHIDeidentifier:
    """
    De-identifies Protected Health Information (PHI) according to HIPAA Safe Harbor method.

    This class implements the 18 identifiers that must be removed for the Safe Harbor method:
    1. Names
    2. Geographic subdivisions smaller than a state
    3. All elements of dates related to an individual
    4. Telephone numbers
    5. Fax numbers
    6. Email addresses
    7. Social Security numbers
    8. Medical record numbers
    9. Health plan beneficiary numbers
    10. Account numbers
    11. Certificate/license numbers
    12. Vehicle identifiers and serial numbers
    13. Device identifiers and serial numbers
    14. Web URLs
    15. IP addresses
    16. Biometric identifiers
    17. Full-face photographs and comparable images
    18. Any other unique identifying number, characteristic, or code
    """

    def __init__(self, config: DeidentificationConfig = None):
        """
        Initialize the PHI de-identifier.

        Args:
            config: Configuration for de-identification
        """
        self.config = config if config else DeidentificationConfig()
        self.patient_date_shifts = {}
        self.global_date_shift = np.random.randint(
            -self.config.max_date_shift_days, self.config.max_date_shift_days
        )

    def deidentify_dataframe(
        self,
        df: pd.DataFrame,
        patient_id_col: Optional[str] = None,
        phi_cols: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        De-identify a pandas DataFrame containing PHI.

        Args:
            df: DataFrame to de-identify
            patient_id_col: Column name for patient ID
            phi_cols: List of column names containing PHI

        Returns:
            De-identified DataFrame
        """
        # Make a copy to avoid modifying the original
        result = df.copy()

        # If no PHI columns specified, try to detect them
        if not phi_cols:
            phi_cols = self._detect_phi_columns(result)

        # Process patient IDs if specified
        if patient_id_col and patient_id_col in result.columns:
            if self.config.hash_patient_ids:
                result[patient_id_col] = result[patient_id_col].apply(
                    lambda x: self._hash_identifier(str(x))
                )

        # Process each PHI column
        for col in phi_cols:
            if col not in result.columns:
                continue

            # Determine column type and apply appropriate de-identification
            if self._is_date_column(result[col]):
                if self.config.shift_dates:
                    result[col] = self._shift_dates(
                        result[col], result.get(patient_id_col)
                    )
            elif self._is_age_column(col):
                result[col] = self._truncate_ages(result[col])
            elif self._is_address_column(col) and self.config.remove_addresses:
                result[col] = "[REDACTED]"
            elif self._is_name_column(col) and self.config.remove_names:
                result[col] = "[REDACTED]"
            elif self._is_contact_info_column(col) and self.config.remove_contact_info:
                result[col] = "[REDACTED]"
            elif self._is_id_column(col):
                # Handle various ID types
                if (
                    (self._is_mrn_column(col) and self.config.remove_mrns)
                    or (self._is_ssn_column(col) and self.config.remove_ssn)
                    or (
                        self._is_device_id_column(col) and self.config.remove_device_ids
                    )
                ):
                    result[col] = "[REDACTED]"
                else:
                    # Hash other IDs
                    result[col] = result[col].apply(
                        lambda x: self._hash_identifier(str(x)) if pd.notna(x) else x
                    )

        # Apply k-anonymity if configured
        if self.config.k_anonymity_threshold > 1:
            result = self._apply_k_anonymity(result)

        return result

    def deidentify_fhir_bundle(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        """
        De-identify a FHIR bundle containing PHI.

        Args:
            bundle: FHIR bundle to de-identify

        Returns:
            De-identified FHIR bundle
        """
        # Make a deep copy to avoid modifying the original
        import copy

        result = copy.deepcopy(bundle)

        # Process each entry in the bundle
        if "entry" in result and isinstance(result["entry"], list):
            for entry in result["entry"]:
                if "resource" in entry:
                    resource = entry["resource"]
                    resource_type = resource.get("resourceType")

                    # De-identify based on resource type
                    if resource_type == "Patient":
                        self._deidentify_patient_resource(resource)
                    elif resource_type == "Observation":
                        self._deidentify_observation_resource(resource)
                    elif resource_type == "Encounter":
                        self._deidentify_encounter_resource(resource)
                    elif resource_type == "Condition":
                        self._deidentify_condition_resource(resource)
                    elif resource_type == "MedicationRequest":
                        self._deidentify_medication_request_resource(resource)
                    # Add more resource types as needed

        return result

    def _deidentify_patient_resource(self, resource: Dict[str, Any]) -> None:
        """De-identify a FHIR Patient resource."""
        # Handle patient identifier
        if "identifier" in resource and isinstance(resource["identifier"], list):
            for identifier in resource["identifier"]:
                if "value" in identifier and self.config.hash_patient_ids:
                    identifier["value"] = self._hash_identifier(identifier["value"])

        # Remove name if configured
        if "name" in resource and self.config.remove_names:
            resource["name"] = [{"text": "[REDACTED]"}]

        # Remove address if configured
        if "address" in resource and self.config.remove_addresses:
            resource["address"] = [{"text": "[REDACTED]"}]

        # Remove telecom if configured
        if "telecom" in resource and self.config.remove_contact_info:
            resource["telecom"] = []

        # Handle birthDate
        if "birthDate" in resource and self.config.remove_dates_of_birth:
            # Either remove or shift based on configuration
            if self.config.shift_dates:
                patient_id = self._extract_patient_id_from_resource(resource)
                resource["birthDate"] = self._shift_date_string(
                    resource["birthDate"], patient_id
                )
            else:
                # Remove birthDate or replace with year only
                birth_year = (
                    resource["birthDate"][:4]
                    if len(resource["birthDate"]) >= 4
                    else None
                )
                if (
                    birth_year
                    and self._calculate_age(resource["birthDate"])
                    >= self.config.age_threshold
                ):
                    birth_year = str(
                        int(birth_year) - int(birth_year) % 10
                    )  # Truncate to decade
                resource["birthDate"] = birth_year if birth_year else "[REDACTED]"

    def _deidentify_observation_resource(self, resource: Dict[str, Any]) -> None:
        """De-identify a FHIR Observation resource."""
        # Handle dates
        if "effectiveDateTime" in resource and self.config.shift_dates:
            patient_id = self._extract_patient_id_from_resource(resource)
            resource["effectiveDateTime"] = self._shift_date_string(
                resource["effectiveDateTime"], patient_id
            )

        # Handle subject reference (usually patient)
        if "subject" in resource and "reference" in resource["subject"]:
            if self.config.hash_patient_ids:
                ref = resource["subject"]["reference"]
                if ref.startswith("Patient/"):
                    patient_id = ref[8:]  # Remove 'Patient/' prefix
                    resource["subject"][
                        "reference"
                    ] = f"Patient/{self._hash_identifier(patient_id)}"

    def _deidentify_encounter_resource(self, resource: Dict[str, Any]) -> None:
        """De-identify a FHIR Encounter resource."""
        # Handle dates
        for date_field in ["period", "start", "end"]:
            if date_field in resource and self.config.shift_dates:
                patient_id = self._extract_patient_id_from_resource(resource)
                if isinstance(resource[date_field], dict):
                    for sub_field in ["start", "end"]:
                        if sub_field in resource[date_field]:
                            resource[date_field][sub_field] = self._shift_date_string(
                                resource[date_field][sub_field], patient_id
                            )
                else:
                    resource[date_field] = self._shift_date_string(
                        resource[date_field], patient_id
                    )

        # Handle subject reference
        if "subject" in resource and "reference" in resource["subject"]:
            if self.config.hash_patient_ids:
                ref = resource["subject"]["reference"]
                if ref.startswith("Patient/"):
                    patient_id = ref[8:]  # Remove 'Patient/' prefix
                    resource["subject"][
                        "reference"
                    ] = f"Patient/{self._hash_identifier(patient_id)}"

    def _deidentify_condition_resource(self, resource: Dict[str, Any]) -> None:
        """De-identify a FHIR Condition resource."""
        # Handle dates
        for date_field in ["onsetDateTime", "abatementDateTime", "recordedDate"]:
            if date_field in resource and self.config.shift_dates:
                patient_id = self._extract_patient_id_from_resource(resource)
                resource[date_field] = self._shift_date_string(
                    resource[date_field], patient_id
                )

        # Handle subject reference
        if "subject" in resource and "reference" in resource["subject"]:
            if self.config.hash_patient_ids:
                ref = resource["subject"]["reference"]
                if ref.startswith("Patient/"):
                    patient_id = ref[8:]  # Remove 'Patient/' prefix
                    resource["subject"][
                        "reference"
                    ] = f"Patient/{self._hash_identifier(patient_id)}"

    def _deidentify_medication_request_resource(self, resource: Dict[str, Any]) -> None:
        """De-identify a FHIR MedicationRequest resource."""
        # Handle dates
        for date_field in ["authoredOn", "dateWritten"]:
            if date_field in resource and self.config.shift_dates:
                patient_id = self._extract_patient_id_from_resource(resource)
                resource[date_field] = self._shift_date_string(
                    resource[date_field], patient_id
                )

        # Handle subject reference
        if "subject" in resource and "reference" in resource["subject"]:
            if self.config.hash_patient_ids:
                ref = resource["subject"]["reference"]
                if ref.startswith("Patient/"):
                    patient_id = ref[8:]  # Remove 'Patient/' prefix
                    resource["subject"][
                        "reference"
                    ] = f"Patient/{self._hash_identifier(patient_id)}"

    def _extract_patient_id_from_resource(
        self, resource: Dict[str, Any]
    ) -> Optional[str]:
        """Extract patient ID from a FHIR resource."""
        if "subject" in resource and "reference" in resource["subject"]:
            ref = resource["subject"]["reference"]
            if ref.startswith("Patient/"):
                return ref[8:]  # Remove 'Patient/' prefix

        if "patient" in resource and "reference" in resource["patient"]:
            ref = resource["patient"]["reference"]
            if ref.startswith("Patient/"):
                return ref[8:]  # Remove 'Patient/' prefix

        return None

    def _detect_phi_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Detect columns that might contain PHI based on column names.

        Args:
            df: DataFrame to analyze

        Returns:
            List of column names that might contain PHI
        """
        phi_patterns = [
            r"(?i)name",
            r"(?i)address",
            r"(?i)birth",
            r"(?i)dob",
            r"(?i)phone",
            r"(?i)email",
            r"(?i)ssn",
            r"(?i)social",
            r"(?i)mrn",
            r"(?i)medical.?record",
            r"(?i)patient.?id",
            r"(?i)zip",
            r"(?i)postal",
            r"(?i)city",
            r"(?i)state",
            r"(?i)date",
            r"(?i)age",
            r"(?i)identifier",
            r"(?i)license",
            r"(?i)account",
            r"(?i)url",
            r"(?i)ip.?address",
            r"(?i)device",
        ]

        phi_cols = []
        for col in df.columns:
            if any(re.search(pattern, col) for pattern in phi_patterns):
                phi_cols.append(col)

        return phi_cols

    def _is_date_column(self, series: pd.Series) -> bool:
        """Check if a series contains date values."""
        if pd.api.types.is_datetime64_any_dtype(series):
            return True

        # Check if string series might contain dates
        if series.dtype == "object":
            # Sample non-null values
            sample = series.dropna().head(10)
            date_patterns = [
                r"\d{4}-\d{2}-\d{2}",  # ISO format
                r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
                r"\d{2}-\d{2}-\d{4}",  # MM-DD-YYYY
            ]

            for val in sample:
                if isinstance(val, str) and any(
                    re.search(pattern, val) for pattern in date_patterns
                ):
                    return True

        return False

    def _is_age_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains age values."""
        age_patterns = [
            r"(?i)^age$",
            r"(?i)age[_\s]",
            r"(?i)[_\s]age$",
            r"(?i)patient[_\s]age",
            r"(?i)age[_\s]years",
        ]
        return any(re.search(pattern, col_name) for pattern in age_patterns)

    def _is_address_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains address values."""
        address_patterns = [
            r"(?i)address",
            r"(?i)street",
            r"(?i)city",
            r"(?i)state",
            r"(?i)zip",
            r"(?i)postal",
        ]
        return any(re.search(pattern, col_name) for pattern in address_patterns)

    def _is_name_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains name values."""
        name_patterns = [
            r"(?i)name",
            r"(?i)first[_\s]name",
            r"(?i)last[_\s]name",
            r"(?i)middle[_\s]name",
            r"(?i)patient[_\s]name",
        ]
        return any(re.search(pattern, col_name) for pattern in name_patterns)

    def _is_contact_info_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains contact information."""
        contact_patterns = [
            r"(?i)phone",
            r"(?i)email",
            r"(?i)fax",
            r"(?i)contact",
            r"(?i)mobile",
            r"(?i)cell",
        ]
        return any(re.search(pattern, col_name) for pattern in contact_patterns)

    def _is_id_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains ID values."""
        id_patterns = [
            r"(?i)id$",
            r"(?i)identifier",
            r"(?i)number",
            r"(?i)code",
            r"(?i)key",
        ]
        return any(re.search(pattern, col_name) for pattern in id_patterns)

    def _is_mrn_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains medical record numbers."""
        mrn_patterns = [r"(?i)mrn", r"(?i)medical[_\s]record", r"(?i)record[_\s]number"]
        return any(re.search(pattern, col_name) for pattern in mrn_patterns)

    def _is_ssn_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains social security numbers."""
        ssn_patterns = [r"(?i)ssn", r"(?i)social[_\s]security", r"(?i)tax[_\s]id"]
        return any(re.search(pattern, col_name) for pattern in ssn_patterns)

    def _is_device_id_column(self, col_name: str) -> bool:
        """Check if a column name suggests it contains device identifiers."""
        device_patterns = [
            r"(?i)device[_\s]id",
            r"(?i)serial[_\s]number",
            r"(?i)imei",
            r"(?i)uuid",
        ]
        return any(re.search(pattern, col_name) for pattern in device_patterns)

    def _hash_identifier(self, value: str) -> str:
        """
        Hash an identifier using SHA-256 with a salt.

        Args:
            value: Value to hash

        Returns:
            Hashed value
        """
        if not value:
            return value

        # Create a salted hash
        salted = f"{value}{self.config.salt}"
        hashed = hashlib.sha256(salted.encode()).hexdigest()

        return hashed

    def _shift_dates(
        self, date_series: pd.Series, patient_id_series: Optional[pd.Series] = None
    ) -> pd.Series:
        """
        Shift dates in a series by a random amount.

        Args:
            date_series: Series containing dates
            patient_id_series: Series containing patient IDs

        Returns:
            Series with shifted dates
        """
        # Convert to datetime if not already
        dates = pd.to_datetime(date_series, errors="coerce")

        # Apply shifting based on strategy
        if (
            self.config.date_shift_strategy == "patient"
            and patient_id_series is not None
        ):
            # Shift dates consistently for each patient
            result = dates.copy()

            for i, (date, patient_id) in enumerate(zip(dates, patient_id_series)):
                if pd.isna(date) or pd.isna(patient_id):
                    continue

                # Get or generate patient-specific shift
                if patient_id not in self.patient_date_shifts:
                    self.patient_date_shifts[patient_id] = np.random.randint(
                        -self.config.max_date_shift_days,
                        self.config.max_date_shift_days,
                    )

                # Apply shift
                shift_days = self.patient_date_shifts[patient_id]
                result.iloc[i] = date + pd.Timedelta(days=shift_days)

            return result

        else:
            # Use global shift for all dates
            return dates + pd.Timedelta(days=self.global_date_shift)

    def _shift_date_string(
        self, date_str: str, patient_id: Optional[str] = None
    ) -> str:
        """
        Shift a date string by a random amount.

        Args:
            date_str: Date string to shift
            patient_id: Patient ID for patient-specific shifting

        Returns:
            Shifted date string
        """
        try:
            # Parse the date string
            date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))

            # Determine shift amount
            if self.config.date_shift_strategy == "patient" and patient_id:
                # Get or generate patient-specific shift
                if patient_id not in self.patient_date_shifts:
                    self.patient_date_shifts[patient_id] = np.random.randint(
                        -self.config.max_date_shift_days,
                        self.config.max_date_shift_days,
                    )
                shift_days = self.patient_date_shifts[patient_id]
            else:
                # Use global shift
                shift_days = self.global_date_shift

            # Apply shift
            shifted_date = date_obj + pd.Timedelta(days=shift_days)

            # Format back to string
            if "T" in date_str:
                # Include time component
                return shifted_date.isoformat()
            else:
                # Date only
                return shifted_date.date().isoformat()

        except (ValueError, TypeError):
            # Return original if parsing fails
            return date_str

    def _truncate_ages(self, age_series: pd.Series) -> pd.Series:
        """
        Truncate ages above the threshold.

        Args:
            age_series: Series containing ages

        Returns:
            Series with truncated ages
        """
        return age_series.apply(
            lambda x: (
                f"{self.config.age_threshold}+"
                if pd.notna(x) and float(x) >= self.config.age_threshold
                else x
            )
        )

    def _calculate_age(self, birth_date_str: str) -> int:
        """
        Calculate age from birth date string.

        Args:
            birth_date_str: Birth date string

        Returns:
            Age in years
        """
        try:
            birth_date = datetime.fromisoformat(
                birth_date_str.replace("Z", "+00:00")
            ).date()
            today = date.today()
            age = (
                today.year
                - birth_date.year
                - ((today.month, today.day) < (birth_date.month, birth_date.day))
            )
            return age
        except (ValueError, TypeError):
            return 0

    def _apply_k_anonymity(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply k-anonymity to the DataFrame.

        Args:
            df: DataFrame to anonymize

        Returns:
            k-anonymized DataFrame
        """
        # Identify quasi-identifiers (columns that together might identify an individual)
        quasi_identifiers = []
        for col in df.columns:
            if (
                self._is_age_column(col)
                or "gender" in col.lower()
                or "race" in col.lower()
                or "ethnicity" in col.lower()
            ):
                quasi_identifiers.append(col)

        if not quasi_identifiers:
            return df

        # Group by quasi-identifiers and count
        group_counts = df.groupby(quasi_identifiers).size().reset_index(name="count")

        # Identify groups smaller than k
        small_groups = group_counts[
            group_counts["count"] < self.config.k_anonymity_threshold
        ]

        if small_groups.empty:
            return df

        # Create a copy for modification
        result = df.copy()

        # For each small group, generalize or suppress values
        for _, group in small_groups.iterrows():
            mask = pd.Series(True, index=df.index)

            for col in quasi_identifiers:
                mask = mask & (df[col] == group[col])

            # Apply generalization or suppression
            for col in quasi_identifiers:
                if self._is_age_column(col):
                    # Generalize age to age ranges
                    age_val = group[col]
                    if pd.notna(age_val):
                        age_range_start = int(age_val) - (int(age_val) % 5)
                        age_range_end = age_range_start + 4
                        result.loc[mask, col] = f"{age_range_start}-{age_range_end}"
                else:
                    # Suppress other quasi-identifiers
                    result.loc[mask, col] = "[REDACTED]"

        return result
