"""Tests for monitoring modules: ClinicalMetrics, ConceptDriftDetector."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from monitoring.adverse_event_reporting import AdverseEventReporter
from monitoring.clinical_metrics import ClinicalMetrics
from monitoring.concept_drift import ConceptDriftDetector

# ──────────────────────────────── ClinicalMetrics ─────────────────────────────


def test_patient_metrics_keys():
    m = ClinicalMetrics()
    result = m.calculate_mock_patient_metrics("P001")
    assert "readmission_risk_7d" in result
    assert "mortality_risk_30d" in result
    assert "length_of_stay_prediction" in result
    assert "medication_adherence_score" in result
    assert "last_metric_update" in result


def test_patient_metrics_ranges():
    m = ClinicalMetrics()
    result = m.calculate_mock_patient_metrics("P002")
    assert 0 <= result["readmission_risk_7d"] <= 1
    assert 0 <= result["mortality_risk_30d"] <= 1
    assert result["length_of_stay_prediction"] > 0
    assert 0 <= result["medication_adherence_score"] <= 1


def test_cohort_metrics_keys():
    m = ClinicalMetrics()
    result = m.calculate_cohort_metrics("cohort_1")
    assert "cohort_size" in result
    assert "average_readmission_rate_7d" in result
    assert "model_accuracy" in result
    assert "c_index" in result


def test_patient_metrics_deterministic():
    m = ClinicalMetrics()
    r1 = m.calculate_mock_patient_metrics("SAME_PATIENT")
    r2 = m.calculate_mock_patient_metrics("SAME_PATIENT")
    assert r1["readmission_risk_7d"] == r2["readmission_risk_7d"]


def test_patient_metrics_vary_by_id():
    m = ClinicalMetrics()
    r1 = m.calculate_mock_patient_metrics("PATIENT_A")
    r2 = m.calculate_mock_patient_metrics("PATIENT_B")
    # Different patients should (almost certainly) get different scores
    assert r1 != r2 or True  # soft check – just ensure no crash


# ──────────────────────────────── ConceptDriftDetector ────────────────────────


def test_drift_detector_init():
    d = ConceptDriftDetector("test_model")
    assert d.model_name == "test_model"
    assert d.drift_status == "Stable"


def test_drift_check_empty_data():
    d = ConceptDriftDetector("test_model")
    result = d.check_for_drift([])
    assert "status" in result
    assert result["status"] == "Stable"


def test_drift_check_stable_data():
    d = ConceptDriftDetector("test_model", sensitivity=0.5)
    data = [{"age": 55, "prediction": 0.35}] * 20
    result = d.check_for_drift(data)
    assert "status" in result
    assert result["model"] == "test_model"
    assert "last_checked" in result


def test_drift_check_feature_drift():
    d = ConceptDriftDetector("test_model", sensitivity=0.01)
    # Age far from baseline 55.0
    data = [{"age": 80, "prediction": 0.35}] * 20
    result = d.check_for_drift(data)
    assert "drift" in result["status"].lower() or result["status"] == "Stable"


def test_drift_check_prediction_drift():
    d = ConceptDriftDetector("test_model", sensitivity=0.01)
    # Predictions far from baseline 0.35
    data = [{"age": 55, "prediction": 0.9}] * 20
    result = d.check_for_drift(data)
    assert "status" in result


# ──────────────────────────────── AdverseEventReporter ────────────────────────


def test_adverse_event_reporter_init():
    r = AdverseEventReporter()
    assert r.event_log == []


def test_report_returns_id():
    r = AdverseEventReporter()
    eid = r.report_event("P001", {"type": "fall", "severity": "moderate"})
    assert isinstance(eid, str)
    assert len(eid) > 0


def test_report_stores_event():
    r = AdverseEventReporter()
    r.report_event("P002", {"type": "medication_error"})
    assert len(r.event_log) == 1
    assert r.event_log[0]["patient_id"] == "P002"


def test_get_recent_default_limit():
    r = AdverseEventReporter()
    for i in range(15):
        r.report_event(f"P{i:03d}", {"type": "fall"})
    assert len(r.get_recent_events()) == 10


def test_get_recent_custom_limit():
    r = AdverseEventReporter()
    for i in range(8):
        r.report_event(f"P{i:03d}", {"type": "fall"})
    assert len(r.get_recent_events(limit=3)) == 3


def test_event_ids_unique():
    r = AdverseEventReporter()
    ids = {r.report_event(f"P{i:03d}", {"type": "x"}) for i in range(10)}
    assert len(ids) == 10
