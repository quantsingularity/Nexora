"""
Batch Scoring Script for Nexora Clinical Models

Runs a registered Nexora model (from ml_core.models.model_registry) over a
batch of patient records loaded from CSV/Parquet/JSON, and writes the
predictions to an output file. Can score in-process (loading the model
directly) or via the running Nexora REST API's /predict/batch endpoint.

Usage:
    # Score locally using the model registry
    python batch_scoring.py --model-name deep_fm \
        --input-path patients.csv --output-path predictions.csv

    # Score against a running Nexora API instance instead
    python batch_scoring.py --model-name deep_fm \
        --input-path patients.csv --output-path predictions.csv \
        --use-api --api-url http://localhost:8000

Input files must contain a `patient_id` column; every other column is
passed through as a demographics field for the model.
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

# Make the real `ml_core` package (code/ml_core) importable. This mirrors the
# `pythonpath = ..` convention used by code/backend/pytest.ini and
# code/ml_core/pytest.ini: both point at `code/` as the import root, so
# `ml_core` and `backend` are imported as top-level packages from there.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CODE_DIR = os.path.join(_REPO_ROOT, "code")
if _CODE_DIR not in sys.path:
    sys.path.insert(0, _CODE_DIR)

from ml_core.models.model_registry import ModelRegistry  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def _json_encode_nested(record: Dict[str, Any]) -> Dict[str, Any]:
    """JSON-encode any dict-valued fields so a record is safe to write to
    CSV/Parquet, which don't support arbitrarily nested Python objects."""
    return {k: (json.dumps(v) if isinstance(v, dict) else v) for k, v in record.items()}


class BatchScorer:
    """Runs a registered Nexora model over a batch of patient records."""

    def __init__(
        self,
        model_name: str,
        model_version: Optional[str] = None,
        use_api: bool = False,
        api_url: str = "http://localhost:8000",
        api_batch_size: int = 50,
        include_explanations: bool = False,
        registry_path: Optional[str] = None,
    ) -> None:
        self.model_name = model_name
        self.model_version = model_version or "latest"
        self.use_api = use_api
        self.api_url = api_url.rstrip("/")
        self.api_batch_size = max(1, api_batch_size)
        self.include_explanations = include_explanations

        self.model = None
        if not self.use_api:
            registry = (
                ModelRegistry(registry_path) if registry_path else ModelRegistry()
            )
            self.model = registry.get_model(self.model_name, self.model_version)
            logger.info(
                f"Loaded model '{self.model_name}' v{self.model.version} for local scoring."
            )
        else:
            logger.info(f"Scoring via remote API at {self.api_url}")

    # ── Data loading ────────────────────────────────────────────────────

    def load_data(self, input_path: str) -> pd.DataFrame:
        logger.info(f"Loading data from {input_path}")
        if input_path.endswith(".csv"):
            data = pd.read_csv(input_path)
        elif input_path.endswith(".parquet"):
            data = pd.read_parquet(input_path)
        elif input_path.endswith(".json"):
            data = pd.read_json(input_path, orient="records", lines=True)
        else:
            raise ValueError(
                f"Unsupported input format: {input_path} "
                "(expected .csv, .parquet, or .json)"
            )
        if "patient_id" not in data.columns:
            raise ValueError("Input data must include a 'patient_id' column.")
        logger.info(f"Loaded {len(data)} records")
        return data

    @staticmethod
    def _row_to_patient_data(row: "pd.Series") -> Dict[str, Any]:
        """Convert one input row into a PatientData-shaped dict (matching
        backend.app.schemas.clinical.PatientData). Every column other than
        patient_id becomes a demographics field."""
        demographics = {
            col: row[col]
            for col in row.index
            if col != "patient_id" and pd.notna(row[col])
        }
        return {
            "patient_id": str(row["patient_id"]),
            "demographics": demographics,
            "clinical_events": [],
        }

    # ── Scoring ─────────────────────────────────────────────────────────

    def score_batch(self, data: pd.DataFrame) -> pd.DataFrame:
        logger.info(f"Generating predictions for {len(data)} records")
        start_time = time.time()

        results = (
            self._score_via_api(data) if self.use_api else self._score_locally(data)
        )

        elapsed = time.time() - start_time
        logger.info(
            f"Generated predictions for {len(data)} records in {elapsed:.2f} seconds"
        )
        return pd.DataFrame(results).set_index("patient_id")

    def _score_locally(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        results = []
        for _, row in data.iterrows():
            patient_data = self._row_to_patient_data(row)
            pid = patient_data["patient_id"]
            try:
                prediction = self.model.predict(patient_data)
                record = {"patient_id": pid, "status": "ok", **prediction}
                if self.include_explanations:
                    record["explanation"] = self.model.explain(patient_data)
                results.append(_json_encode_nested(record))
            except Exception as e:
                logger.error(f"Prediction failed for patient {pid}: {e}")
                results.append({"patient_id": pid, "status": "error", "detail": str(e)})
        return results

    def _score_via_api(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        endpoint = f"{self.api_url}/predict/batch"
        results: List[Dict[str, Any]] = []
        rows = list(data.iterrows())
        for i in range(0, len(rows), self.api_batch_size):
            chunk = rows[i : i + self.api_batch_size]
            payload = {
                "model_name": self.model_name,
                "model_version": (
                    None if self.model_version == "latest" else self.model_version
                ),
                "patients": [self._row_to_patient_data(row) for _, row in chunk],
            }
            response = requests.post(endpoint, json=payload, timeout=60)
            if response.status_code != 200:
                logger.error(
                    f"API request failed ({response.status_code}): {response.text}"
                )
                raise RuntimeError(
                    f"API request failed with status {response.status_code}"
                )
            results.extend(response.json().get("results", []))
        return results

    # ── Output ──────────────────────────────────────────────────────────

    def save_results(self, predictions: pd.DataFrame, output_path: str) -> None:
        logger.info(f"Saving results to {output_path}")
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        if output_path.endswith(".csv"):
            predictions.to_csv(output_path, index=True)
        elif output_path.endswith(".parquet"):
            predictions.to_parquet(output_path, index=True)
        elif output_path.endswith(".json"):
            predictions.reset_index().to_json(output_path, orient="records", lines=True)
        else:
            raise ValueError(
                f"Unsupported output format: {output_path} "
                "(expected .csv, .parquet, or .json)"
            )
        logger.info("Results saved successfully")

    def run(self, input_path: str, output_path: str) -> pd.DataFrame:
        logger.info(f"Starting batch scoring run for model '{self.model_name}'")
        data = self.load_data(input_path)
        predictions = self.score_batch(data)
        self.save_results(predictions, output_path)
        if "status" in predictions.columns:
            n_errors = int((predictions["status"] == "error").sum())
            if n_errors:
                logger.warning(
                    f"{n_errors} of {len(predictions)} records failed scoring."
                )
        logger.info("Batch scoring completed successfully")
        return predictions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch scoring for Nexora clinical prediction models"
    )
    parser.add_argument(
        "--model-name", required=True, help="Registered model name, e.g. deep_fm"
    )
    parser.add_argument(
        "--model-version", default=None, help="Model version (default: latest)"
    )
    parser.add_argument(
        "--input-path",
        required=True,
        help="Path to input data (.csv, .parquet, or .json)",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="Path to save results (.csv, .parquet, or .json)",
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        help="Score via a running Nexora REST API instead of loading the model in-process",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the Nexora API (used with --use-api)",
    )
    parser.add_argument(
        "--api-batch-size",
        type=int,
        default=50,
        help="Patients per API request (used with --use-api)",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Include per-patient explanations (local scoring only)",
    )
    parser.add_argument(
        "--registry-path", default=None, help="Path to a custom model_registry.json"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        scorer = BatchScorer(
            model_name=args.model_name,
            model_version=args.model_version,
            use_api=args.use_api,
            api_url=args.api_url,
            api_batch_size=args.api_batch_size,
            include_explanations=args.explain,
            registry_path=args.registry_path,
        )
        scorer.run(args.input_path, args.output_path)
        return 0
    except Exception as e:
        logger.error(f"Error in batch scoring: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
