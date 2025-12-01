"""Minimal notifications REST API.

Provides the endpoints required by the Web UI's ``notificationsStore.js``.
All routes are under the ``/v1/notifications`` prefix and operate on the
``NotificationsStore`` defined in ``services.common.notifications_store``.
The implementation is deliberately lightweight – it creates the table on the
first request and swallows any database errors, returning empty results so the
UI remains functional even when the database is unavailable.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.common.notifications_store import NotificationsStore

router = APIRouter(prefix="/v1/notifications", tags=["notifications"])

STORE = NotificationsStore()


class CreateNotificationRequest(BaseModel):
    type: str
    title: str
    body: str
    severity: str = "info"
    ttl_seconds: int | None = None
    meta: dict | None = None


@router.get("")
async def list_notifications(limit: int = 50, unreadOnly: bool = False):
    """Return a list of notifications for the current tenant.

    For simplicity the tenant_id is taken from an environment variable; the UI
    does not currently send a tenant identifier.
    """
    try:
        await STORE.ensure_schema()
        tenant = "default"
        data = await STORE.list(
            tenant_id=tenant,
            user_id=None,
            limit=limit,
            unread_only=unreadOnly,
        )
        return {"notifications": data}
    except Exception:
        return {"notifications": []}


@router.post("")
async def create_notification(req: CreateNotificationRequest):
    try:
        await STORE.ensure_schema()
        tenant = "default"
        notif = await STORE.create(
            tenant_id=tenant,
            user_id=None,
            ntype=req.type,
            title=req.title,
            body=req.body,
            severity=req.severity,
            ttl_seconds=req.ttl_seconds,
            meta=req.meta or {},
        )
        return {"notification": notif}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/{notif_id}/read")
async def mark_read(notif_id: str):
    try:
        await STORE.ensure_schema()
        tenant = "default"
        await STORE.mark_read(tenant_id=tenant, notif_id=notif_id, user_id=None)
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/clear")
async def clear_notifications():
    try:
        await STORE.ensure_schema()
        tenant = "default"
        await STORE.clear(tenant_id=tenant, user_id=None)
        return {"status": "cleared"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
