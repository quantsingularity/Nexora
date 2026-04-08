import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field

    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    uvicorn = None  # type: ignore
    HTTPException = Exception  # type: ignore
    Field = lambda *a, **kw: None  # type: ignore

from compliance.phi_audit_logger import PHIAuditLogger
from model_factory.base_model import BaseModel as MLBaseModel
from model_factory.model_registry import ModelRegistry
from utils.fhir_connector import FHIRConnector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if _FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Nexora Clinical API",
        description="API for clinical prediction and decision support",
        version="2.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _audit_db_path = os.environ.get("AUDIT_DB_PATH", "audit/phi_access.db")
    _audit_db_dir = os.path.dirname(_audit_db_path)
    if _audit_db_dir:
        os.makedirs(_audit_db_dir, exist_ok=True)

    audit_logger = PHIAuditLogger(db_path=_audit_db_path)
    model_registry = ModelRegistry()

    # ------------------------------------------------------------------ schemas
    class PatientData(BaseModel):
        patient_id: str
        demographics: Dict[str, Any]
        clinical_events: List[Dict[str, Any]]
        lab_results: Optional[List[Dict[str, Any]]] = None
        medications: Optional[List[Dict[str, Any]]] = None

    class PredictionRequest(BaseModel):
        model_name: str = Field(..., description="Name of the model to use")
        model_version: Optional[str] = Field(
            None, description="Version (default: latest)"
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

    class HealthResponse(BaseModel):
        status: str
        timestamp: str
        version: str

    # ------------------------------------------------------------------ middleware
    @app.middleware("http")
    async def log_requests(request, call_next):
        request_id = request.headers.get("X-Request-ID", "unknown")
        logger.info(f"Request {request_id}: {request.method} {request.url}")
        response = await call_next(request)
        logger.info(f"Response {request_id}: {response.status_code}")
        return response

    # ------------------------------------------------------------------ routes
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
        )

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
                request.model_name, model_version
            )
            patient_dict = request.patient_data.model_dump()
            predictions = model.predict(patient_dict)
            explanations = model.explain(patient_dict)

            uncertainty = predictions.pop(
                "uncertainty", {"confidence_interval": [0.65, 0.85]}
            )

            return PredictionResponse(
                request_id=request.request_id,
                model_name=request.model_name,
                model_version=model_version,
                timestamp=datetime.now().isoformat(),
                predictions=predictions,
                explanations=explanations,
                uncertainty=uncertainty,
            )

        except (ValueError, NotImplementedError) as e:
            logger.error(f"Prediction error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/fhir/patient/{patient_id}/predict")
    async def predict_from_fhir(
        patient_id: str,
        model_name: str = Query(...),
        model_version: Optional[str] = Query(None),
    ):
        try:
            fhir_server_url = os.environ.get(
                "FHIR_SERVER_URL", "http://mock-fhir-server/R4"
            )
            fhir_connector = FHIRConnector(base_url=fhir_server_url)
            patient_data_dict = fhir_connector.get_patient_data(patient_id)
            patient_data = PatientData(**patient_data_dict)
            req = PredictionRequest(
                model_name=model_name,
                model_version=model_version,
                patient_data=patient_data,
            )
            return await predict(req)
        except Exception as e:
            logger.error(f"FHIR prediction error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/metrics")
    async def get_metrics():
        from monitoring.clinical_metrics import ClinicalMetrics

        metrics = ClinicalMetrics()
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "cohort_metrics": metrics.calculate_cohort_metrics("global"),
        }

    @app.get("/audit/patient/{patient_id}")
    async def get_patient_audit_history(patient_id: str):
        try:
            df = audit_logger.get_patient_access_history(patient_id)
            return {
                "patient_id": patient_id,
                "access_history": df.to_dict(orient="records"),
            }
        except Exception as e:
            logger.error(f"Audit history error for {patient_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/models/{model_name}/{version}")
    async def delete_model(model_name: str, version: str):
        try:
            model_registry.delete_model(model_name, version)
            return {"status": "deleted", "model_name": model_name, "version": version}
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))

    if __name__ == "__main__":
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        uvicorn.run(app, host=host, port=port, reload=False)

else:
    logger.warning("FastAPI not available; rest_api endpoints are not active.")
    app = None  # type: ignore
    audit_logger = None  # type: ignore
    model_registry = None  # type: ignore
