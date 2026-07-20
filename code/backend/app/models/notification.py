"""
Alert/notification store for the clinical dashboard (SQLite-backed).

Notifications are derived from current patient risk data (e.g. a high-risk
patient needing review) plus system events, and are stable across requests
because they're keyed by a deterministic id. Per-user read/unread state is
tracked in a small join table.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from backend.app.core.database import get_connection
from backend.app.models.patient import PatientStore


class NotificationStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.conn = get_connection(db_path)
        self._init_db()

    def _init_db(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notification_reads (
                user_id TEXT NOT NULL,
                notification_id TEXT NOT NULL,
                read_at TEXT NOT NULL,
                PRIMARY KEY (user_id, notification_id)
            )
            """
        )
        self.conn.commit()

    def _generate(self) -> List[Dict[str, Any]]:
        patients, _ = PatientStore(seed=False).list(
            risk_band="high", page=1, page_size=8
        )
        now = datetime.now(timezone.utc)
        items: List[Dict[str, Any]] = []
        for idx, p in enumerate(patients):
            items.append(
                {
                    "id": f"alert-risk-{p['id']}",
                    "severity": "critical" if p["riskScore"] >= 0.85 else "warning",
                    "title": f"High readmission risk: {p['name']}",
                    "message": (
                        f"{p['name']} ({p['id']}) has a 30-day readmission risk of "
                        f"{round(p['riskScore'] * 100)}%. Consider reviewing the care plan."
                    ),
                    "patient_id": p["id"],
                    "created_at": (now - timedelta(hours=idx * 3 + 1)).isoformat(),
                }
            )

        items.append(
            {
                "id": "alert-system-audit",
                "severity": "info",
                "title": "Weekly compliance report ready",
                "message": "The HIPAA audit log summary for this week has been generated.",
                "patient_id": None,
                "created_at": (now - timedelta(days=1)).isoformat(),
            }
        )
        items.append(
            {
                "id": "alert-system-models",
                "severity": "info",
                "title": "Model registry up to date",
                "message": "All prediction models are on their latest registered version.",
                "patient_id": None,
                "created_at": (now - timedelta(days=2)).isoformat(),
            }
        )
        items.sort(key=lambda n: n["created_at"], reverse=True)
        return items

    def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        read_ids = {
            row["notification_id"]
            for row in self.conn.execute(
                "SELECT notification_id FROM notification_reads WHERE user_id = ?",
                (user_id,),
            ).fetchall()
        }
        notifications = self._generate()
        for n in notifications:
            n["read"] = n["id"] in read_ids
        return notifications

    def mark_read(self, user_id: str, notification_id: str) -> None:
        self.conn.execute(
            """
            INSERT OR REPLACE INTO notification_reads (user_id, notification_id, read_at)
            VALUES (?, ?, ?)
            """,
            (user_id, notification_id, datetime.now(timezone.utc).isoformat()),
        )
        self.conn.commit()

    def mark_all_read(self, user_id: str) -> None:
        for n in self._generate():
            self.mark_read(user_id, n["id"])
