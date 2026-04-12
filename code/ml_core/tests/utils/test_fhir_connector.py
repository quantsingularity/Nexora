"""Tests for FHIRConnector (offline - no live server required)."""

import os
import sys

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import pytest
from ml_core.utils.fhir_connector import FHIRConnector


def test_fhir_connector_init():
    c = FHIRConnector(base_url="http://test-fhir-server")
    assert "test-fhir-server" in c.base_url


def test_fhir_connector_base_url_trailing_slash():
    c = FHIRConnector(base_url="http://test-fhir-server")
    assert c.base_url.endswith("/")


def test_fhir_connector_get_patient_data_raises_on_unreachable():
    c = FHIRConnector(
        base_url="http://localhost:19999", timeout=1, max_retries=1, retry_delay=0
    )
    with pytest.raises(Exception):
        c.get_patient_data("P001")
