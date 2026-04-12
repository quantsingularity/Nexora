"""
PHI Audit Logger Module for Nexora

Tracks all access to Protected Health Information (PHI) for HIPAA compliance.
"""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Column names must match the DB schema exactly
_COLUMNS = [
    "id",
    "timestamp",
    "user_id",
    "patient_id",
    "resource_type",
    "operation",
    "justification",
    "model_used",
]
# Friendly aliases exposed to callers
_ALIAS_MAP = {
    "user_id": "user",
    "patient_id": "patient",
    "resource_type": "resource",
    "justification": "reason",
    "model_used": "model",
}


class PHIAuditLogger:
    """
    Audit logger for tracking access to Protected Health Information (PHI).
    """

    def __init__(self, db_path: str = "audit/phi_access.db") -> None:
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        logger.info(f"Initialized PHI Audit Logger with database: {db_path}")

    def _init_db(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                patient_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                operation TEXT NOT NULL,
                justification TEXT NOT NULL,
                model_used TEXT
            )
        """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_patient_id ON access_logs(patient_id)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_id ON access_logs(user_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON access_logs(timestamp)"
        )
        self.conn.commit()

    def _rows_to_df(self, rows: list) -> pd.DataFrame:
        """Convert raw DB rows to a DataFrame with aliased column names."""
        df = pd.DataFrame(rows, columns=_COLUMNS)
        df = df.rename(columns=_ALIAS_MAP)
        return df

    def log_access(
        self,
        user_id: str,
        patient_id: str,
        resource_type: str,
        operation: str,
        justification: str,
        model: Optional[str] = None,
    ) -> None:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO access_logs (timestamp, user_id, patient_id, resource_type, operation, justification, model_used)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcnow().isoformat(),
                    user_id,
                    patient_id,
                    resource_type,
                    operation,
                    justification,
                    model,
                ),
            )
            self.conn.commit()
            logger.info(
                f"Logged PHI access: user={user_id}, patient={patient_id}, "
                f"resource={resource_type}, operation={operation}"
            )
        except sqlite3.Error as e:
            logger.error(f"Failed to log PHI access: {str(e)}")
            raise

    def log_prediction_request(
        self, patient_id: str, user_id: str = "API_USER", model_used: str = "UNKNOWN"
    ) -> None:
        self.log_access(
            user_id=user_id,
            patient_id=patient_id,
            resource_type="PredictionRequest",
            operation="READ",
            justification="Clinical Decision Support",
            model=model_used,
        )

    def generate_report(self, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM access_logs
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
                """,
                (start_date, end_date),
            )
            return self._rows_to_df(cursor.fetchall())
        except sqlite3.Error as e:
            logger.error(f"Failed to generate audit report: {str(e)}")
            raise

    def get_patient_access_history(self, patient_id: str) -> pd.DataFrame:
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT * FROM access_logs
                WHERE patient_id = ?
                ORDER BY timestamp DESC
                """,
                (patient_id,),
            )
            return self._rows_to_df(cursor.fetchall())
        except sqlite3.Error as e:
            logger.error(f"Failed to get patient access history: {str(e)}")
            raise

    def close(self) -> None:
        if getattr(self, "conn", None):
            self.conn.close()
            logger.info("Closed PHI Audit Logger database connection")

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
