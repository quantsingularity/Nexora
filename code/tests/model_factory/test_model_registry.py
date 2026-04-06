import os
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest
from model_factory.model_registry import ModelRegistry
from model_factory.transformer_model import TransformerModel


@pytest.fixture
def model_config() -> Any:
    return {
        "name": "readmission_risk",
        "version": "1.0.0",
        "vocab_size": 500,
        "d_model": 32,
        "nhead": 2,
        "num_layers": 1,
        "dim_feedforward": 64,
        "num_classes": 1,
    }


@pytest.fixture
def sample_data() -> Any:
    return {
        "patient_id": "123",
        "features": {"age": 50, "previous_admissions": 2, "gender": "M"},
        "demographics": {"age": 50, "gender": "M"},
        "clinical_events": [],
    }


@pytest.fixture
def registry(tmp_path, model_config):
    reg = ModelRegistry(registry_path=str(tmp_path / "registry.json"))
    return reg


def test_model_registry_initialization(tmp_path) -> None:
    registry = ModelRegistry(registry_path=str(tmp_path / "registry.json"))
    assert registry is not None
    assert hasattr(registry, "models")
    assert hasattr(registry, "get_model")
    assert hasattr(registry, "register_model")


def test_model_registration(registry, model_config) -> None:
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    assert "readmission_risk" in registry.models
    assert "1.0.0" in registry.models["readmission_risk"]


def test_model_retrieval(registry, model_config) -> None:
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    retrieved = registry.get_model("readmission_risk", "1.0.0")
    assert retrieved is not None
    assert isinstance(retrieved, TransformerModel)


def test_model_prediction(registry, model_config, sample_data) -> None:
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    predictions = model.predict(sample_data)
    assert "risk_score" in predictions
    assert isinstance(predictions["risk_score"], float)
    assert 0 <= predictions["risk_score"] <= 1


def test_model_explanation(registry, model_config, sample_data) -> None:
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    explanation = model.explain(sample_data)
    assert "method" in explanation
    assert "values" in explanation
    assert isinstance(explanation["values"], list)


def test_model_versioning(registry, model_config) -> None:
    cfg2 = dict(model_config)
    cfg2["version"] = "2.0.0"
    model_v1 = TransformerModel(model_config)
    model_v2 = TransformerModel(cfg2)
    registry.register_model("readmission_risk", "1.0.0", model_v1)
    registry.register_model("readmission_risk", "2.0.0", model_v2)
    assert len(registry.models["readmission_risk"]) == 2
    assert registry.get_model("readmission_risk", "1.0.0") is not registry.get_model(
        "readmission_risk", "2.0.0"
    )


def test_model_validation(registry, model_config) -> None:
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    invalid_data = {"patient_id": "123"}  # no features or demographics
    with pytest.raises(ValueError):
        model.predict(invalid_data)


def test_model_uncertainty(registry, model_config, sample_data) -> None:
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    predictions = model.predict_with_uncertainty(sample_data)
    assert "risk" in predictions
    assert "uncertainty" in predictions
    assert "confidence_interval" in predictions["uncertainty"]
    assert len(predictions["uncertainty"]["confidence_interval"]) == 2


def test_list_models(registry, model_config) -> None:
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    models_list = registry.list_models()
    assert "readmission_risk" in models_list


def test_model_not_found(registry) -> None:
    with pytest.raises(ValueError):
        registry.get_model("nonexistent_model_xyz", "1.0.0")
