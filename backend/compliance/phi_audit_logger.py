import sqlite3
from datetime import datetime
import pandas as pd


class PHIAuditLogger:

    def __init__(self, db_path: Any = "audit/phi_access.db") -> Any:
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> Any:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS access_logs (\n            timestamp TEXT,\n            user_id TEXT,\n            patient_id TEXT,\n            resource_type TEXT,\n            operation TEXT,\n            justification TEXT,\n            model_used TEXT\n        )"
        )

    def log_access(
        self,
        user_id: Any,
        patient_id: Any,
        resource_type: Any,
        operation: Any,
        justification: Any,
        model: Any = None,
    ) -> Any:
        self.conn.execute(
            "INSERT INTO access_logs VALUES (\n            ?, ?, ?, ?, ?, ?, ?\n        )",
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

    def log_prediction_request(
        self, patient_id: str, user_id: str = "API_USER", model_used: str = "UNKNOWN"
    ) -> Any:
        """
        Logs a prediction request which involves accessing PHI.
        """
        self.log_access(
            user_id=user_id,
            patient_id=patient_id,
            resource_type="PredictionRequest",
            operation="READ",
            justification="Clinical Decision Support",
            model=model_used,
        )

    def generate_report(self, start_date: Any, end_date: Any) -> Any:
        cursor = self.conn.execute(
            "SELECT * FROM access_logs\n            WHERE timestamp BETWEEN ? AND ?",
            (start_date, end_date),
        )
        return pd.DataFrame(
            cursor.fetchall(),
            columns=[
                "timestamp",
                "user",
                "patient",
                "resource",
                "operation",
                "reason",
                "model",
            ],
        )
