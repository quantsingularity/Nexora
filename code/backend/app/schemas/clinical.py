"""
Pydantic v2 schemas shared across the Nexora backend API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class PatientData(BaseModel):
    patient_id: str
    demographics: Dict[str, Any] = Field(default_factory=dict)
    clinical_events: List[Dict[str, Any]] = Field(default_factory=list)
    lab_results: Optional[List[Dict[str, Any]]] = None
    medications: Optional[List[Dict[str, Any]]] = None


class PredictionRequest(BaseModel):
    model_name: str = Field(..., description="Name of the model to use")
    model_version: Optional[str] = Field(None, description="Version (default: latest)")
    patient_data: PatientData
    request_id: Optional[str] = None


class BatchPredictionRequest(BaseModel):
    model_name: str
    model_version: Optional[str] = None
    patients: List[PatientData]


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class PredictionResponse(BaseModel):
    request_id: str
    model_name: str
    model_version: str
    timestamp: str
    predictions: Dict[str, Any]
    explanations: Optional[Dict[str, Any]] = None
    uncertainty: Optional[Dict[str, Any]] = None


class BatchPredictionResponse(BaseModel):
    model_name: str
    model_version: str
    timestamp: str
    results: List[Dict[str, Any]]
    total: int


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
