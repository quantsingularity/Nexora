import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd
from data_pipeline.hipaa_compliance.deidentifier import (
    DeidentificationConfig,
    PHIDeidentifier,
)
from data_pipeline.icd10_encoder import ICD10Encoder
from data_pipeline.temporal_features import TemporalFeatureExtractor
from utils.fhir_connector import FHIRConnector

logger = logging.getLogger(__name__)


class ClinicalETL:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config if config is not None else {}
        self.fhir_connector = FHIRConnector(
            self.config.get("fhir_server_url", "http://mock-fhir-server/R4")
        )
        self.icd10_encoder = ICD10Encoder()
        self.temporal_extractor = TemporalFeatureExtractor()
        deid_config = DeidentificationConfig(**self.config.get("deidentification", {}))
        self.deidentifier = PHIDeidentifier(config=deid_config)
        logger.info("ClinicalETL initialized.")

    def extract(self, patient_ids: List[str]) -> List[Dict[str, Any]]:
        raw_data = []
        for pid in patient_ids:
            try:
                data = self.fhir_connector.get_patient_data(pid)
                raw_data.append(data)
            except Exception as e:
                logger.error(f"Failed to extract data for patient {pid}: {e}")
        return raw_data

    def transform(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        if not raw_data:
            return pd.DataFrame()

        flat_data = []
        for patient_data in raw_data:
            patient_id = patient_data.get("patient_id", "unknown")
            row: Dict[str, Any] = {
                "patient_id": patient_id,
                **patient_data.get("demographics", {}),
            }

            # ICD-10 encoding
            icd_codes = [
                event["code"]
                for event in patient_data.get("clinical_events", [])
                if event.get("type") == "diagnosis" and "code" in event
            ]
            icd_features = self.icd10_encoder.encode_codes_binary(
                icd_codes, level="group"
            )
            row.update(icd_features)

            # Temporal lab features
            lab_df = pd.DataFrame(patient_data.get("lab_results", []))
            if not lab_df.empty and "name" in lab_df.columns:
                creatinine_df = lab_df[lab_df["name"] == "Creatinine"].copy()
                if not creatinine_df.empty:
                    creatinine_df = creatinine_df.rename(
                        columns={"date": "timestamp", "value": "creatinine_value"}
                    )
                    creatinine_df["timestamp"] = pd.to_datetime(
                        creatinine_df["timestamp"]
                    )
                    reference_time = creatinine_df["timestamp"].max()
                    creatinine_extractor = TemporalFeatureExtractor(
                        value_column="creatinine_value",
                        aggregation_functions=["mean", "min", "max", "std", "count"],
                    )
                    temporal_features = creatinine_extractor._extract_window_features(
                        creatinine_df, reference_time=reference_time
                    )
                    row.update(temporal_features)

            flat_data.append(row)

        feature_df = pd.DataFrame(flat_data)
        feature_df.fillna(0, inplace=True)
        logger.info(
            f"Transformation complete: {feature_df.shape[0]} rows, {feature_df.shape[1]} cols."
        )
        return feature_df

    def load(self, feature_df: pd.DataFrame, output_path: Optional[str] = None) -> str:
        logger.info(f"Loading {feature_df.shape[0]} rows to feature store.")
        if output_path is None:
            os.makedirs("data/processed", exist_ok=True)
            output_path = "data/processed/features.parquet"
        else:
            os.makedirs(
                os.path.dirname(output_path) if os.path.dirname(output_path) else ".",
                exist_ok=True,
            )

        try:
            feature_df.to_parquet(output_path, index=False)
        except Exception:
            output_path = output_path.replace(".parquet", ".csv")
            feature_df.to_csv(output_path, index=False)
        logger.info(f"Features saved to {output_path}")
        return output_path

    def run_pipeline(self, patient_ids: List[str]) -> pd.DataFrame:
        raw_data = self.extract(patient_ids)
        feature_df = self.transform(raw_data)
        self.load(feature_df)
        return feature_df
