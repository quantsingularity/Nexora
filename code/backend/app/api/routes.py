"""
FastAPI router with all Nexora endpoints.
Imported by rest_api.py to keep route definitions separate from app setup.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.core.config import settings
from backend.app.schemas.clinical import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
)
from ml_core.compliance.phi_audit_logger import PHIAuditLogger
from ml_core.models.model_registry import ModelRegistry
from ml_core.monitoring.clinical_metrics import ClinicalMetrics
from ml_core.utils.fhir_connector import FHIRConnector

logger = logging.getLogger(__name__)
router = APIRouter()

# Shared singletons (initialised once on import)
os.makedirs(
    (
        os.path.dirname(settings.AUDIT_DB_PATH)
        if os.path.dirname(settings.AUDIT_DB_PATH)
        else "."
    ),
    exist_ok=True,
)
_audit = PHIAuditLogger(db_path=settings.AUDIT_DB_PATH)
_registry = ModelRegistry()


# ── Health ────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version=settings.APP_VERSION,
    )


# ── Models ────────────────────────────────────────────────────────────────


@router.get("/models", tags=["Models"])
async def list_models():
    return {"models": _registry.list_models()}


@router.delete("/models/{model_name}/{version}", tags=["Models"])
async def delete_model(model_name: str, version: str):
    try:
        _registry.delete_model(model_name, version)
        return {"status": "deleted", "model_name": model_name, "version": version}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Prediction ────────────────────────────────────────────────────────────


@router.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
async def predict(request: PredictionRequest) -> PredictionResponse:
    if not request.request_id:
        request.request_id = (
            f"req_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        )

    model_version = request.model_version or "latest"

    _audit.log_prediction_request(
        patient_id=request.patient_data.patient_id,
        model_used=f"{request.model_name} v{model_version}",
    )

    try:
        model = _registry.get_model(request.model_name, model_version)
        patient_dict = request.patient_data.model_dump()
        predictions = model.predict(patient_dict)
        explanations = model.explain(patient_dict)
        uncertainty = predictions.pop(
            "uncertainty", {"confidence_interval": [0.65, 0.85]}
        )
    except Exception as e:
        # Unknown model, runtime error, or any unexpected failure → 500
        logger.error(
            f"Prediction error for model '{request.model_name}': {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Internal prediction error")

    return PredictionResponse(
        request_id=request.request_id,
        model_name=request.model_name,
        model_version=model_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        predictions=predictions,
        explanations=explanations,
        uncertainty=uncertainty,
    )


@router.post(
    "/predict/batch", response_model=BatchPredictionResponse, tags=["Prediction"]
)
async def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    model_version = request.model_version or "latest"
    try:
        model = _registry.get_model(request.model_name, model_version)
    except Exception as e:
        logger.error(f"Batch predict model load error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal prediction error")

    results = []
    for patient in request.patients:
        _audit.log_prediction_request(
            patient_id=patient.patient_id,
            model_used=f"{request.model_name} v{model_version}",
        )
        try:
            preds = model.predict(patient.model_dump())
            preds.pop("uncertainty", None)
            results.append({"patient_id": patient.patient_id, "status": "ok", **preds})
        except Exception as e:
            results.append(
                {"patient_id": patient.patient_id, "status": "error", "detail": str(e)}
            )

    return BatchPredictionResponse(
        model_name=request.model_name,
        model_version=model_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        results=results,
        total=len(results),
    )


# ── FHIR ─────────────────────────────────────────────────────────────────


@router.post("/fhir/patient/{patient_id}/predict", tags=["FHIR"])
async def predict_from_fhir(
    patient_id: str,
    model_name: str = Query(...),
    model_version: Optional[str] = Query(None),
):
    try:
        fhir = FHIRConnector(base_url=settings.FHIR_SERVER_URL)
        patient_data_dict = fhir.get_patient_data(patient_id)
        from backend.app.schemas.clinical import PatientData

        patient_data = PatientData(**patient_data_dict)
        req = PredictionRequest(
            model_name=model_name,
            model_version=model_version,
            patient_data=patient_data,
        )
        return await predict(req)
    except HTTPException:
        raise  # re-raise HTTP exceptions as-is
    except Exception as e:
        logger.error(f"FHIR prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ── Metrics ───────────────────────────────────────────────────────────────


@router.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    metrics = ClinicalMetrics()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cohort_metrics": metrics.calculate_cohort_metrics("global"),
    }


# ── Audit ─────────────────────────────────────────────────────────────────


@router.get("/audit/patient/{patient_id}", tags=["Compliance"])
async def get_patient_audit_history(patient_id: str):
    try:
        df = _audit.get_patient_access_history(patient_id)
        return {
            "patient_id": patient_id,
            "access_history": df.to_dict(orient="records"),
        }
    except Exception as e:
        logger.error(f"Audit history error for {patient_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
