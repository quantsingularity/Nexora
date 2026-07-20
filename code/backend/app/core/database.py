"""
Shared SQLite connection helper for the Nexora application database.

Kept deliberately separate from the PHI audit database (`ml_core.compliance
.phi_audit_logger.PHIAuditLogger`) so compliance logs stay isolated from
application data such as accounts and patient records.
"""

from __future__ import annotations

import os
import sqlite3

from backend.app.core.config import settings


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection to the Nexora application database.

    The connection is safe to share across FastAPI's threaded request
    handling (``check_same_thread=False``) and rows are returned as
    ``sqlite3.Row`` so callers can access columns by name.
    """
    path = db_path or settings.APP_DB_PATH
    db_dir = os.path.dirname(path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
