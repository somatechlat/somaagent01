"""Notifications API Router.

Migrated from: services/gateway/routers/notifications.py
Django Ninja.
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import ServiceError

router = Router(tags=["notifications"])
logger = logging.getLogger(__name__)


def _get_store():
    from services.common.notifications_store import NotificationsStore

    return NotificationsStore()


class CreateNotificationRequest(BaseModel):
    type: str
    title: str
    body: str
    severity: str = "info"
    ttl_seconds: Optional[int] = None
    meta: Optional[dict] = None


@router.get("", summary="List notifications")
async def list_notifications(limit: int = 50, unreadOnly: bool = False) -> dict:
    """Return a list of notifications."""
    try:
        store = _get_store()
        await store.ensure_schema()
        data = await store.list(
            tenant_id="default", user_id=None, limit=limit, unread_only=unreadOnly
        )
        return {"notifications": data}
    except Exception:
        return {"notifications": []}


@router.post("", summary="Create notification")
async def create_notification(req: CreateNotificationRequest) -> dict:
    """Create a new notification."""
    store = _get_store()
    await store.ensure_schema()
    notif = await store.create(
        tenant_id="default",
        user_id=None,
        ntype=req.type,
        title=req.title,
        body=req.body,
        severity=req.severity,
        ttl_seconds=req.ttl_seconds,
        meta=req.meta or {},
    )
    return {"notification": notif}


@router.post("/{notif_id}/read", summary="Mark read")
async def mark_read(notif_id: str) -> dict:
    store = _get_store()
    await store.ensure_schema()
    await store.mark_read(tenant_id="default", notif_id=notif_id, user_id=None)
    return {"status": "ok"}


@router.delete("/clear", summary="Clear notifications")
async def clear_notifications() -> dict:
    store = _get_store()
    await store.ensure_schema()
    await store.clear(tenant_id="default", user_id=None)
    return {"status": "cleared"}
