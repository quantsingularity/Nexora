from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AdverseEvent(BaseModel):
    patient_id: str
    event_date: date
    event_type: str
    suspected_cause: str
    severity: str
    model_prediction: float


@router.post("/report")
async def report_adverse_event(event: AdverseEvent):
    # Validate patient ID format
    if not validate_mrn_format(event.patient_id):
        raise HTTPException(400, "Invalid patient ID")

    # Store in AE database
    with DatabaseConnection("adverse_events") as conn:
        conn.execute(
            """
            INSERT INTO adverse_events VALUES (
                ?, ?, ?, ?, ?, ?
            )""",
            (
                event.patient_id,
                event.event_date.isoformat(),
                event.event_type,
                event.suspected_cause,
                event.severity,
                event.model_prediction,
            ),
        )

    # Trigger model review if needed
    if event.severity in ["severe", "fatal"]:
        ModelReviewer().schedule_review(
            patient_id=event.patient_id, event_details=event.dict()
        )

    return {"status": "reported"}
