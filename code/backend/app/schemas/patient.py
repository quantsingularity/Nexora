"""
Pydantic v2 schemas for patient management endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PatientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=160)
    age: Optional[int] = Field(None, ge=0, le=130)
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    mrn: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class PatientUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=160)
    age: Optional[int] = Field(None, ge=0, le=130)
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    mrn: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None


class PatientSummary(BaseModel):
    id: str
    mrn: Optional[str] = None
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    diagnosis: Optional[str] = None
    riskScore: Optional[float] = None
    riskBand: Optional[str] = None
    lengthOfStay: Optional[float] = None
    lastVisit: Optional[str] = None


class PatientListResponse(BaseModel):
    patients: List[PatientSummary]
    total: int
    page: int
    page_size: int


class PatientDetail(PatientSummary):
    dob: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    primaryDiagnosis: Optional[str] = None
    labResults: List[Dict[str, Any]] = Field(default_factory=list)
    diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    medications: List[Dict[str, Any]] = Field(default_factory=list)
    riskFactors: List[Dict[str, Any]] = Field(default_factory=list)
    interventions: List[Dict[str, Any]] = Field(default_factory=list)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
