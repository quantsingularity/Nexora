"""
Synthetic Clinical Data Generator Module for Nexora

This module provides functionality for generating synthetic clinical data
that mimics real patient data while preserving privacy. Useful for development,
testing, and demonstration purposes.
"""

import os
import logging
from typing import Optional
import numpy as np
import pandas as pd
from faker import Faker
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ClinicalDataGenerator:
    """
    Generator for synthetic clinical data.

    This class creates realistic synthetic patient records including demographics,
    diagnoses, medications, lab results, and other clinical data.
    """

    # Common ICD-10 codes for testing
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

    def __init__(self, seed: int = 42) -> None:
        """
        Initialize the clinical data generator.

        Args:
            seed: Random seed for reproducibility
        """
        self.faker = Faker()
        Faker.seed(seed)
        self.rng = np.random.default_rng(seed)
        logger.info(f"Initialized ClinicalDataGenerator with seed={seed}")

    def generate_patient_records(
        self, n: int = 1000, output_path: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generate synthetic patient records.

        Args:
            n: Number of patient records to generate
            output_path: Optional path to save the generated data

        Returns:
            DataFrame containing synthetic patient records
        """
        logger.info(f"Generating {n} synthetic patient records...")

        # Generate patient IDs
        patient_ids = [f"PAT{str(i).zfill(6)}" for i in range(1, n + 1)]

        # Generate demographics
        ages = self.rng.integers(18, 95, n)
        genders = self.rng.choice(["M", "F"], n)

        # Generate diagnoses (1-3 ICD-10 codes per patient)
        diagnoses = []
        for _ in range(n):
            num_diagnoses = self.rng.integers(1, 4)
            patient_diagnoses = self.rng.choice(
                self.COMMON_ICD10_CODES, size=num_diagnoses, replace=False
            )
            diagnoses.append(",".join(patient_diagnoses))

        # Generate clinical metrics
        # Readmission risk: higher for older patients and those with more comorbidities
        base_risk = self.rng.uniform(0.05, 0.30, n)
        age_factor = (ages - 18) / 77 * 0.3  # Up to 30% increase for age
        comorbidity_factor = [
            len(d.split(",")) * 0.1 for d in diagnoses
        ]  # 10% per diagnosis
        readmission_risk = np.clip(base_risk + age_factor + comorbidity_factor, 0, 1)

        # Length of stay: lognormal distribution
        length_of_stay = np.round(self.rng.lognormal(1.2, 0.3, n), 1)

        # Admission dates: random dates in the past 2 years
        admission_dates = [
            self.faker.date_between(start_date="-2y", end_date="today")
            for _ in range(n)
        ]

        # Discharge dates: admission + length of stay
        discharge_dates = [
            admission_dates[i] + timedelta(days=int(length_of_stay[i]))
            for i in range(n)
        ]

        # Create DataFrame
        data = pd.DataFrame(
            {
                "patient_id": patient_ids,
                "age": ages,
                "gender": genders,
                "diagnoses": diagnoses,
                "readmission_risk": np.round(readmission_risk, 3),
                "length_of_stay": length_of_stay,
                "admission_date": admission_dates,
                "discharge_date": discharge_dates,
            }
        )

        logger.info(f"Generated {len(data)} patient records")

        # Save if output path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            if output_path.endswith(".parquet"):
                data.to_parquet(output_path, index=False)
            elif output_path.endswith(".csv"):
                data.to_csv(output_path, index=False)
            else:
                raise ValueError("Output path must end with .parquet or .csv")

            logger.info(f"Saved synthetic data to {output_path}")

        return data

    def generate_lab_results(
        self, patient_ids: list, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Generate synthetic lab results for patients.

        Args:
            patient_ids: List of patient IDs to generate labs for
            start_date: Start date for lab results
            end_date: End date for lab results

        Returns:
            DataFrame containing synthetic lab results
        """
        logger.info(f"Generating lab results for {len(patient_ids)} patients...")

        # Common lab tests
        lab_tests = [
            ("Creatinine", "mg/dL", 0.6, 1.2),
            ("Glucose", "mg/dL", 70, 100),
            ("Hemoglobin", "g/dL", 12, 16),
            ("WBC", "K/uL", 4.5, 11.0),
            ("Platelet", "K/uL", 150, 400),
        ]

        records = []
        for patient_id in patient_ids:
            # Each patient gets 2-5 lab results
            num_labs = self.rng.integers(2, 6)

            for _ in range(num_labs):
                # Random date between start and end
                days_diff = (end_date - start_date).days
                random_days = self.rng.integers(0, days_diff + 1)
                lab_date = start_date + timedelta(days=random_days)

                # Random lab test
                test_name, unit, min_val, max_val = self.rng.choice(lab_tests)
                value = self.rng.uniform(min_val, max_val)

                records.append(
                    {
                        "patient_id": patient_id,
                        "test_name": test_name,
                        "value": round(value, 2),
                        "unit": unit,
                        "date": lab_date,
                    }
                )

        df = pd.DataFrame(records)
        logger.info(f"Generated {len(df)} lab results")

        return df


if __name__ == "__main__":
    # Example usage
    generator = ClinicalDataGenerator(seed=42)

    # Generate patient records
    patients = generator.generate_patient_records(
        n=1000, output_path="data/synthetic/synthetic_patients.parquet"
    )

    print(f"Generated {len(patients)} patient records")
    print(patients.head())
