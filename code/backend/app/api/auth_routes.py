"""
Authentication & account API routes.

Imported by rest_api.py and mounted under /auth. All endpoints operate on
the SQLite-backed UserStore; passwords are never returned to the client.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import create_access_token, get_current_user
from backend.app.models.user import UserStore
from backend.app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserOut,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(payload: RegisterRequest) -> TokenResponse:
    store = UserStore()
    try:
        user = store.create_user(
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            organization=payload.organization,
            specialty=payload.specialty,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    token = create_access_token(user_id=user["id"], email=user["email"])
    return TokenResponse(access_token=token, user=UserOut(**user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    store = UserStore()
    user = store.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    token = create_access_token(user_id=user["id"], email=user["email"])
    return TokenResponse(access_token=token, user=UserOut(**user))


@router.get("/me", response_model=UserOut)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)) -> UserOut:
    return UserOut(**current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> UserOut:
    store = UserStore()
    updated = store.update_profile(
        current_user["id"],
        full_name=payload.full_name,
        organization=payload.organization,
        specialty=payload.specialty,
    )
    assert updated is not None
    return UserOut(**updated)


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    store = UserStore()
    ok = store.change_password(
        current_user["id"], payload.current_password, payload.new_password
    )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    return {"status": "password_updated"}


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    # Tokens are stateless JWTs; the client discards the token on logout.
    # This endpoint exists for audit/telemetry symmetry and future
    # server-side revocation (e.g. a token blocklist) if ever needed.
    logger.info(f"User logged out: {current_user['email']}")
    return {"status": "logged_out"}
