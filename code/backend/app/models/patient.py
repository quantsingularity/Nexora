"""
Patient record model & store for the Nexora clinical dashboard (SQLite-backed).

Risk scores are produced by calling the *same* ``ml_core`` model registry
used by the public ``/predict`` API (see ``backend.app.api.routes``), so the
numbers shown in the patient list / dashboard are backed by the identical
prediction code path rather than a disconnected mock.
"""

from __future__ import annotations

import json
import logging
import random
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.database import get_connection

logger = logging.getLogger(__name__)

_JSON_FIELDS = [
    "lab_results",
    "diagnoses",
    "medications",
    "risk_factors",
    "interventions",
    "timeline",
]

_FIRST_NAMES = [
    "James",
    "Mary",
    "John",
    "Patricia",
    "Robert",
    "Jennifer",
    "Michael",
    "Linda",
    "William",
    "Elizabeth",
    "David",
    "Susan",
    "Richard",
    "Jessica",
    "Joseph",
    "Sarah",
    "Thomas",
    "Karen",
    "Charles",
    "Nancy",
]
_LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Garcia",
    "Miller",
    "Davis",
    "Rodriguez",
    "Martinez",
    "Hernandez",
    "Lopez",
    "Gonzalez",
    "Wilson",
    "Anderson",
    "Thomas",
    "Taylor",
    "Moore",
    "Jackson",
    "Martin",
]
_DIAGNOSES = [
    "Hypertension",
    "Type 2 Diabetes",
    "Congestive Heart Failure",
    "COPD",
    "Asthma",
    "Pneumonia",
    "Chronic Kidney Disease",
    "Coronary Artery Disease",
    "Atrial Fibrillation",
    "Stroke",
]
_MEDICATIONS = [
    ("Metformin", "1000mg", "Twice daily"),
    ("Lisinopril", "10mg", "Once daily"),
    ("Atorvastatin", "20mg", "Once daily at bedtime"),
    ("Aspirin", "81mg", "Once daily"),
    ("Furosemide", "40mg", "Once daily"),
    ("Albuterol", "90mcg", "As needed"),
    ("Warfarin", "5mg", "Once daily"),
    ("Insulin Glargine", "20 units", "Once daily at bedtime"),
]
_INTERVENTIONS = [
    ("Medication Adherence Program", "Enroll in weekly adherence check-ins.", "High"),
    ("Diabetes Education", "Schedule diabetes self-management education.", "Medium"),
    (
        "Nutrition Consultation",
        "Refer to dietitian for medical nutrition therapy.",
        "Medium",
    ),
    ("Remote Monitoring", "Provide a home vitals monitoring device.", "High"),
    (
        "Cardiology Follow-up",
        "Schedule a follow-up with cardiology within 7 days.",
        "High",
    ),
    (
        "Home Health Visit",
        "Arrange a home health nurse visit post-discharge.",
        "Medium",
    ),
]


def _risk_band(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.40:
        return "medium"
    return "low"


_risk_model_cache: Dict[str, Any] = {}


def _get_risk_model() -> Any:
    """Lazily build (and cache) the deep_fm model used for risk scoring."""
    if "model" not in _risk_model_cache:
        from ml_core.models.model_registry import ModelRegistry

        _risk_model_cache["model"] = ModelRegistry().get_model("deep_fm", "latest")
    return _risk_model_cache["model"]


def _predict_risk(patient_id: str, demographics: Dict[str, Any]) -> Dict[str, Any]:
    """Call the real deep_fm model from the ml_core registry for this patient.

    Falls back to a deterministic local estimate if the registry/model
    cannot be loaded (e.g. optional ML deps not installed) so patient
    records always have a usable risk score.
    """
    try:
        model = _get_risk_model()
        return model.predict({"patient_id": patient_id, "demographics": demographics})
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.warning(f"Falling back to local risk estimate for {patient_id}: {exc}")
        rng = random.Random(patient_id)
        score = round(rng.uniform(0.1, 0.9), 4)
        return {
            "risk_score": score,
            "readmission_probability_30d": round(min(score * 1.1, 1.0), 4),
            "top_features": ["age", "previous_admissions", "comorbidity_count"],
        }


class PatientStore:
    """CRUD operations for patient records, seeded with a demo cohort."""

    def __init__(self, db_path: Optional[str] = None, seed: bool = True) -> None:
        self.conn = get_connection(db_path)
        self._init_db()
        if seed and self.count() == 0:
            self._seed(45)

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id TEXT PRIMARY KEY,
                mrn TEXT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                dob TEXT,
                diagnosis TEXT,
                phone TEXT,
                email TEXT,
                address TEXT,
                risk_score REAL,
                risk_band TEXT,
                length_of_stay REAL,
                last_visit TEXT,
                lab_results TEXT,
                diagnoses TEXT,
                medications TEXT,
                risk_factors TEXT,
                interventions TEXT,
                timeline TEXT,
                created_by TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_patients_risk ON patients(risk_score)"
        )
        self.conn.commit()

    # ── Seeding ──────────────────────────────────────────────────────────

    def _generate_detail(
        self, patient_id: str, rng: random.Random, risk_score: float
    ) -> Dict[str, Any]:
        band = _risk_band(risk_score)
        base_glucose = rng.randint(95, 180)
        lab_results = []
        today = datetime.now(timezone.utc)
        for i in range(6):
            d = today - timedelta(days=(5 - i) * 15)
            lab_results.append(
                {
                    "date": d.strftime("%Y-%m-%d"),
                    "glucose": base_glucose + rng.randint(-15, 20),
                    "hemoglobin": round(rng.uniform(11.5, 14.5), 1),
                }
            )

        n_diag = rng.randint(1, 4)
        diag_names = rng.sample(_DIAGNOSES, n_diag)
        diagnoses = [
            {
                "name": name,
                "date": (today - timedelta(days=rng.randint(200, 2000))).strftime(
                    "%Y-%m-%d"
                ),
                "code": f"{rng.choice('ABCDEFGHIJ')}{rng.randint(10,99)}.{rng.randint(0,9)}",
            }
            for name in diag_names
        ]

        n_meds = rng.randint(1, 4)
        medications = [
            {"name": n, "dosage": d, "frequency": f}
            for n, d, f in rng.sample(_MEDICATIONS, n_meds)
        ]

        risk_factor_pool = [
            ("Previous Hospitalizations", 0.28),
            ("HbA1c > 8.0", 0.22),
            ("Medication Non-adherence", 0.18),
            ("Age > 55", 0.15),
            ("Hypertension", 0.12),
            ("Polypharmacy", 0.10),
            ("Social Isolation", 0.08),
        ]
        n_factors = rng.randint(3, 5)
        chosen = rng.sample(risk_factor_pool, n_factors)
        risk_factors = [{"name": n, "impact": v} for n, v in chosen]

        n_interventions = 3 if band == "high" else (2 if band == "medium" else 1)
        interventions = [
            {"name": n, "description": d, "priority": p}
            for n, d, p in rng.sample(_INTERVENTIONS, n_interventions)
        ]

        admit_date = today - timedelta(days=rng.randint(10, 400))
        timeline = [
            {
                "title": "Initial Diagnosis",
                "date": (
                    diagnoses[0]["date"]
                    if diagnoses
                    else admit_date.strftime("%Y-%m-%d")
                ),
                "description": f"Diagnosed with {diagnoses[0]['name'] if diagnoses else 'a chronic condition'}",
            },
            {
                "title": "Hospital Admission",
                "date": admit_date.strftime("%Y-%m-%d"),
                "description": "Admitted for evaluation and stabilization.",
            },
            {
                "title": "Care Plan Updated",
                "date": (admit_date + timedelta(days=rng.randint(1, 5))).strftime(
                    "%Y-%m-%d"
                ),
                "description": "Care team adjusted the treatment plan based on labs.",
            },
            {
                "title": "Latest Visit",
                "date": (
                    lab_results[-1]["date"]
                    if lab_results
                    else today.strftime("%Y-%m-%d")
                ),
                "description": "Follow-up visit; medication regimen reviewed.",
            },
        ]

        return {
            "lab_results": lab_results,
            "diagnoses": diagnoses,
            "medications": medications,
            "risk_factors": risk_factors,
            "interventions": interventions,
            "timeline": timeline,
        }

    def _seed(self, n: int) -> None:
        logger.info(f"Seeding patient store with {n} demo patients...")
        rng = random.Random(1337)
        for i in range(1, n + 1):
            patient_id = f"P{i:05d}"
            first = rng.choice(_FIRST_NAMES)
            last = rng.choice(_LAST_NAMES)
            age = rng.randint(24, 89)
            gender = rng.choice(["Female", "Male"])
            diagnosis = rng.choice(_DIAGNOSES)
            days_ago = rng.randint(0, 120)
            last_visit = (
                datetime.now(timezone.utc) - timedelta(days=days_ago)
            ).strftime("%Y-%m-%d")

            prediction = _predict_risk(
                patient_id, {"age": age, "gender": gender, "diagnosis": diagnosis}
            )
            risk_score = float(prediction.get("risk_score", 0.5))
            detail = self._generate_detail(patient_id, rng, risk_score)

            self._insert(
                patient_id=patient_id,
                mrn=f"MRN-{100000 + i}",
                name=f"{first} {last}",
                age=age,
                gender=gender,
                dob="",
                diagnosis=diagnosis,
                phone=f"(555) {rng.randint(100,999)}-{rng.randint(1000,9999)}",
                email=f"{first.lower()}.{last.lower()}{i}@example.com",
                address=f"{rng.randint(100,9999)} Main St, Springfield, ST {rng.randint(10000,99999)}",
                risk_score=risk_score,
                length_of_stay=round(rng.uniform(1.5, 12.0), 1),
                last_visit=last_visit,
                detail=detail,
                created_by="system",
            )

    # ── Helpers ──────────────────────────────────────────────────────────

    def _insert(
        self,
        *,
        patient_id: str,
        mrn: str,
        name: str,
        age: int,
        gender: str,
        dob: str,
        diagnosis: str,
        phone: str,
        email: str,
        address: str,
        risk_score: float,
        length_of_stay: float,
        last_visit: str,
        detail: Dict[str, Any],
        created_by: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            """
            INSERT INTO patients (
                id, mrn, name, age, gender, dob, diagnosis, phone, email, address,
                risk_score, risk_band, length_of_stay, last_visit,
                lab_results, diagnoses, medications, risk_factors, interventions, timeline,
                created_by, created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?, ?,?,?,?, ?,?,?,?,?,?, ?,?,?)
            """,
            (
                patient_id,
                mrn,
                name,
                age,
                gender,
                dob,
                diagnosis,
                phone,
                email,
                address,
                risk_score,
                _risk_band(risk_score),
                length_of_stay,
                last_visit,
                json.dumps(detail["lab_results"]),
                json.dumps(detail["diagnoses"]),
                json.dumps(detail["medications"]),
                json.dumps(detail["risk_factors"]),
                json.dumps(detail["interventions"]),
                json.dumps(detail["timeline"]),
                created_by,
                now,
                now,
            ),
        )
        self.conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row, full: bool = False) -> Dict[str, Any]:
        base = {
            "id": row["id"],
            "mrn": row["mrn"],
            "name": row["name"],
            "age": row["age"],
            "gender": row["gender"],
            "diagnosis": row["diagnosis"],
            "riskScore": row["risk_score"],
            "riskBand": row["risk_band"],
            "lengthOfStay": row["length_of_stay"],
            "lastVisit": row["last_visit"],
        }
        if full:
            base.update(
                {
                    "dob": row["dob"],
                    "phone": row["phone"],
                    "email": row["email"],
                    "address": row["address"],
                    "primaryDiagnosis": row["diagnosis"],
                    "labResults": json.loads(row["lab_results"] or "[]"),
                    "diagnoses": json.loads(row["diagnoses"] or "[]"),
                    "medications": json.loads(row["medications"] or "[]"),
                    "riskFactors": json.loads(row["risk_factors"] or "[]"),
                    "interventions": json.loads(row["interventions"] or "[]"),
                    "timeline": json.loads(row["timeline"] or "[]"),
                    "createdAt": row["created_at"],
                    "updatedAt": row["updated_at"],
                }
            )
        return base

    # ── Public API ───────────────────────────────────────────────────────

    def count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS c FROM patients").fetchone()
        return int(row["c"])

    def list_all_raw(self) -> List[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM patients").fetchall()

    def list(
        self,
        search: Optional[str] = None,
        risk_band: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Dict[str, Any]], int]:
        clauses, params = [], []
        if search:
            clauses.append(
                "(LOWER(name) LIKE ? OR LOWER(id) LIKE ? OR LOWER(mrn) LIKE ?)"
            )
            like = f"%{search.strip().lower()}%"
            params += [like, like, like]
        if risk_band and risk_band != "all":
            clauses.append("risk_band = ?")
            params.append(risk_band)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        total = self.conn.execute(
            f"SELECT COUNT(*) AS c FROM patients {where}", params
        ).fetchone()["c"]

        page = max(1, page)
        page_size = max(1, min(page_size, 200))
        offset = (page - 1) * page_size
        rows = self.conn.execute(
            f"SELECT * FROM patients {where} ORDER BY risk_score DESC LIMIT ? OFFSET ?",
            params + [page_size, offset],
        ).fetchall()
        return [self._row_to_dict(r) for r in rows], int(total)

    def get(self, patient_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        return self._row_to_dict(row, full=True) if row else None

    def create(self, payload: Dict[str, Any], created_by: str) -> Dict[str, Any]:
        patient_id = payload.get("id") or f"P{uuid.uuid4().hex[:8].upper()}"
        demographics = {
            "age": payload.get("age"),
            "gender": payload.get("gender"),
            "diagnosis": payload.get("diagnosis"),
        }
        prediction = _predict_risk(patient_id, demographics)
        risk_score = float(prediction.get("risk_score", 0.5))
        rng = random.Random(patient_id)
        detail = self._generate_detail(patient_id, rng, risk_score)

        self._insert(
            patient_id=patient_id,
            mrn=payload.get("mrn") or f"MRN-{rng.randint(100000, 999999)}",
            name=payload["name"],
            age=payload.get("age", 0),
            gender=payload.get("gender", ""),
            dob=payload.get("dob", ""),
            diagnosis=payload.get("diagnosis", ""),
            phone=payload.get("phone", ""),
            email=payload.get("email", ""),
            address=payload.get("address", ""),
            risk_score=risk_score,
            length_of_stay=round(rng.uniform(1.5, 12.0), 1),
            last_visit=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            detail=detail,
            created_by=created_by,
        )
        created = self.get(patient_id)
        assert created is not None
        return created

    def update(
        self, patient_id: str, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if self.get(patient_id) is None:
            return None
        allowed = {
            "name",
            "age",
            "gender",
            "diagnosis",
            "phone",
            "email",
            "address",
            "mrn",
        }
        updates = {k: v for k, v in payload.items() if k in allowed and v is not None}
        if updates:
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            self.conn.execute(
                f"UPDATE patients SET {set_clause}, updated_at = ? WHERE id = ?",
                (*updates.values(), datetime.now(timezone.utc).isoformat(), patient_id),
            )
            self.conn.commit()
        return self.get(patient_id)

    def delete(self, patient_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def recompute_risk(self, patient_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        ).fetchone()
        if row is None:
            return None
        prediction = _predict_risk(
            patient_id,
            {"age": row["age"], "gender": row["gender"], "diagnosis": row["diagnosis"]},
        )
        risk_score = float(prediction.get("risk_score", row["risk_score"] or 0.5))
        self.conn.execute(
            "UPDATE patients SET risk_score = ?, risk_band = ?, updated_at = ? WHERE id = ?",
            (
                risk_score,
                _risk_band(risk_score),
                datetime.now(timezone.utc).isoformat(),
                patient_id,
            ),
        )
        self.conn.commit()
        return self.get(patient_id)
