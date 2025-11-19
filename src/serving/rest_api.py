import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ..compliance.phi_audit_logger import PHIAuditLogger
# Import model registry and other utilities
# These would need to be implemented or imported from other modules
from ..model_factory.model_registry import ModelRegistry
from ..utils.fhir_connector import FHIRConnector

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nexora Clinical API",
    description="API for clinical prediction and decision support",
    version="1.0.0",
)


# Define data models
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


# Middleware for request logging
@app.middleware("http")
async def log_requests(request, call_next):
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.info(f"Request {request_id}: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response {request_id}: {response.status_code}")
    return response


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Model information endpoint
@app.get("/models")
async def list_models():
    models = ModelRegistry().list_models()
    return {"models": models}


# Prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        PHIAuditLogger().log_prediction_request(request.patient_id)

        if not request.request_id:
            request.request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        model = ModelRegistry().get_model(request.model_name, request.model_version)
        predictions = model.predict(request.patient_data)
        explanations = model.explain(request.patient_data)

        return PredictionResponse(
            request_id=request.request_id,
            model_name=request.model_name,
            model_version=request.model_version or "latest",
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


# FHIR integration endpoint
@app.post("/fhir/patient/{patient_id}/predict")
async def predict_from_fhir(
    patient_id: str, model_name: str, model_version: Optional[str] = None
):
    try:
        fhir_connector = FHIRConnector()
        patient_data = fhir_connector.get_patient_data(patient_id)

        request = PredictionRequest(
            model_name=model_name,
            model_version=model_version,
            patient_data=patient_data,
        )

        return await predict(request)

    except Exception as e:
        logger.error(f"Error processing FHIR prediction request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Run the API server
if __name__ == "__main__":
    uvicorn.run("rest_api:app", host="0.0.0.0", port=8000, reload=True)
