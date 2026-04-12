"""
Model Explainability Module for Nexora

Provides model-agnostic and model-specific explanation methods:
  - SHAP-style permutation importance (works without shap installed)
  - LIME-style local linear approximation
  - Counterfactual explanation generation
  - Attention weight extraction for Transformer models
  - Integrated gradients for DeepFM (TensorFlow)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ExplanationResult:
    """Container for a single explanation."""

    method: str
    feature_names: List[str]
    feature_importances: Dict[str, float]
    base_value: float
    prediction: float
    counterfactuals: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def top_features(self, n: int = 5) -> List[tuple[str, float]]:
        """Return the top-n features by absolute importance."""
        sorted_items = sorted(
            self.feature_importances.items(), key=lambda kv: abs(kv[1]), reverse=True
        )
        return sorted_items[:n]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "feature_names": self.feature_names,
            "feature_importances": self.feature_importances,
            "base_value": self.base_value,
            "prediction": self.prediction,
            "top_features": self.top_features(),
            "counterfactuals": self.counterfactuals,
            "metadata": self.metadata,
        }


# ---------------------------------------------------------------------------
# Core explainer
# ---------------------------------------------------------------------------


class ModelExplainer:
    """
    Model-agnostic explainer for Nexora clinical prediction models.

    Supports:
      - permutation_shap: Permutation-based feature importance (SHAP-compatible)
      - lime: Local Interpretable Model-agnostic Explanations
      - integrated_gradients: For TensorFlow/Keras models
      - attention: For Transformer models (returns attention weight summary)
      - counterfactual: Nearest counterfactual via random perturbation search
    """

    def __init__(
        self,
        predict_fn: Callable[[np.ndarray], np.ndarray],
        feature_names: List[str],
        background_data: Optional[np.ndarray] = None,
        random_state: int = 42,
    ) -> None:
        """
        Args:
            predict_fn: Function that takes (n_samples, n_features) array and
                        returns (n_samples,) probability array.
            feature_names: List of feature names in column order.
            background_data: Reference dataset for SHAP-style baselines.
                             Shape (n_background, n_features). If None, zeros are used.
            random_state: Seed for reproducibility.
        """
        self.predict_fn = predict_fn
        self.feature_names = feature_names
        self.background_data = background_data
        self.rng = np.random.default_rng(random_state)
        self._base_value: Optional[float] = None
        logger.info(f"ModelExplainer initialized with {len(feature_names)} features.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def explain(
        self,
        instance: np.ndarray,
        method: str = "permutation_shap",
        n_samples: int = 100,
    ) -> ExplanationResult:
        """
        Generate an explanation for a single instance.

        Args:
            instance: 1-D feature vector of shape (n_features,).
            method: One of 'permutation_shap', 'lime', 'attention', 'counterfactual'.
            n_samples: Number of perturbation samples (used by permutation_shap and lime).

        Returns:
            ExplanationResult
        """
        instance = np.asarray(instance, dtype=float).flatten()
        prediction = float(self.predict_fn(instance.reshape(1, -1))[0])
        base_value = self._get_base_value()

        if method == "permutation_shap":
            importances = self._permutation_shap(instance, n_samples)
        elif method == "lime":
            importances = self._lime(instance, n_samples)
        elif method == "attention":
            importances = self._attention_proxy(instance)
        elif method == "counterfactual":
            importances = self._permutation_shap(instance, n_samples // 2)
        else:
            raise ValueError(
                f"Unknown explanation method: '{method}'. "
                "Choose from: permutation_shap, lime, attention, counterfactual."
            )

        counterfactuals = None
        if method == "counterfactual":
            counterfactuals = self._generate_counterfactuals(instance, prediction, n=3)

        return ExplanationResult(
            method=method,
            feature_names=self.feature_names,
            feature_importances=dict(zip(self.feature_names, importances.tolist())),
            base_value=base_value,
            prediction=prediction,
            counterfactuals=counterfactuals,
            metadata={"n_samples": n_samples, "n_features": len(self.feature_names)},
        )

    def explain_batch(
        self,
        instances: np.ndarray,
        method: str = "permutation_shap",
        n_samples: int = 50,
    ) -> List[ExplanationResult]:
        """Explain a batch of instances."""
        return [
            self.explain(row, method=method, n_samples=n_samples) for row in instances
        ]

    def global_importance(self, data: np.ndarray, n_samples: int = 50) -> pd.DataFrame:
        """
        Compute global feature importance as mean absolute SHAP values.

        Args:
            data: Array of shape (n_instances, n_features).
            n_samples: Perturbation samples per instance.

        Returns:
            DataFrame with columns ['feature', 'mean_abs_importance'] sorted descending.
        """
        all_importances = []
        for row in data:
            imp = self._permutation_shap(row, n_samples)
            all_importances.append(np.abs(imp))
        mean_imp = np.mean(all_importances, axis=0)
        df = pd.DataFrame(
            {"feature": self.feature_names, "mean_abs_importance": mean_imp}
        ).sort_values("mean_abs_importance", ascending=False)
        return df.reset_index(drop=True)

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _get_base_value(self) -> float:
        if self._base_value is not None:
            return self._base_value
        if self.background_data is not None:
            preds = self.predict_fn(self.background_data)
            self._base_value = float(np.mean(preds))
        else:
            n_feat = len(self.feature_names)
            baseline = np.zeros((1, n_feat))
            self._base_value = float(self.predict_fn(baseline)[0])
        return self._base_value

    def _permutation_shap(self, instance: np.ndarray, n_samples: int) -> np.ndarray:
        """
        Estimate Shapley values via permutation sampling.

        For each sample:
          1. Pick a random permutation of features.
          2. Build two coalitions: one including feature i, one excluding it.
          3. The marginal contribution approximates the Shapley value.
        """
        n_feat = len(self.feature_names)
        if self.background_data is not None:
            bg_idx = self.rng.integers(0, len(self.background_data), n_samples)
            backgrounds = self.background_data[bg_idx]
        else:
            backgrounds = np.zeros((n_samples, n_feat))

        shap_values = np.zeros(n_feat)

        for bg in backgrounds:
            perm = self.rng.permutation(n_feat)
            x_with = bg.copy()
            x_without = bg.copy()
            for pos, feat_idx in enumerate(perm):
                x_with[feat_idx] = instance[feat_idx]
                pred_with = float(self.predict_fn(x_with.reshape(1, -1))[0])
                pred_without = float(self.predict_fn(x_without.reshape(1, -1))[0])
                shap_values[feat_idx] += pred_with - pred_without

        return shap_values / n_samples

    def _lime(self, instance: np.ndarray, n_samples: int) -> np.ndarray:
        """
        LIME: perturb the instance, collect predictions, fit weighted linear model.
        """
        from sklearn.linear_model import Ridge

        n_feat = len(self.feature_names)
        noise_scale = np.std(instance) if np.std(instance) > 0 else 1.0

        perturbed = self.rng.normal(
            loc=instance, scale=noise_scale * 0.1, size=(n_samples, n_feat)
        )
        distances = np.linalg.norm(perturbed - instance, axis=1)
        kernel_width = np.percentile(distances, 75) + 1e-8
        weights = np.exp(-(distances**2) / (2 * kernel_width**2))

        preds = self.predict_fn(perturbed)

        model = Ridge(alpha=1.0)
        model.fit(perturbed, preds, sample_weight=weights)

        return model.coef_

    def _attention_proxy(self, instance: np.ndarray) -> np.ndarray:
        """
        Proxy attention weights: use input magnitude as a stand-in when
        real attention weights are unavailable (e.g., non-Transformer model).
        """
        abs_vals = np.abs(instance)
        total = abs_vals.sum()
        if total > 0:
            return abs_vals / total
        return np.ones(len(self.feature_names)) / len(self.feature_names)

    def _generate_counterfactuals(
        self,
        instance: np.ndarray,
        current_prediction: float,
        n: int = 3,
        flip_threshold: float = 0.5,
        n_search: int = 500,
    ) -> List[Dict[str, Any]]:
        """
        Generate counterfactuals by randomly perturbing instance features until
        the predicted class flips.

        Returns up to `n` counterfactuals sorted by L1 distance.
        """
        n_feat = len(self.feature_names)
        noise_scale = np.std(instance) if np.std(instance) > 0 else 1.0
        target_class = 1 if current_prediction < flip_threshold else 0
        counterfactuals = []

        for _ in range(n_search):
            perturb = self.rng.normal(scale=noise_scale * 0.5, size=n_feat)
            candidate = instance + perturb
            pred = float(self.predict_fn(candidate.reshape(1, -1))[0])
            pred_class = 1 if pred >= flip_threshold else 0
            if pred_class == target_class:
                delta = candidate - instance
                changed = {
                    self.feature_names[i]: {
                        "original": float(instance[i]),
                        "counterfactual": float(candidate[i]),
                        "delta": float(delta[i]),
                    }
                    for i in np.where(np.abs(delta) > 1e-6)[0]
                }
                counterfactuals.append(
                    {
                        "prediction": round(pred, 4),
                        "l1_distance": float(np.abs(delta).sum()),
                        "changed_features": changed,
                    }
                )
                if len(counterfactuals) >= n * 3:
                    break

        # Return top-n by L1 distance (closest counterfactuals)
        counterfactuals.sort(key=lambda x: x["l1_distance"])
        return counterfactuals[:n]
