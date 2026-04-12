"""
Model Artifact Versioning for Nexora ML Core

Tracks trained model artifacts with:
  - SHA-256 checksums for integrity verification
  - Full training metadata (hyperparameters, dataset hash, metrics)
  - Lineage tracking (parent model, training data snapshot)
  - Semantic versioning helpers
  - Promotion workflow (staging → production → archived)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ModelStage(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class ArtifactIntegrityError(Exception):
    """Raised when a stored artifact fails its checksum verification."""


class ModelArtifactStore:
    """
    Filesystem-backed artifact store with versioning, checksums, and promotion.

    Directory layout::

        artifacts/
          deep_fm/
            1.0.0/
              model.bin          ← actual model file
              metadata.json      ← training run metadata
            1.1.0/
              ...
          survival_analysis/
            ...
          _registry.json         ← index of all artifacts

    Usage::

        store = ModelArtifactStore("artifacts")
        store.register(
            model_name="deep_fm",
            version="1.0.0",
            artifact_path="/tmp/deep_fm.h5",
            metrics={"auc": 0.87},
            hyperparameters={"layers": [256, 128]},
        )
        meta = store.get_metadata("deep_fm", "1.0.0")
        store.promote("deep_fm", "1.0.0", ModelStage.PRODUCTION)
        prod = store.get_production_version("deep_fm")
    """

    _REGISTRY_FILE = "_registry.json"

    def __init__(self, base_path: str = "artifacts") -> None:
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self._registry: Dict[str, Any] = self._load_registry()
        logger.info(f"ModelArtifactStore initialised at '{base_path}'")

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        model_name: str,
        version: str,
        artifact_path: str,
        metrics: Optional[Dict[str, float]] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        training_data_hash: Optional[str] = None,
        parent_version: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a model artifact, copying it into the managed store.

        Args:
            model_name: Logical model name (e.g. 'deep_fm').
            version: Semantic version string (e.g. '1.2.3').
            artifact_path: Path to the trained model file to store.
            metrics: Evaluation metrics dict (e.g. {'auc': 0.87, 'brier': 0.11}).
            hyperparameters: Training hyperparameters.
            training_data_hash: SHA-256 of the training dataset for lineage.
            parent_version: Version this model was fine-tuned from.
            tags: Arbitrary string key-value tags.

        Returns:
            Metadata dict for the registered artifact.
        """
        dest_dir = self._artifact_dir(model_name, version)
        os.makedirs(dest_dir, exist_ok=True)

        ext = os.path.splitext(artifact_path)[1] or ".bin"
        dest_path = os.path.join(dest_dir, f"model{ext}")
        shutil.copy2(artifact_path, dest_path)
        checksum = self._sha256(dest_path)

        metadata: Dict[str, Any] = {
            "model_name": model_name,
            "version": version,
            "stage": ModelStage.DEVELOPMENT,
            "registered_at": datetime.utcnow().isoformat(),
            "artifact_path": dest_path,
            "checksum_sha256": checksum,
            "metrics": metrics or {},
            "hyperparameters": hyperparameters or {},
            "training_data_hash": training_data_hash,
            "parent_version": parent_version,
            "tags": tags or {},
            "promotion_history": [],
        }

        meta_path = os.path.join(dest_dir, "metadata.json")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Update registry index
        if model_name not in self._registry:
            self._registry[model_name] = {}
        self._registry[model_name][version] = {
            "stage": ModelStage.DEVELOPMENT,
            "registered_at": metadata["registered_at"],
            "checksum_sha256": checksum,
        }
        self._save_registry()

        logger.info(
            f"Registered artifact: {model_name} v{version} "
            f"(stage=development, checksum={checksum[:12]}…)"
        )
        return metadata

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get_metadata(self, model_name: str, version: str) -> Dict[str, Any]:
        """Return full metadata for a specific model version."""
        meta_path = os.path.join(
            self._artifact_dir(model_name, version), "metadata.json"
        )
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"No artifact found for {model_name} v{version}")
        with open(meta_path) as f:
            return json.load(f)

    def get_artifact_path(
        self, model_name: str, version: str, verify_checksum: bool = True
    ) -> str:
        """Return the local path to the model file, optionally verifying integrity."""
        meta = self.get_metadata(model_name, version)
        path = meta["artifact_path"]
        if not os.path.exists(path):
            raise FileNotFoundError(f"Artifact file missing: {path}")
        if verify_checksum:
            actual = self._sha256(path)
            expected = meta["checksum_sha256"]
            if actual != expected:
                raise ArtifactIntegrityError(
                    f"Checksum mismatch for {model_name} v{version}: "
                    f"expected {expected}, got {actual}"
                )
        return path

    def get_production_version(self, model_name: str) -> Optional[str]:
        """Return the version string currently in production, or None."""
        versions = self._registry.get(model_name, {})
        prod = [
            v
            for v, info in versions.items()
            if info.get("stage") == ModelStage.PRODUCTION
        ]
        return prod[-1] if prod else None

    def list_versions(
        self, model_name: str, stage: Optional[ModelStage] = None
    ) -> List[Dict[str, Any]]:
        """List all versions of a model, optionally filtered by stage."""
        versions = self._registry.get(model_name, {})
        result = []
        for v, info in versions.items():
            if stage is None or info.get("stage") == stage:
                result.append({"version": v, **info})
        return sorted(result, key=lambda x: x["registered_at"])

    def list_models(self) -> List[str]:
        """Return names of all registered models."""
        return sorted(self._registry.keys())

    # ------------------------------------------------------------------
    # Promotion workflow
    # ------------------------------------------------------------------

    def promote(
        self,
        model_name: str,
        version: str,
        target_stage: ModelStage,
        promoted_by: str = "system",
        notes: str = "",
    ) -> None:
        """
        Promote a model version to a new stage.

        Promoting to PRODUCTION automatically archives the current
        production version (if any).
        """
        meta = self.get_metadata(model_name, version)
        current_stage = meta.get("stage", ModelStage.DEVELOPMENT)

        if target_stage == ModelStage.PRODUCTION:
            current_prod = self.get_production_version(model_name)
            if current_prod and current_prod != version:
                self._update_stage(model_name, current_prod, ModelStage.ARCHIVED)
                logger.info(
                    f"Auto-archived {model_name} v{current_prod} "
                    "before promoting new production version."
                )

        self._update_stage(model_name, version, target_stage)

        # Record promotion event in metadata
        meta["stage"] = target_stage
        meta["promotion_history"].append(
            {
                "from_stage": current_stage,
                "to_stage": target_stage,
                "promoted_by": promoted_by,
                "promoted_at": datetime.utcnow().isoformat(),
                "notes": notes,
            }
        )
        meta_path = os.path.join(
            self._artifact_dir(model_name, version), "metadata.json"
        )
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        logger.info(
            f"Promoted {model_name} v{version}: {current_stage} → {target_stage}"
        )

    # ------------------------------------------------------------------
    # Deletion
    # ------------------------------------------------------------------

    def delete_version(self, model_name: str, version: str) -> None:
        """Permanently delete an artifact version (must not be in production)."""
        info = self._registry.get(model_name, {}).get(version)
        if info and info.get("stage") == ModelStage.PRODUCTION:
            raise ValueError(
                f"Cannot delete {model_name} v{version}: it is in PRODUCTION. "
                "Archive or promote a replacement first."
            )
        artifact_dir = self._artifact_dir(model_name, version)
        if os.path.exists(artifact_dir):
            shutil.rmtree(artifact_dir)
        self._registry.get(model_name, {}).pop(version, None)
        if not self._registry.get(model_name):
            self._registry.pop(model_name, None)
        self._save_registry()
        logger.info(f"Deleted artifact: {model_name} v{version}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _artifact_dir(self, model_name: str, version: str) -> str:
        return os.path.join(self.base_path, model_name, version)

    def _update_stage(self, model_name: str, version: str, stage: ModelStage) -> None:
        self._registry[model_name][version]["stage"] = stage
        self._save_registry()

    @staticmethod
    def _sha256(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _load_registry(self) -> Dict[str, Any]:
        path = os.path.join(self.base_path, self._REGISTRY_FILE)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    def _save_registry(self) -> None:
        path = os.path.join(self.base_path, self._REGISTRY_FILE)
        with open(path, "w") as f:
            json.dump(self._registry, f, indent=2)
