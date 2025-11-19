from datetime import date

import pytest

from src.monitoring.adverse_event_reporting import (AdverseEvent,
                                                    report_adverse_event)
from src.monitoring.model_reviewer import ModelReviewer


@pytest.fixture
def sample_adverse_event():
    return AdverseEvent(
        patient_id="12345",
        event_date=date(2023, 1, 1),
        event_type="readmission",
        suspected_cause="model_prediction",
        severity="severe",
        model_prediction=0.85,
    )


def test_adverse_event_validation():
    # Test valid event
    event = AdverseEvent(
        patient_id="12345",
        event_date=date(2023, 1, 1),
        event_type="readmission",
        suspected_cause="model_prediction",
        severity="severe",
        model_prediction=0.85,
    )
    assert event.patient_id == "12345"
    assert event.severity == "severe"

    # Test invalid severity
    with pytest.raises(ValueError):
        AdverseEvent(
            patient_id="12345",
            event_date=date(2023, 1, 1),
            event_type="readmission",
            suspected_cause="model_prediction",
            severity="invalid",
            model_prediction=0.85,
        )


def test_adverse_event_reporting(sample_adverse_event):
    response = report_adverse_event(sample_adverse_event)
    assert response["status"] == "reported"

    # Verify event was stored in database
    with DatabaseConnection("adverse_events") as conn:
        cursor = conn.execute(
            "SELECT * FROM adverse_events WHERE patient_id = ?",
            (sample_adverse_event.patient_id,),
        )
        stored_event = cursor.fetchone()
        assert stored_event is not None
        assert stored_event["event_type"] == "readmission"
        assert stored_event["severity"] == "severe"


def test_model_review_triggering(sample_adverse_event):
    # Test that severe events trigger model review
    reviewer = ModelReviewer()
    review_scheduled = reviewer.schedule_review(
        patient_id=sample_adverse_event.patient_id,
        event_details=sample_adverse_event.dict(),
    )
    assert review_scheduled is True

    # Verify review was scheduled
    with DatabaseConnection("model_reviews") as conn:
        cursor = conn.execute(
            "SELECT * FROM scheduled_reviews WHERE patient_id = ?",
            (sample_adverse_event.patient_id,),
        )
        review = cursor.fetchone()
        assert review is not None
        assert review["status"] == "scheduled"


def test_adverse_event_statistics():
    # Test aggregation of adverse events
    with DatabaseConnection("adverse_events") as conn:
        stats = conn.execute(
            """
            SELECT
                event_type,
                severity,
                COUNT(*) as count
            FROM adverse_events
            GROUP BY event_type, severity
        """
        ).fetchall()

        assert len(stats) > 0
        for stat in stats:
            assert "event_type" in stat
            assert "severity" in stat
            assert "count" in stat
            assert stat["count"] > 0


def test_adverse_event_trends():
    # Test trend analysis of adverse events
    with DatabaseConnection("adverse_events") as conn:
        trends = conn.execute(
            """
            SELECT
                DATE_TRUNC('month', event_date) as month,
                COUNT(*) as count
            FROM adverse_events
            GROUP BY month
            ORDER BY month
        """
        ).fetchall()

        assert len(trends) > 0
        for trend in trends:
            assert "month" in trend
            assert "count" in trend
            assert trend["count"] > 0


def test_adverse_event_correlation():
    # Test correlation between model predictions and adverse events
    with DatabaseConnection("adverse_events") as conn:
        correlations = conn.execute(
            """
            SELECT
                AVG(model_prediction) as avg_prediction,
                COUNT(*) as event_count
            FROM adverse_events
            GROUP BY severity
        """
        ).fetchall()

        assert len(correlations) > 0
        for corr in correlations:
            assert "avg_prediction" in corr
            assert "event_count" in corr
            assert 0 <= corr["avg_prediction"] <= 1
            assert corr["event_count"] > 0
