"""
PHI Audit Logger Module for Nexora

This module provides comprehensive audit logging for Protected Health Information (PHI) access.
It ensures HIPAA compliance by tracking all access to patient data.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class PHIAuditLogger:
    """
    Audit logger for tracking access to Protected Health Information (PHI).

    This class maintains a SQLite database of all PHI access events, including
    who accessed what data, when, and for what purpose. This is critical for
    HIPAA compliance and security auditing.
    """

    def __init__(self, db_path: str = "audit/phi_access.db") -> None:
        """
        Initialize the PHI audit logger.

        Args:
            db_path: Path to the SQLite database file for audit logs
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
        logger.info(f"Initialized PHI Audit Logger with database: {db_path}")

    def _init_db(self) -> None:
        """Initialize the audit log database schema."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS access_logs (
                timestamp TEXT NOT NULL,
                user_id TEXT NOT NULL,
                patient_id TEXT NOT NULL,
                resource_type TEXT NOT NULL,
                operation TEXT NOT NULL,
                justification TEXT NOT NULL,
                model_used TEXT,
                PRIMARY KEY (timestamp, user_id, patient_id)
            )
        """
        )

        # Create indexes for common queries
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_patient_id 
            ON access_logs(patient_id)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_id 
            ON access_logs(user_id)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON access_logs(timestamp)
        """
        )

        self.conn.commit()

    def log_access(
        self,
        user_id: str,
        patient_id: str,
        resource_type: str,
        operation: str,
        justification: str,
        model: Optional[str] = None,
    ) -> None:
        """
        Log an access event to the audit database.

        Args:
            user_id: ID of the user accessing the data
            patient_id: ID of the patient whose data is being accessed
            resource_type: Type of resource being accessed
            operation: Operation being performed (READ, WRITE, UPDATE, DELETE)
            justification: Reason for accessing the data
            model: Model used for the operation (if applicable)
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO access_logs VALUES (?, ?, ?, ?, ?, ?, ?)
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
        """
        Logs a prediction request which involves accessing PHI.

        Args:
            patient_id: ID of the patient whose data is being used for prediction
            user_id: ID of the user requesting the prediction
            model_used: Name and version of the model being used
        """
        self.log_access(
            user_id=user_id,
            patient_id=patient_id,
            resource_type="PredictionRequest",
            operation="READ",
            justification="Clinical Decision Support",
            model=model_used,
        )

    def generate_report(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Generate an audit report for a specific time period.

        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)

        Returns:
            DataFrame containing audit log entries within the specified time range
        """
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

            rows = cursor.fetchall()

            df = pd.DataFrame(
                rows,
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

            logger.info(
                f"Generated audit report: {len(df)} entries between {start_date} and {end_date}"
            )

            return df

        except sqlite3.Error as e:
            logger.error(f"Failed to generate audit report: {str(e)}")
            raise

    def get_patient_access_history(self, patient_id: str) -> pd.DataFrame:
        """
        Get all access history for a specific patient.

        Args:
            patient_id: ID of the patient

        Returns:
            DataFrame containing all access events for the patient
        """
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

            rows = cursor.fetchall()

            df = pd.DataFrame(
                rows,
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

            return df

        except sqlite3.Error as e:
            logger.error(f"Failed to get patient access history: {str(e)}")
            raise

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Closed PHI Audit Logger database connection")

    def __del__(self) -> None:
        """Cleanup database connection on deletion."""
        self.close()
