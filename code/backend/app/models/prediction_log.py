"""
In-memory and SQLite-backed prediction log model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class PredictionLog:
    """Represents a single prediction event stored for auditing and analytics."""

    request_id: str
    patient_id: str
    model_name: str
    model_version: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    risk_score: Optional[float] = None
    predictions: Dict[str, Any] = field(default_factory=dict)
    user_id: str = "API_USER"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "patient_id": self.patient_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "timestamp": self.timestamp,
            "risk_score": self.risk_score,
            "predictions": self.predictions,
            "user_id": self.user_id,
        }
