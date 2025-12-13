import os
import json
from typing import Dict, Any, Optional
from .base_model import BaseModel


class ModelRegistry:
    """
    Manages the registration, loading, and retrieval of different model versions.
    In a real-world scenario, this would interact with a persistent model store (e.g., MLflow, S3).
    """

    def __init__(self, registry_path: str = "model_registry.json") -> Any:
        self.registry_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), registry_path
        )
        self.models: Dict[str, Dict[str, BaseModel]] = {}
        self._load_registry()

    def _load_registry(self) -> Any:
        """Loads the model metadata from a JSON file."""
        if not os.path.exists(self.registry_path):
            self.metadata = {
                "deep_fm": {
                    "latest": {
                        "path": "models/deep_fm_v1.h5",
                        "config": {"name": "deep_fm", "version": "1.0.0"},
                    }
                },
                "survival_analysis": {
                    "latest": {
                        "path": "models/survival_v1.pkl",
                        "config": {"name": "survival_analysis", "version": "1.0.0"},
                    }
                },
                "transformer_model": {
                    "latest": {
                        "path": "models/transformer_v1.pt",
                        "config": {"name": "transformer_model", "version": "1.0.0"},
                    }
                },
            }
            self._save_registry()
            return
        with open(self.registry_path, "r") as f:
            self.metadata = json.load(f)

    def _save_registry(self) -> Any:
        """Saves the model metadata to a JSON file."""
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def register_model(
        self, model_name: str, version: str, path: str, config: Dict[str, Any]
    ) -> Any:
        """Registers a new model version."""
        if model_name not in self.metadata:
            self.metadata[model_name] = {}
        self.metadata[model_name][version] = {"path": path, "config": config}
        self.metadata[model_name]["latest"] = self.metadata[model_name][version]
        self._save_registry()

    def get_model(
        self, model_name: str, version: Optional[str] = "latest"
    ) -> BaseModel:
        """Retrieves a specific model instance."""
        version = version or "latest"
        if model_name not in self.metadata or version not in self.metadata[model_name]:
            raise ValueError(
                f"Model {model_name} version {version} not found in registry."
            )
        model_info = self.metadata[model_name][version]
        model_info["path"]
        model_config = model_info["config"]
        if model_name == "deep_fm":
            from .deep_fm import DeepFMModel

            model_class = DeepFMModel
        elif model_name == "survival_analysis":
            from .survival_analysis import SurvivalAnalysisModel

            model_class = SurvivalAnalysisModel
        elif model_name == "transformer_model":
            from .transformer_model import TransformerModel

            model_class = TransformerModel
        else:
            raise NotImplementedError(
                f"Model class for {model_name} is not implemented."
            )
        if model_name in self.models and version in self.models[model_name]:
            return self.models[model_name][version]
        model_instance = model_class(model_config)
        if model_name not in self.models:
            self.models[model_name] = {}
        self.models[model_name][version] = model_instance
        return model_instance

    def list_models(self) -> Dict[str, Any]:
        """Returns a list of all registered models and their versions."""
        return {
            name: {
                version: info["config"]
                for version, info in versions.items()
                if version != "latest"
            }
            for name, versions in self.metadata.items()
        }


if not os.path.exists(os.path.join(os.path.dirname(__file__), "model_registry.json")):
    ModelRegistry()
