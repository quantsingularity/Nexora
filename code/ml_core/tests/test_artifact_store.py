"""Tests for ml_core.versioning.artifact_store"""

import os

import pytest

from ml_core.versioning import ArtifactIntegrityError, ModelArtifactStore, ModelStage


@pytest.fixture
def store(tmp_path):
    return ModelArtifactStore(base_path=str(tmp_path / "artifacts"))


@pytest.fixture
def dummy_model_file(tmp_path):
    path = tmp_path / "model.bin"
    path.write_bytes(b"fake model weights " * 100)
    return str(path)


def test_register_and_get_metadata(store, dummy_model_file):
    meta = store.register(
        model_name="deep_fm",
        version="1.0.0",
        artifact_path=dummy_model_file,
        metrics={"auc": 0.87},
    )
    assert meta["model_name"] == "deep_fm"
    assert meta["version"] == "1.0.0"
    assert meta["metrics"]["auc"] == 0.87
    assert "checksum_sha256" in meta


def test_get_artifact_path_valid(store, dummy_model_file):
    store.register("deep_fm", "1.0.0", dummy_model_file)
    path = store.get_artifact_path("deep_fm", "1.0.0")
    assert os.path.exists(path)


def test_checksum_mismatch_raises(store, dummy_model_file):
    store.register("deep_fm", "1.0.0", dummy_model_file)
    # Corrupt the stored artifact
    meta = store.get_metadata("deep_fm", "1.0.0")
    with open(meta["artifact_path"], "wb") as f:
        f.write(b"corrupted")
    with pytest.raises(ArtifactIntegrityError):
        store.get_artifact_path("deep_fm", "1.0.0", verify_checksum=True)


def test_promote_to_staging(store, dummy_model_file):
    store.register("deep_fm", "1.0.0", dummy_model_file)
    store.promote("deep_fm", "1.0.0", ModelStage.STAGING)
    meta = store.get_metadata("deep_fm", "1.0.0")
    assert meta["stage"] == ModelStage.STAGING


def test_promote_to_production_archives_previous(store, dummy_model_file, tmp_path):
    f2 = tmp_path / "m2.bin"
    f2.write_bytes(b"v2 weights " * 50)
    store.register("deep_fm", "1.0.0", dummy_model_file)
    store.promote("deep_fm", "1.0.0", ModelStage.PRODUCTION)
    store.register("deep_fm", "2.0.0", str(f2))
    store.promote("deep_fm", "2.0.0", ModelStage.PRODUCTION)
    old_meta = store.get_metadata("deep_fm", "1.0.0")
    assert old_meta["stage"] == ModelStage.ARCHIVED


def test_get_production_version(store, dummy_model_file):
    store.register("deep_fm", "1.0.0", dummy_model_file)
    store.promote("deep_fm", "1.0.0", ModelStage.PRODUCTION)
    assert store.get_production_version("deep_fm") == "1.0.0"


def test_delete_non_production(store, dummy_model_file):
    store.register("deep_fm", "1.0.0", dummy_model_file)
    store.delete_version("deep_fm", "1.0.0")
    with pytest.raises(FileNotFoundError):
        store.get_metadata("deep_fm", "1.0.0")


def test_cannot_delete_production(store, dummy_model_file):
    store.register("deep_fm", "1.0.0", dummy_model_file)
    store.promote("deep_fm", "1.0.0", ModelStage.PRODUCTION)
    with pytest.raises(ValueError, match="PRODUCTION"):
        store.delete_version("deep_fm", "1.0.0")


def test_list_models(store, dummy_model_file):
    store.register("deep_fm", "1.0.0", dummy_model_file)
    store.register("survival_analysis", "1.0.0", dummy_model_file)
    models = store.list_models()
    assert "deep_fm" in models
    assert "survival_analysis" in models
