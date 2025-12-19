import pandas as pd
import os
from typing import Dict, Any, List, Optional
import logging
from utils.fhir_connector import FHIRConnector
from data_pipeline.icd10_encoder import ICD10Encoder
from data_pipeline.temporal_features import TemporalFeatureExtractor
from data_pipeline.hipaa_compliance.deidentifier import (
    PHIDeidentifier,
    DeidentificationConfig,
)

logger = logging.getLogger(__name__)


class ClinicalETL:
    """
    Extract, Transform, Load (ETL) pipeline for clinical data.

    This class orchestrates the data flow from raw FHIR data to a feature-ready
    DataFrame, including compliance checks, encoding, and feature engineering.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> Any:
        self.config = config if config is not None else {}
        self.fhir_connector = FHIRConnector(
            self.config.get("fhir_server_url", "http://mock-fhir-server/R4")
        )
        self.icd10_encoder = ICD10Encoder()
        self.temporal_extractor = TemporalFeatureExtractor()
        deid_config = DeidentificationConfig(**self.config.get("deidentification", {}))
        self.deidentifier = PHIDeidentifier(config=deid_config)
        logger.info(
            "ClinicalETL initialized with FHIR, ICD-10, Temporal, and De-identification components."
        )

    def extract(self, patient_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Extracts raw clinical data (FHIR bundles) for a list of patient IDs.

        Args:
            patient_ids: List of patient IDs to fetch data for.

        Returns:
            A list of FHIR-like patient data dictionaries.
        """
        raw_data = []
        for patient_id in patient_ids:
            try:
                data = self.fhir_connector.get_patient_data(patient_id)
                raw_data.append(data)
            except Exception as e:
                logger.error(f"Failed to extract data for patient {patient_id}: {e}")
        return raw_data

    def transform(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Transforms raw data into a feature-ready DataFrame.

        Args:
            raw_data: List of raw patient data dictionaries.

        Returns:
            A pandas DataFrame of engineered features.
        """
        if not raw_data:
            return pd.DataFrame()
        flat_data = []
        for patient_data in raw_data:
            patient_id = patient_data["patient_id"]
            row = {"patient_id": patient_id, **patient_data["demographics"]}
            icd_codes = [
                event["code"]
                for event in patient_data["clinical_events"]
                if event["type"] == "diagnosis" and "code" in event
            ]
            icd_features = self.icd10_encoder.encode_codes_binary(
                icd_codes, level="group"
            )
            row.update(icd_features)
            lab_df = pd.DataFrame(patient_data.get("lab_results", []))
            if not lab_df.empty:
                creatinine_df = lab_df[lab_df["name"] == "Creatinine"].copy()
                if not creatinine_df.empty:
                    creatinine_df.rename(
                        columns={"date": "timestamp", "value": "creatinine_value"},
                        inplace=True,
                    )
                    creatinine_df["timestamp"] = pd.to_datetime(
                        creatinine_df["timestamp"]
                    )
                    reference_time = creatinine_df["timestamp"].max()
                    temporal_features = (
                        self.temporal_extractor._extract_window_features(
                            creatinine_df, reference_time=reference_time
                        )
                    )
                    row.update(temporal_features)
            flat_data.append(row)
        feature_df = pd.DataFrame(flat_data)
        feature_df.fillna(0, inplace=True)
        logger.info(
            f"Transformation complete. Generated DataFrame with {feature_df.shape[0]} rows and {feature_df.shape[1]} columns."
        )
        return feature_df

    def load(self, feature_df: pd.DataFrame) -> Any:
        """
        Loads the feature DataFrame into a feature store or database.

        Args:
            feature_df: The DataFrame of engineered features.
        """
        logger.info(
            f"Loading {feature_df.shape[0]} rows of features to mock feature store."
        )
        output_path = "data/processed/features.parquet"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        feature_df.to_parquet(output_path, index=False)
        logger.info(f"Features successfully saved to {output_path}")

    def run_pipeline(self, patient_ids: List[str]) -> pd.DataFrame:
        """Runs the full ETL pipeline."""
        raw_data = self.extract(patient_ids)
        feature_df = self.transform(raw_data)
        self.load(feature_df)
        return feature_df
