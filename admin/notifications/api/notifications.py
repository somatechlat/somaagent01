"""Notifications API Router.

Migrated from: services/gateway/routers/notifications.py
Django Ninja.
"""

from __future__ import annotations

import logging
from typing import Optional

from django.http import HttpRequest
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from services.common.authorization import authorize

router = Router(tags=["notifications"])
logger = logging.getLogger(__name__)


def _get_store():
    """Execute get store."""

    from services.common.notifications_store import NotificationsStore

    return NotificationsStore()


class CreateNotificationRequest(BaseModel):
    """Data model for CreateNotificationRequest."""

    type: str
    title: str
    body: str
    severity: str = "info"
    ttl_seconds: Optional[int] = None
    meta: Optional[dict] = None


@router.get("", summary="List notifications", auth=AuthBearer())
async def list_notifications(
    request: HttpRequest, limit: int = 50, unreadOnly: bool = False
) -> dict:
    """Return a list of notifications."""
    await authorize(request, action="org:user_activity", resource="notifications")
    try:
        store = _get_store()
        await store.ensure_schema()
        data = await store.list(
            tenant_id="default", user_id=None, limit=limit, unread_only=unreadOnly
        )
        return {"notifications": data}
    except Exception as exc:
        # Fail loud. Returning [] here made a broken store look like "you have
        # no notifications", which is the worst possible lie to show an admin.
        logger.error("Failed to list notifications: %s", exc)
        raise HttpError(502, f"Notification store unavailable: {exc}")


@router.post("", summary="Create notification", auth=AuthBearer())
async def create_notification(request: HttpRequest, req: CreateNotificationRequest) -> dict:
    """Create a new notification."""
    # Not self-service: this writes into someone else's inbox, so user_update.
    await authorize(request, action="org:user_update", resource="notifications")
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


@router.post("/{notif_id}/read", summary="Mark read", auth=AuthBearer())
async def mark_read(request: HttpRequest, notif_id: str) -> dict:
    """Execute mark read.

    Args:
        notif_id: The notif_id.
    """
    await authorize(request, action="org:user_activity", resource="notifications")

    store = _get_store()
    await store.ensure_schema()
    await store.mark_read(tenant_id="default", notif_id=notif_id, user_id=None)
    return {"status": "ok"}


@router.delete("/clear", summary="Clear notifications", auth=AuthBearer())
async def clear_notifications(request: HttpRequest) -> dict:
    """Execute clear notifications."""
    # Not self-service: clearing erases the record of what was delivered.
    await authorize(request, action="org:user_update", resource="notifications")

    store = _get_store()
    await store.ensure_schema()
    await store.clear(tenant_id="default", user_id=None)
    return {"status": "cleared"}
