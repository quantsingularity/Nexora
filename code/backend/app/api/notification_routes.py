"""
Alerts / notifications API routes.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.security import get_current_user
from backend.app.models.notification import NotificationStore

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("")
async def list_notifications(current_user: Dict[str, Any] = Depends(get_current_user)):
    store = NotificationStore()
    items = store.list_for_user(current_user["id"])
    return {"notifications": items, "unread": sum(1 for n in items if not n["read"])}


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    store = NotificationStore()
    valid_ids = {n["id"] for n in store.list_for_user(current_user["id"])}
    if notification_id not in valid_ids:
        raise HTTPException(status_code=404, detail="Notification not found")
    store.mark_read(current_user["id"], notification_id)
    return {"status": "read", "id": notification_id}


@router.post("/read-all")
async def mark_all_read(current_user: Dict[str, Any] = Depends(get_current_user)):
    store = NotificationStore()
    store.mark_all_read(current_user["id"])
    return {"status": "all_read"}
