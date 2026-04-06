import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from compliance.phi_audit_logger import PHIAuditLogger
from fastapi import FastAPI, HTTPException
from model_factory.base_model import BaseModel as MLBaseModel
from model_factory.model_registry import ModelRegistry
from pydantic import BaseModel, Field
from utils.fhir_connector import FHIRConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nexora Clinical API",
    description="API for clinical prediction and decision support",
    version="1.0.0",
)

# Singletons initialized once at startup, not per-request
_audit_db_path = os.environ.get("AUDIT_DB_PATH", "audit/phi_access.db")
_audit_db_dir = os.path.dirname(_audit_db_path)
if _audit_db_dir:
    os.makedirs(_audit_db_dir, exist_ok=True)

audit_logger = PHIAuditLogger(db_path=_audit_db_path)
model_registry = ModelRegistry()


class PatientData(BaseModel):
    patient_id: str
    demographics: Dict[str, Any]
    clinical_events: List[Dict[str, Any]]
    lab_results: Optional[List[Dict[str, Any]]] = None
    medications: Optional[List[Dict[str, Any]]] = None


class PredictionRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to use for prediction")
    model_version: Optional[str] = Field(
        None, description="Version of the model to use"
    )
    patient_data: PatientData
    request_id: Optional[str] = None


class PredictionResponse(BaseModel):
    request_id: str
    model_name: str
    model_version: str
    timestamp: str
    predictions: Dict[str, Any]
    explanations: Optional[Dict[str, Any]] = None
    uncertainty: Optional[Dict[str, Any]] = None


@app.middleware("http")
async def log_requests(request, call_next):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response {request_id}: {response.status_code}")
    return response


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/models")
async def list_models():
    models = model_registry.list_models()
    return {"models": models}


@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        if not request.request_id:
            request.request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        model_version = request.model_version or "latest"

        audit_logger.log_prediction_request(
            patient_id=request.patient_data.patient_id,
            model_used=f"{request.model_name} v{model_version}",
        )

        model: MLBaseModel = model_registry.get_model(
            request.model_name, request.model_version
        )

        predictions = model.predict(request.patient_data.model_dump())
        explanations = model.explain(request.patient_data.model_dump())

        return PredictionResponse(
            request_id=request.request_id,
            model_name=request.model_name,
            model_version=model_version,
            timestamp=datetime.now().isoformat(),
            predictions=predictions,
            explanations=explanations,
            uncertainty=predictions.get(
                "uncertainty", {"confidence_interval": [0.65, 0.85]}
            ),
        )

    except Exception as e:
        logger.error(f"Error processing prediction request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fhir/patient/{patient_id}/predict")
async def predict_from_fhir(
    patient_id: str, model_name: str, model_version: Optional[str] = None
):
    try:
        fhir_server_url = os.environ.get(
            "FHIR_SERVER_URL", "http://mock-fhir-server/R4"
        )

        fhir_connector = FHIRConnector(base_url=fhir_server_url)
        patient_data_dict = fhir_connector.get_patient_data(patient_id)

        patient_data = PatientData(**patient_data_dict)

        request = PredictionRequest(
            model_name=model_name,
            model_version=model_version,
            patient_data=patient_data,
        )

        return await predict(request)

    except Exception as e:
        logger.error(f"Error processing FHIR prediction request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics")
async def get_metrics():
    """Returns basic system and model serving metrics."""
    from monitoring.clinical_metrics import ClinicalMetrics

    metrics = ClinicalMetrics()
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "cohort_metrics": metrics.calculate_cohort_metrics("global"),
    }


@app.get("/audit/patient/{patient_id}")
async def get_patient_audit_history(patient_id: str):
    """Returns PHI access history for a specific patient."""
    try:
        df = audit_logger.get_patient_access_history(patient_id)
        return {
            "patient_id": patient_id,
            "access_history": df.to_dict(orient="records"),
        }
    except Exception as e:
        logger.error(f"Error fetching audit history for {patient_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port, reload=False)
