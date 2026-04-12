"""
Synthetic Clinical Data Generator Module for Nexora

This module provides functionality for generating synthetic clinical data
that mimics real patient data while preserving privacy. Useful for development,
testing, and demonstration purposes.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from faker import Faker as _Faker

    _FAKER_AVAILABLE = True
except ImportError:
    _FAKER_AVAILABLE = False
    _Faker = None  # type: ignore


class _SimpleFaker:
    """Minimal faker fallback using random data when Faker is not installed."""

    _FIRST_NAMES = [
        "James",
        "Mary",
        "John",
        "Patricia",
        "Robert",
        "Jennifer",
        "Michael",
        "Linda",
        "William",
        "Barbara",
        "David",
        "Susan",
    ]
    _LAST_NAMES = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Wilson",
        "Anderson",
        "Taylor",
        "Thomas",
    ]
    _CITIES = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
        "Dallas",
        "San Jose",
    ]
    _STATES = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA", "TX", "CA"]

    def __init__(self, rng: np.random.Generator) -> None:
        self._rng = rng

    def name(self) -> str:
        first = self._FIRST_NAMES[int(self._rng.integers(0, len(self._FIRST_NAMES)))]
        last = self._LAST_NAMES[int(self._rng.integers(0, len(self._LAST_NAMES)))]
        return f"{first} {last}"

    def city(self) -> str:
        idx = int(self._rng.integers(0, len(self._CITIES)))
        return self._CITIES[idx]

    def state(self) -> str:
        idx = int(self._rng.integers(0, len(self._STATES)))
        return self._STATES[idx]

    def zipcode(self) -> str:
        return str(int(self._rng.integers(10000, 99999))).zfill(5)

    def phone_number(self) -> str:
        a = int(self._rng.integers(200, 999))
        b = int(self._rng.integers(100, 999))
        c = int(self._rng.integers(1000, 9999))
        return f"({a}) {b}-{c}"

    def email(self) -> str:
        domains = ["example.com", "test.org", "health.net"]
        d = domains[int(self._rng.integers(0, len(domains)))]
        u = int(self._rng.integers(1000, 9999))
        return f"patient{u}@{d}"


class ClinicalDataGenerator:
    """
    Generator for synthetic clinical data.

    Creates realistic synthetic patient records including demographics,
    diagnoses, medications, lab results, and other clinical data.
    """

    COMMON_ICD10_CODES = [
        "I10",  # Essential hypertension
        "E11",  # Type 2 diabetes
        "J44",  # COPD
        "I50",  # Heart failure
        "N18",  # Chronic kidney disease
        "J45",  # Asthma
        "I25",  # Chronic ischemic heart disease
        "E66",  # Obesity
        "F32",  # Major depressive disorder
        "K21",  # Gastro-esophageal reflux disease
    ]

    COMMON_MEDICATIONS = [
        "Lisinopril",
        "Metformin",
        "Atorvastatin",
        "Amlodipine",
        "Metoprolol",
        "Omeprazole",
        "Albuterol",
        "Sertraline",
        "Furosemide",
        "Warfarin",
    ]

    LAB_TESTS = {
        "Creatinine": (0.5, 3.0, "mg/dL"),
        "HbA1c": (4.5, 12.0, "%"),
        "Hemoglobin": (8.0, 18.0, "g/dL"),
        "Sodium": (130, 150, "mEq/L"),
        "Potassium": (3.0, 6.0, "mEq/L"),
        "Glucose": (60, 400, "mg/dL"),
        "WBC": (2.0, 15.0, "10^3/uL"),
    }

    def __init__(self, seed: int = 42) -> None:
        self.rng = np.random.default_rng(seed)
        if _FAKER_AVAILABLE and _Faker is not None:
            _Faker.seed(seed)
            self._faker = _Faker()
        else:
            self._faker = _SimpleFaker(self.rng)
            logger.warning("faker not installed; using built-in data generator.")
        logger.info(f"Initialized ClinicalDataGenerator with seed={seed}")

    def _random_date(self, start_year: int = 2020, end_year: int = 2024) -> str:
        days = int(self.rng.integers(0, 365 * (end_year - start_year)))
        d = datetime(start_year, 1, 1) + timedelta(days=days)
        return d.strftime("%Y-%m-%d")

    def _random_birthdate(self, age: int) -> str:
        year = datetime.now().year - age
        day_of_year = int(self.rng.integers(1, 365))
        d = datetime(year, 1, 1) + timedelta(days=day_of_year)
        return d.strftime("%Y-%m-%d")

    def generate_patient_records(
        self, n: int = 1000, output_path: Optional[str] = None
    ) -> pd.DataFrame:
        logger.info(f"Generating {n} synthetic patient records...")

        patient_ids = [f"PAT{str(i).zfill(6)}" for i in range(1, n + 1)]
        ages = self.rng.integers(18, 95, n)
        genders = self.rng.choice(["M", "F"], n)

        diagnoses = []
        for _ in range(n):
            num_diagnoses = int(self.rng.integers(1, 4))
            codes = self.rng.choice(
                self.COMMON_ICD10_CODES, num_diagnoses, replace=False
            ).tolist()
            diagnoses.append("|".join(codes))

        medications = []
        for _ in range(n):
            num_meds = int(self.rng.integers(1, 6))
            meds = self.rng.choice(
                self.COMMON_MEDICATIONS, num_meds, replace=False
            ).tolist()
            medications.append("|".join(meds))

        admission_dates = [self._random_date(2022, 2024) for _ in range(n)]
        los = self.rng.integers(1, 15, n)
        discharge_dates = [
            (datetime.strptime(ad, "%Y-%m-%d") + timedelta(days=int(l))).strftime(
                "%Y-%m-%d"
            )
            for ad, l in zip(admission_dates, los)
        ]

        readmission_prob = np.where(ages > 65, 0.25, 0.12)
        readmission = self.rng.binomial(1, readmission_prob).tolist()
        mortality_prob = np.where(ages > 75, 0.08, 0.03)
        mortality = self.rng.binomial(1, mortality_prob).tolist()

        creatinine = np.round(self.rng.uniform(0.6, 2.5, n), 2)
        hba1c = np.round(self.rng.uniform(5.0, 10.0, n), 1)

        names = [self._faker.name() for _ in range(n)]
        birth_dates = [self._random_birthdate(int(a)) for a in ages]

        df = pd.DataFrame(
            {
                "patient_id": patient_ids,
                "name": names,
                "age": ages,
                "gender": genders,
                "birth_date": birth_dates,
                "diagnoses": diagnoses,
                "medications": medications,
                "admission_date": admission_dates,
                "discharge_date": discharge_dates,
                "length_of_stay": los,
                "readmission_30d": readmission,
                "in_hospital_mortality": mortality,
                "creatinine": creatinine,
                "hba1c": hba1c,
            }
        )

        if output_path:
            os.makedirs(
                os.path.dirname(output_path) if os.path.dirname(output_path) else ".",
                exist_ok=True,
            )
            df.to_csv(output_path, index=False)
            logger.info(f"Saved {n} records to {output_path}")

        logger.info(f"Generated {n} synthetic patient records.")
        return df

    def generate_fhir_bundle(self, patient_id: str) -> dict:
        """Generate a minimal synthetic FHIR patient bundle."""
        age = int(self.rng.integers(25, 85))
        gender = self.rng.choice(["male", "female"])
        birth_date = self._random_birthdate(age)
        num_diagnoses = int(self.rng.integers(1, 4))
        codes = self.rng.choice(
            self.COMMON_ICD10_CODES, num_diagnoses, replace=False
        ).tolist()

        entries = [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": patient_id,
                    "gender": gender,
                    "birthDate": birth_date,
                }
            }
        ]

        for code in codes:
            entries.append(
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": f"cond-{patient_id}-{code}",
                        "subject": {"reference": f"Patient/{patient_id}"},
                        "code": {
                            "coding": [
                                {
                                    "system": "http://hl7.org/fhir/sid/icd-10",
                                    "code": code,
                                }
                            ]
                        },
                        "onsetDateTime": self._random_date(),
                    }
                }
            )

        for lab, (lo, hi, unit) in self.LAB_TESTS.items():
            val = round(float(self.rng.uniform(lo, hi)), 2)
            entries.append(
                {
                    "resource": {
                        "resourceType": "Observation",
                        "id": f"obs-{patient_id}-{lab}",
                        "subject": {"reference": f"Patient/{patient_id}"},
                        "code": {"coding": [{"code": lab}], "text": lab},
                        "valueQuantity": {"value": val, "unit": unit},
                        "effectiveDateTime": self._random_date(),
                        "category": [{"coding": [{"code": "laboratory"}]}],
                    }
                }
            )

        return {"resourceType": "Bundle", "type": "collection", "entry": entries}
