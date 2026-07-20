"""Tests for ml_core.explainability.explainer"""

import numpy as np
import pytest

from ml_core.explainability.explainer import ExplanationResult, ModelExplainer

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _simple_predict(X: np.ndarray) -> np.ndarray:
    """Deterministic mock: prediction = sigmoid(mean of features)."""
    means = X.mean(axis=1)
    return 1.0 / (1.0 + np.exp(-means))


N_FEAT = 10
FEATURE_NAMES = [f"feature_{i}" for i in range(N_FEAT)]
BACKGROUND = np.random.default_rng(0).random((50, N_FEAT))


@pytest.fixture
def explainer() -> ModelExplainer:
    return ModelExplainer(
        predict_fn=_simple_predict,
        feature_names=FEATURE_NAMES,
        background_data=BACKGROUND,
        random_state=42,
    )


@pytest.fixture
def instance() -> np.ndarray:
    return np.random.default_rng(1).random(N_FEAT)


# ---------------------------------------------------------------------------
# ExplanationResult
# ---------------------------------------------------------------------------


class TestExplanationResult:
    def test_top_features_sorted(self, explainer, instance):
        result = explainer.explain(instance, method="permutation_shap", n_samples=20)
        top = result.top_features(n=3)
        assert len(top) == 3
        # Sorted by absolute importance descending
        abs_vals = [abs(v) for _, v in top]
        assert abs_vals == sorted(abs_vals, reverse=True)

    def test_to_dict_keys(self, explainer, instance):
        result = explainer.explain(instance, method="lime", n_samples=20)
        d = result.to_dict()
        for key in (
            "method",
            "feature_names",
            "feature_importances",
            "base_value",
            "prediction",
            "top_features",
        ):
            assert key in d

    def test_feature_names_count(self, explainer, instance):
        result = explainer.explain(instance)
        assert len(result.feature_importances) == N_FEAT


# ---------------------------------------------------------------------------
# permutation_shap
# ---------------------------------------------------------------------------


class TestPermutationShap:
    def test_returns_explanation_result(self, explainer, instance):
        result = explainer.explain(instance, method="permutation_shap", n_samples=30)
        assert isinstance(result, ExplanationResult)
        assert result.method == "permutation_shap"

    def test_prediction_in_range(self, explainer, instance):
        result = explainer.explain(instance, method="permutation_shap", n_samples=30)
        assert 0.0 <= result.prediction <= 1.0

    def test_importances_sum_approx_delta(self, explainer, instance):
        """Sum of SHAP values should approximately equal prediction - base_value."""
        result = explainer.explain(instance, method="permutation_shap", n_samples=200)
        shap_sum = sum(result.feature_importances.values())
        delta = result.prediction - result.base_value
        # Loose tolerance due to permutation approximation
        assert abs(shap_sum - delta) < 0.5

    def test_no_background_fallback(self, instance):
        """Should work without background data (zeros baseline)."""
        exp = ModelExplainer(
            predict_fn=_simple_predict,
            feature_names=FEATURE_NAMES,
            random_state=0,
        )
        result = exp.explain(instance, method="permutation_shap", n_samples=20)
        assert len(result.feature_importances) == N_FEAT


# ---------------------------------------------------------------------------
# LIME
# ---------------------------------------------------------------------------


class TestLime:
    def test_returns_explanation_result(self, explainer, instance):
        result = explainer.explain(instance, method="lime", n_samples=50)
        assert isinstance(result, ExplanationResult)
        assert result.method == "lime"

    def test_all_features_present(self, explainer, instance):
        result = explainer.explain(instance, method="lime", n_samples=50)
        assert set(result.feature_importances.keys()) == set(FEATURE_NAMES)


# ---------------------------------------------------------------------------
# Attention proxy
# ---------------------------------------------------------------------------


class TestAttention:
    def test_importances_sum_to_one(self, explainer, instance):
        result = explainer.explain(instance, method="attention")
        total = sum(result.feature_importances.values())
        assert abs(total - 1.0) < 1e-6

    def test_non_negative(self, explainer, instance):
        result = explainer.explain(instance, method="attention")
        for v in result.feature_importances.values():
            assert v >= 0.0


# ---------------------------------------------------------------------------
# Counterfactuals
# ---------------------------------------------------------------------------


class TestCounterfactuals:
    def test_counterfactuals_returned(self, explainer, instance):
        result = explainer.explain(instance, method="counterfactual", n_samples=200)
        assert result.counterfactuals is not None

    def test_counterfactual_structure(self, explainer, instance):
        result = explainer.explain(instance, method="counterfactual", n_samples=200)
        for cf in result.counterfactuals:
            assert "prediction" in cf
            assert "l1_distance" in cf
            assert "changed_features" in cf

    def test_counterfactuals_sorted_by_distance(self, explainer, instance):
        result = explainer.explain(instance, method="counterfactual", n_samples=400)
        distances = [cf["l1_distance"] for cf in result.counterfactuals]
        assert distances == sorted(distances)


# ---------------------------------------------------------------------------
# Batch & global
# ---------------------------------------------------------------------------


class TestBatchAndGlobal:
    def test_explain_batch_length(self, explainer):
        batch = np.random.default_rng(5).random((4, N_FEAT))
        results = explainer.explain_batch(batch, n_samples=20)
        assert len(results) == 4

    def test_global_importance_dataframe(self, explainer):
        data = np.random.default_rng(7).random((10, N_FEAT))
        df = explainer.global_importance(data, n_samples=20)
        assert list(df.columns) == ["feature", "mean_abs_importance"]
        assert len(df) == N_FEAT
        # Should be sorted descending
        vals = df["mean_abs_importance"].tolist()
        assert vals == sorted(vals, reverse=True)


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestErrors:
    def test_unknown_method_raises(self, explainer, instance):
        with pytest.raises(ValueError, match="Unknown explanation method"):
            explainer.explain(instance, method="magic_shap")
