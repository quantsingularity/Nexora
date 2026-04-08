import json
import os
from typing import Any, Dict, Optional

from model_factory.base_model import BaseModel


class ModelRegistry:
    """
    Manages the registration, loading, and retrieval of different model versions.
    """

    def __init__(self, registry_path: str = "model_registry.json") -> None:
        if os.path.isabs(registry_path):
            self.registry_path = registry_path
        else:
            self.registry_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), registry_path
            )
        self.models: Dict[str, Dict[str, BaseModel]] = {}
        self._load_registry()

    def _load_registry(self) -> None:
        if not os.path.exists(self.registry_path):
            self.metadata: Dict[str, Any] = {
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

    def _save_registry(self) -> None:
        registry_dir = os.path.dirname(self.registry_path)
        if registry_dir:
            os.makedirs(registry_dir, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def register_model(
        self,
        model_name: str,
        version: str,
        model_or_path: Any,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        if model_name not in self.metadata:
            self.metadata[model_name] = {}

        if isinstance(model_or_path, BaseModel):
            model_instance = model_or_path
            path = config.get("path", "") if config else ""
            model_config = config or getattr(
                model_instance, "config", {"name": model_name, "version": version}
            )
        else:
            path = model_or_path
            model_config = config or {"name": model_name, "version": version}
            model_instance = None

        self.metadata[model_name][version] = {"path": path, "config": model_config}
        # Update "latest" alias to point to the most recently registered version
        self.metadata[model_name]["latest"] = self.metadata[model_name][version]
        self._save_registry()

        if model_instance is not None:
            if model_name not in self.models:
                self.models[model_name] = {}
            self.models[model_name][version] = model_instance
            # Cache under "latest" key as well so get_model("latest") hits cache
            self.models[model_name]["latest"] = model_instance

    def get_model(
        self, model_name: str, version: Optional[str] = "latest"
    ) -> BaseModel:
        version = version or "latest"
        if model_name not in self.metadata or version not in self.metadata[model_name]:
            raise ValueError(
                f"Model {model_name} version {version} not found in registry."
            )

        # Return cached instance if available
        if model_name in self.models and version in self.models[model_name]:
            return self.models[model_name][version]

        model_info = self.metadata[model_name][version]
        model_config = model_info["config"]

        if model_name == "deep_fm":
            from model_factory.deep_fm import DeepFMModel

            model_class = DeepFMModel
        elif model_name == "survival_analysis":
            from model_factory.survival_analysis import SurvivalAnalysisModel

            model_class = SurvivalAnalysisModel
        elif model_name == "transformer_model":
            from model_factory.transformer_model import TransformerModel

            model_class = TransformerModel
        else:
            raise NotImplementedError(
                f"Model class for {model_name} is not implemented."
            )

        model_instance = model_class(model_config)
        if model_name not in self.models:
            self.models[model_name] = {}
        self.models[model_name][version] = model_instance
        return model_instance

    def list_models(self) -> Dict[str, Any]:
        return {
            name: {
                ver: info["config"] for ver, info in versions.items() if ver != "latest"
            }
            for name, versions in self.metadata.items()
        }

    def delete_model(self, model_name: str, version: str) -> None:
        """Remove a specific model version from the registry."""
        if model_name not in self.metadata:
            raise ValueError(f"Model {model_name} not found in registry.")
        if version not in self.metadata[model_name]:
            raise ValueError(
                f"Version {version} of model {model_name} not found in registry."
            )
        del self.metadata[model_name][version]
        # Clean up in-memory cache
        if model_name in self.models and version in self.models[model_name]:
            del self.models[model_name][version]
        # Rebuild latest if needed
        remaining = [v for v in self.metadata[model_name] if v != "latest"]
        if remaining:
            self.metadata[model_name]["latest"] = self.metadata[model_name][
                remaining[-1]
            ]
        elif "latest" in self.metadata[model_name]:
            del self.metadata[model_name]["latest"]
        if not self.metadata[model_name]:
            del self.metadata[model_name]
        self._save_registry()
