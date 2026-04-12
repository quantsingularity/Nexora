import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import pytest
from ml_core.models.model_registry import ModelRegistry
from ml_core.models.transformer_model import TransformerModel


@pytest.fixture
def model_config():
    return {
        "name": "readmission_risk",
        "version": "1.0.0",
        "vocab_size": 100,
        "d_model": 16,
        "nhead": 2,
        "num_layers": 1,
        "dim_feedforward": 32,
        "num_classes": 1,
    }


@pytest.fixture
def registry(tmp_path, model_config):
    return ModelRegistry(registry_path=str(tmp_path / "registry.json"))


def test_model_registry_initialization(tmp_path):
    reg = ModelRegistry(registry_path=str(tmp_path / "registry.json"))
    assert reg is not None
    assert hasattr(reg, "models")
    assert hasattr(reg, "get_model")
    assert hasattr(reg, "register_model")


def test_model_registration(registry, model_config):
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    assert "readmission_risk" in registry.models
    assert "1.0.0" in registry.models["readmission_risk"]


def test_model_retrieval(registry, model_config):
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    retrieved = registry.get_model("readmission_risk", "1.0.0")
    assert retrieved is not None
    assert retrieved is model


def test_model_retrieval_latest(registry, model_config):
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    retrieved = registry.get_model("readmission_risk", "latest")
    assert retrieved is not None


def test_model_not_found_raises(registry):
    with pytest.raises(ValueError):
        registry.get_model("nonexistent_model", "1.0.0")


def test_model_version_not_found_raises(registry, model_config):
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    with pytest.raises(ValueError):
        registry.get_model("readmission_risk", "99.0.0")


def test_list_models(registry, model_config):
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    listed = registry.list_models()
    assert "readmission_risk" in listed


def test_default_registry_has_models(tmp_path):
    reg = ModelRegistry(registry_path=str(tmp_path / "new_registry.json"))
    models = reg.list_models()
    assert len(models) > 0
    assert "transformer_model" in models


def test_register_path_only(registry):
    registry.register_model(
        "test_model",
        "1.0.0",
        "models/test.pkl",
        config={"name": "test_model", "version": "1.0.0"},
    )
    assert "test_model" in registry.metadata


def test_multiple_versions(registry, model_config):
    m1 = TransformerModel(model_config)
    cfg2 = {**model_config, "version": "2.0.0"}
    m2 = TransformerModel(cfg2)
    registry.register_model("readmission_risk", "1.0.0", m1)
    registry.register_model("readmission_risk", "2.0.0", m2)
    listed = registry.list_models()
    assert "1.0.0" in listed["readmission_risk"]
    assert "2.0.0" in listed["readmission_risk"]


def test_delete_model(registry, model_config):
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)
    registry.delete_model("readmission_risk", "1.0.0")
    with pytest.raises(Exception):
        registry.get_model("readmission_risk", "1.0.0")


def test_registry_persistence(tmp_path, model_config):
    path = str(tmp_path / "persist.json")
    reg1 = ModelRegistry(registry_path=path)
    reg1.register_model(
        "my_model",
        "1.0.0",
        "models/m.pkl",
        config={"name": "my_model", "version": "1.0.0"},
    )
    reg2 = ModelRegistry(registry_path=path)
    assert "my_model" in reg2.metadata


def test_get_model_by_name_deep_fm(tmp_path):
    reg = ModelRegistry(registry_path=str(tmp_path / "r.json"))
    model = reg.get_model("deep_fm", "latest")
    assert model is not None
    result = model.predict(
        {"patient_id": "P001", "demographics": {}, "clinical_events": []}
    )
    assert "risk_score" in result


def test_get_model_by_name_survival(tmp_path):
    reg = ModelRegistry(registry_path=str(tmp_path / "r.json"))
    model = reg.get_model("survival_analysis", "latest")
    assert model is not None
    result = model.predict(
        {"patient_id": "P001", "demographics": {}, "clinical_events": []}
    )
    assert "risk_score" in result


def test_get_model_by_name_transformer(tmp_path):
    reg = ModelRegistry(registry_path=str(tmp_path / "r.json"))
    model = reg.get_model("transformer_model", "latest")
    assert model is not None
    result = model.predict(
        {"patient_id": "P001", "demographics": {}, "clinical_events": []}
    )
    assert "risk_score" in result
