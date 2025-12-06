import logging
from typing import Dict, Any, List
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class AdverseEventReporter:
    """
    Handles the reporting and logging of adverse events detected by the system
    or reported by clinicians.
    """

    def __init__(self) -> Any:
        self.event_log = []
        logger.info("AdverseEventReporter initialized.")

    def report_event(self, patient_id: str, event_details: Dict[str, Any]) -> str:
        """
        Logs a new adverse event.

        Args:
            patient_id: The ID of the patient involved.
            event_details: Dictionary containing details of the event.

        Returns:
            The unique ID of the reported event.
        """
        event_id = str(uuid.uuid4())
        event_record = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "patient_id": patient_id,
            "status": "Reported",
            **event_details,
        }
        self.event_log.append(event_record)
        logger.warning(
            f"Adverse event reported for patient {patient_id}: {event_details.get('type', 'Unknown Event')}. ID: {event_id}"
        )
        self._trigger_alert(event_record)
        return event_id

    def _trigger_alert(self, event_record: Dict[str, Any]) -> Any:
        """Mock function to simulate triggering an external alert."""
        logger.info(
            f"ALERT: New adverse event {event_record['event_id']} requires immediate review."
        )

    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent adverse events.
        """
        return self.event_log[-limit:]
