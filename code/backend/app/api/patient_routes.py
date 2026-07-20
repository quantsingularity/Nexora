"""
Patient management API routes.

All endpoints require a valid bearer token (see backend.app.core.security
.get_current_user). Risk scores are produced by the ml_core model registry
via PatientStore, so results are consistent with the standalone /predict
endpoint.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.app.core.config import settings
from backend.app.core.security import get_current_user
from backend.app.models.patient import PatientStore
from backend.app.schemas.patient import (
    PatientCreateRequest,
    PatientDetail,
    PatientListResponse,
    PatientUpdateRequest,
)
from ml_core.compliance.phi_audit_logger import PHIAuditLogger

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/patients", tags=["Patients"])

_audit = PHIAuditLogger(db_path=settings.AUDIT_DB_PATH)


@router.get("", response_model=PatientListResponse)
async def list_patients(
    search: Optional[str] = Query(None, description="Search by name, ID, or MRN"),
    risk_band: Optional[str] = Query(
        None, description="Filter by risk band: high, medium, low, or all"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PatientListResponse:
    store = PatientStore()
    items, total = store.list(
        search=search, risk_band=risk_band, page=page, page_size=page_size
    )
    return PatientListResponse(
        patients=items, total=total, page=page, page_size=page_size
    )


@router.post("", response_model=PatientDetail, status_code=status.HTTP_201_CREATED)
async def create_patient(
    payload: PatientCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PatientDetail:
    store = PatientStore()
    patient = store.create(payload.model_dump(), created_by=current_user["id"])
    _audit.log_access(
        user_id=current_user["email"],
        patient_id=patient["id"],
        resource_type="Patient",
        operation="CREATE",
        justification="Clinical intake",
    )
    return PatientDetail(**patient)


@router.get("/{patient_id}", response_model=PatientDetail)
async def get_patient(
    patient_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
) -> PatientDetail:
    store = PatientStore()
    patient = store.get(patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    _audit.log_access(
        user_id=current_user["email"],
        patient_id=patient_id,
        resource_type="Patient",
        operation="READ",
        justification="Clinical review",
    )
    return PatientDetail(**patient)


@router.put("/{patient_id}", response_model=PatientDetail)
async def update_patient(
    patient_id: str,
    payload: PatientUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> PatientDetail:
    store = PatientStore()
    updated = store.update(
        patient_id, {k: v for k, v in payload.model_dump().items() if v is not None}
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    _audit.log_access(
        user_id=current_user["email"],
        patient_id=patient_id,
        resource_type="Patient",
        operation="UPDATE",
        justification="Chart correction",
    )
    return PatientDetail(**updated)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    store = PatientStore()
    if not store.delete(patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    _audit.log_access(
        user_id=current_user["email"],
        patient_id=patient_id,
        resource_type="Patient",
        operation="DELETE",
        justification="Record removal",
    )
    return {"status": "deleted", "id": patient_id}


@router.post("/{patient_id}/recompute-risk", response_model=PatientDetail)
async def recompute_patient_risk(
    patient_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
) -> PatientDetail:
    store = PatientStore()
    updated = store.recompute_risk(patient_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    _audit.log_access(
        user_id=current_user["email"],
        patient_id=patient_id,
        resource_type="Patient",
        operation="READ",
        justification="Risk re-assessment",
        model="deep_fm v1.0.0",
    )
    return PatientDetail(**updated)
