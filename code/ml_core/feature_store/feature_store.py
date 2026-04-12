"""
Feature Store for Nexora ML Core

Lightweight feature store backed by Parquet files with an in-memory cache.
Supports upsert, lookup by patient_id, and time-windowed retrieval.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    Persistent feature store for patient feature vectors.

    Features are stored as Parquet files, partitioned by date.
    An in-memory cache prevents redundant disk reads in the same session.

    Usage::

        store = FeatureStore(base_path="data/feature_store")
        store.upsert(patient_id="P001", features={"age": 65, "creatinine": 1.2})
        row = store.get("P001")
        recent = store.get_recent(days=7)
    """

    _PATIENT_COL = "patient_id"
    _TS_COL = "feature_timestamp"

    def __init__(self, base_path: str = "data/feature_store") -> None:
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"FeatureStore initialised at '{base_path}'")

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert(
        self,
        patient_id: str,
        features: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Insert or update feature row for *patient_id*."""
        ts = (timestamp or datetime.utcnow()).isoformat()
        row = {self._PATIENT_COL: patient_id, self._TS_COL: ts, **features}
        self._cache[patient_id] = row

        partition = (timestamp or datetime.utcnow()).strftime("%Y-%m-%d")
        path = self._partition_path(partition)
        self._append_row(path, row)
        logger.debug(
            f"Upserted features for patient '{patient_id}' (partition={partition})"
        )

    def upsert_batch(
        self,
        records: List[Dict[str, Any]],
        patient_id_key: str = "patient_id",
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Upsert a list of feature dicts in one shot."""
        for record in records:
            pid = record.get(patient_id_key, "unknown")
            features = {k: v for k, v in record.items() if k != patient_id_key}
            self.upsert(pid, features, timestamp=timestamp)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve latest features for *patient_id* (cache-first)."""
        if patient_id in self._cache:
            return self._cache[patient_id]

        all_data = self._load_all()
        if all_data.empty:
            return None
        mask = all_data[self._PATIENT_COL] == patient_id
        if not mask.any():
            return None
        row = (
            all_data[mask].sort_values(self._TS_COL, ascending=False).iloc[0].to_dict()
        )
        self._cache[patient_id] = row
        return row

    def get_batch(self, patient_ids: List[str]) -> pd.DataFrame:
        """Return a DataFrame of latest features for each patient in the list."""
        all_data = self._load_all()
        if all_data.empty:
            return pd.DataFrame()
        mask = all_data[self._PATIENT_COL].isin(patient_ids)
        subset = all_data[mask]
        latest = subset.sort_values(self._TS_COL, ascending=False).drop_duplicates(
            subset=[self._PATIENT_COL]
        )
        return latest.reset_index(drop=True)

    def get_recent(self, days: int = 7) -> pd.DataFrame:
        """Return all feature rows written within the last *days* days."""
        all_data = self._load_all()
        if all_data.empty:
            return pd.DataFrame()
        cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=days)
        ts_col = pd.to_datetime(all_data[self._TS_COL], utc=True, errors="coerce")
        return all_data[ts_col >= cutoff].reset_index(drop=True)

    def list_patients(self) -> List[str]:
        """Return sorted list of all known patient IDs."""
        all_data = self._load_all()
        if all_data.empty:
            return []
        return sorted(all_data[self._PATIENT_COL].unique().tolist())

    def stats(self) -> Dict[str, Any]:
        """Return summary statistics about the feature store."""
        all_data = self._load_all()
        if all_data.empty:
            return {"n_patients": 0, "n_rows": 0, "n_features": 0, "partitions": []}
        return {
            "n_patients": all_data[self._PATIENT_COL].nunique(),
            "n_rows": len(all_data),
            "n_features": len(all_data.columns) - 2,  # exclude patient_id & timestamp
            "partitions": self._list_partitions(),
        }

    # ------------------------------------------------------------------
    # Delete / maintenance
    # ------------------------------------------------------------------

    def delete_patient(self, patient_id: str) -> None:
        """Remove all feature rows for *patient_id* (HIPAA right-to-erasure)."""
        self._cache.pop(patient_id, None)
        for partition in self._list_partitions():
            path = self._partition_path(partition)
            if not os.path.exists(path):
                continue
            df = pd.read_parquet(path)
            df = df[df[self._PATIENT_COL] != patient_id]
            df.to_parquet(path, index=False)
        logger.info(f"Deleted all feature rows for patient '{patient_id}'")

    def clear_cache(self) -> None:
        """Flush the in-memory cache."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _partition_path(self, partition: str) -> str:
        return os.path.join(self.base_path, f"features_{partition}.parquet")

    def _list_partitions(self) -> List[str]:
        files = [
            f.replace("features_", "").replace(".parquet", "")
            for f in os.listdir(self.base_path)
            if f.startswith("features_") and f.endswith(".parquet")
        ]
        return sorted(files)

    def _append_row(self, path: str, row: Dict[str, Any]) -> None:
        new_df = pd.DataFrame([row])
        if os.path.exists(path):
            existing = pd.read_parquet(path)
            # Remove any stale row for this patient before appending
            existing = existing[existing[self._PATIENT_COL] != row[self._PATIENT_COL]]
            combined = pd.concat([existing, new_df], ignore_index=True)
        else:
            combined = new_df
        combined.to_parquet(path, index=False)

    def _load_all(self) -> pd.DataFrame:
        partitions = self._list_partitions()
        if not partitions:
            return pd.DataFrame()
        frames = []
        for p in partitions:
            path = self._partition_path(p)
            try:
                frames.append(pd.read_parquet(path))
            except Exception as e:
                logger.warning(f"Could not read partition '{path}': {e}")
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
