"""
User account model & store for Nexora authentication (SQLite-backed).

Mirrors the style of ``ml_core.compliance.phi_audit_logger.PHIAuditLogger``:
a small, dependency-free class that owns its own table and connection.
"""

from __future__ import annotations

import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.app.core.database import get_connection
from backend.app.core.security import hash_password, verify_password

logger = logging.getLogger(__name__)


class UserStore:
    """CRUD + authentication operations for clinician/user accounts."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self.conn = get_connection(db_path)
        self._init_db()

    def _init_db(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'clinician',
                organization TEXT,
                specialty TEXT,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        self.conn.commit()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
            "organization": row["organization"],
            "specialty": row["specialty"],
            "created_at": row["created_at"],
            "last_login_at": row["last_login_at"],
        }

    def create_user(
        self,
        full_name: str,
        email: str,
        password: str,
        role: str = "clinician",
        organization: Optional[str] = None,
        specialty: Optional[str] = None,
    ) -> Dict[str, Any]:
        email_normalized = email.strip().lower()
        if self.get_by_email(email_normalized) is not None:
            raise ValueError("An account with this email already exists.")

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        try:
            self.conn.execute(
                """
                INSERT INTO users
                    (id, full_name, email, password_hash, role, organization, specialty, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    full_name.strip(),
                    email_normalized,
                    hash_password(password),
                    role,
                    organization,
                    specialty,
                    now,
                ),
            )
            self.conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError("An account with this email already exists.") from exc

        logger.info(f"Created user account: {email_normalized}")
        created = self.get_by_id(user_id)
        assert created is not None
        return created

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        row = self.conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
        ).fetchone()
        if row is None or not verify_password(password, row["password_hash"]):
            return None
        self.conn.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), row["id"]),
        )
        self.conn.commit()
        return self.get_by_id(row["id"])

    def update_profile(self, user_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        allowed = {"full_name", "organization", "specialty"}
        updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
        if not updates:
            return self.get_by_id(user_id)
        set_clause = ", ".join(f"{k} = ?" for k in updates)
        self.conn.execute(
            f"UPDATE users SET {set_clause} WHERE id = ?",
            (*updates.values(), user_id),
        )
        self.conn.commit()
        return self.get_by_id(user_id)

    def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> bool:
        row = self.conn.execute(
            "SELECT password_hash FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None or not verify_password(current_password, row["password_hash"]):
            return False
        self.conn.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )
        self.conn.commit()
        return True
