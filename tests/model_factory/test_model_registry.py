import pytest

from src.model_factory.model_registry import ModelRegistry
from src.model_factory.transformer_model import TransformerModel


@pytest.fixture
def model_config():
    return {
        "model_type": "deepfm",
        "embedding_size": 64,
        "hidden_units": [256, 128, 64],
        "dropout_rate": 0.2,
        "l2_regularization": 0.001,
        "learning_rate": 0.001,
        "batch_size": 32,
        "epochs": 100,
        "early_stopping_patience": 10,
        "feature_columns": {
            "numeric": ["age", "previous_admissions"],
            "categorical": {"gender": {"vocabulary_size": 3, "embedding_dim": 8}},
        },
    }


@pytest.fixture
def sample_data():
    return {
        "patient_id": "123",
        "features": {"age": 50, "previous_admissions": 2, "gender": "M"},
    }


def test_model_registry_initialization():
    registry = ModelRegistry()
    assert registry is not None
    assert hasattr(registry, "models")
    assert hasattr(registry, "get_model")
    assert hasattr(registry, "register_model")


def test_model_registration(model_config):
    registry = ModelRegistry()
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)

    assert "readmission_risk" in registry.models
    assert "1.0.0" in registry.models["readmission_risk"]


def test_model_retrieval(model_config):
    registry = ModelRegistry()
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)

    retrieved_model = registry.get_model("readmission_risk", "1.0.0")
    assert retrieved_model is not None
    assert isinstance(retrieved_model, TransformerModel)


def test_model_prediction(model_config, sample_data):
    registry = ModelRegistry()
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)

    predictions = model.predict(sample_data)
    assert "risk" in predictions
    assert isinstance(predictions["risk"], float)
    assert 0 <= predictions["risk"] <= 1


def test_model_explanation(model_config, sample_data):
    registry = ModelRegistry()
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)

    explanation = model.explain(sample_data)
    assert "method" in explanation
    assert "values" in explanation
    assert isinstance(explanation["values"], list)


def test_model_versioning(model_config):
    registry = ModelRegistry()
    model_v1 = TransformerModel(model_config)
    model_v2 = TransformerModel(model_config)

    registry.register_model("readmission_risk", "1.0.0", model_v1)
    registry.register_model("readmission_risk", "2.0.0", model_v2)

    assert len(registry.models["readmission_risk"]) == 2
    assert registry.get_model("readmission_risk", "1.0.0") != registry.get_model(
        "readmission_risk", "2.0.0"
    )


def test_model_validation(model_config, sample_data):
    registry = ModelRegistry()
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)

    # Test with invalid data
    invalid_data = {"patient_id": "123"}  # Missing features
    with pytest.raises(ValueError):
        model.predict(invalid_data)


def test_model_uncertainty(model_config, sample_data):
    registry = ModelRegistry()
    model = TransformerModel(model_config)
    registry.register_model("readmission_risk", "1.0.0", model)

    predictions = model.predict_with_uncertainty(sample_data)
    assert "risk" in predictions
    assert "uncertainty" in predictions
    assert "confidence_interval" in predictions["uncertainty"]
    assert len(predictions["uncertainty"]["confidence_interval"]) == 2
