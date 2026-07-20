"""
Authentication utilities: password hashing and JWT issuing/verification.

Password hashing uses PBKDF2-HMAC-SHA256 from the Python standard library
(``hashlib``) so the backend has no native/C-extension dependency for
credential storage. Tokens are signed JWTs (HS256) via PyJWT.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.config import settings

_HASH_NAME = "sha256"
_PBKDF2_ITERATIONS = 260_000

bearer_scheme = HTTPBearer(auto_error=False)


# ── Passwords ────────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 hash encoded as `pbkdf2_sha256$iters$salt$hash`."""
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac(
        _HASH_NAME, password.encode("utf-8"), bytes.fromhex(salt), _PBKDF2_ITERATIONS
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${derived.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Constant-time verification of a plaintext password against a stored hash."""
    try:
        algo_tag, iterations_str, salt, hash_hex = encoded_hash.split("$")
        if algo_tag != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
    except (ValueError, AttributeError):
        return False

    derived = hashlib.pbkdf2_hmac(
        _HASH_NAME, password.encode("utf-8"), bytes.fromhex(salt), iterations
    )
    return hmac.compare_digest(derived.hex(), hash_hex)


# ── JWTs ─────────────────────────────────────────────────────────────────


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )


# ── FastAPI dependency ──────────────────────────────────────────────────


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """Resolve the authenticated user from the `Authorization: Bearer` header.

    Raises 401 if the token is missing, malformed, expired, or no longer
    matches a known account.
    """
    from backend.app.models.user import UserStore  # local import avoids cycles

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired, please sign in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    user = UserStore().get_by_id(payload.get("sub", ""))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer exists.",
        )
    return user
