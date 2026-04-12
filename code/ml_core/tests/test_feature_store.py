"""Tests for ml_core.feature_store"""

import pytest
from ml_core.feature_store import FeatureStore


@pytest.fixture
def store(tmp_path):
    return FeatureStore(base_path=str(tmp_path / "fs"))


def test_upsert_and_get(store):
    store.upsert("P001", {"age": 65, "creatinine": 1.2})
    row = store.get("P001")
    assert row is not None
    assert row["age"] == 65


def test_get_missing_patient(store):
    assert store.get("UNKNOWN") is None


def test_upsert_overwrites(store):
    store.upsert("P001", {"age": 65})
    store.clear_cache()
    store.upsert("P001", {"age": 70})
    store.clear_cache()
    row = store.get("P001")
    assert row["age"] == 70


def test_get_batch(store):
    store.upsert("P001", {"age": 65})
    store.upsert("P002", {"age": 72})
    df = store.get_batch(["P001", "P002"])
    assert len(df) == 2


def test_list_patients(store):
    store.upsert("P001", {"x": 1})
    store.upsert("P002", {"x": 2})
    patients = store.list_patients()
    assert "P001" in patients
    assert "P002" in patients


def test_delete_patient(store):
    store.upsert("P001", {"age": 65})
    store.delete_patient("P001")
    store.clear_cache()
    assert store.get("P001") is None


def test_stats(store):
    store.upsert("P001", {"a": 1, "b": 2})
    stats = store.stats()
    assert stats["n_patients"] == 1
    assert stats["n_rows"] == 1


def test_upsert_batch(store):
    records = [{"patient_id": f"P{i:03d}", "age": 50 + i} for i in range(5)]
    store.upsert_batch(records)
    assert len(store.list_patients()) == 5
