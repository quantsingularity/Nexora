import os
import sys
from datetime import datetime

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)

import pytest
from ml_core.monitoring.adverse_event_reporting import AdverseEventReporter


@pytest.fixture
def reporter():
    return AdverseEventReporter()


def test_report_event_returns_id(reporter):
    event_id = reporter.report_event(
        patient_id="12345",
        event_details={
            "type": "readmission",
            "severity": "severe",
            "model_prediction": 0.85,
        },
    )
    assert event_id is not None
    assert isinstance(event_id, str)
    assert len(event_id) > 0


def test_report_event_stores_in_log(reporter):
    reporter.report_event(
        patient_id="67890",
        event_details={"type": "adverse_drug_reaction", "severity": "moderate"},
    )
    events = reporter.event_log
    assert len(events) == 1
    assert events[0]["patient_id"] == "67890"
    assert events[0]["status"] == "Reported"


def test_report_event_has_timestamp(reporter):
    reporter.report_event(
        patient_id="11111",
        event_details={"type": "fall", "severity": "mild"},
    )
    event = reporter.event_log[0]
    assert "timestamp" in event
    # Should parse as a valid ISO datetime
    datetime.fromisoformat(event["timestamp"])


def test_get_recent_events_default_limit(reporter):
    for i in range(15):
        reporter.report_event(
            patient_id=f"P{i:03d}",
            event_details={"type": "readmission", "index": i},
        )
    recent = reporter.get_recent_events()
    assert len(recent) == 10


def test_get_recent_events_custom_limit(reporter):
    for i in range(8):
        reporter.report_event(
            patient_id=f"P{i:03d}",
            event_details={"type": "readmission"},
        )
    recent = reporter.get_recent_events(limit=5)
    assert len(recent) == 5


def test_get_recent_events_returns_latest(reporter):
    for i in range(5):
        reporter.report_event(
            patient_id=f"P{i:03d}",
            event_details={"type": "event", "index": i},
        )
    recent = reporter.get_recent_events(limit=2)
    # Should be the last two events
    assert recent[-1]["patient_id"] == "P004"
    assert recent[0]["patient_id"] == "P003"


def test_event_id_is_unique(reporter):
    ids = set()
    for i in range(10):
        event_id = reporter.report_event(
            patient_id=f"P{i:03d}",
            event_details={"type": "readmission"},
        )
        ids.add(event_id)
    assert len(ids) == 10


def test_event_details_preserved(reporter):
    reporter.report_event(
        patient_id="DETAIL_PAT",
        event_details={
            "type": "medication_error",
            "severity": "critical",
            "model_prediction": 0.92,
            "notes": "Overdose detected",
        },
    )
    event = reporter.event_log[0]
    assert event["type"] == "medication_error"
    assert event["severity"] == "critical"
    assert event["model_prediction"] == 0.92
    assert event["notes"] == "Overdose detected"


def test_multiple_patients(reporter):
    reporter.report_event("P001", {"type": "readmission"})
    reporter.report_event("P002", {"type": "adverse_drug_reaction"})
    reporter.report_event("P001", {"type": "fall"})
    assert len(reporter.event_log) == 3
    p001_events = [e for e in reporter.event_log if e["patient_id"] == "P001"]
    assert len(p001_events) == 2


def test_get_recent_events_empty(reporter):
    recent = reporter.get_recent_events()
    assert recent == []
