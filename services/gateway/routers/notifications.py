"""Notifications REST API used by the Web UI.

The UI expects a set of endpoints under ``/v1/ui/notifications`` for CRUD
operations on toast/notification objects.  The implementation mirrors the
behaviour of the original monolith but is deliberately lightweight – it only
exposes the operations required by the current front‑end:

* ``GET /v1/ui/notifications`` – list notifications with optional filtering.
* ``POST /v1/ui/notifications`` – create a new notification.
* ``POST /v1/ui/notifications/{notif_id}/read`` – mark a notification as read.
* ``DELETE /v1/ui/notifications`` – clear all notifications for a tenant /
  optional user.

All calls delegate to :class:`services.common.notifications_store.NotificationsStore`
which handles Postgres interaction.  Errors are translated to ``HTTPException``
instances with appropriate status codes so the UI receives standard JSON error
objects.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator

from services.common.notifications_store import NotificationsStore

router = APIRouter(prefix="/v1/ui/notifications", tags=["notifications"])


class NotificationCreate(BaseModel):
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    type: str = Field(..., description="Notification type/category")
    title: str = Field(..., description="Short title shown in the toast")
    body: str = Field(..., description="Full body text of the notification")
    severity: str = Field(..., description="One of 'info', 'success', 'warning', 'error'")
    ttl_seconds: Optional[int] = Field(
        None, description="Time‑to‑live in seconds; ``null`` means keep forever"
    )
    meta: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")

    @validator("severity")
    def _validate_severity(cls, v: str) -> str:
        allowed = {"info", "success", "warning", "error"}
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v


@router.get("")
async def list_notifications(
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_id: Optional[str] = Query(None, description="Optional user identifier"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items to return"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    cursor_created_at: Optional[str] = Query(
        None, description="ISO‑8601 timestamp for pagination cursor"
    ),
    cursor_id: Optional[str] = Query(None, description="Notification ID for pagination cursor"),
):
    """List notifications for a tenant (and optionally a user).

    The endpoint mirrors the signature of :meth:`NotificationsStore.list` and
    returns a JSON list of notification objects.
    """
    store = NotificationsStore()
    # Ensure the underlying table exists before querying.
    await store.ensure_schema()
    try:
        items: List[Dict[str, Any]] = await store.list(
            tenant_id=tenant_id,
            user_id=user_id,
            limit=limit,
            severity=severity,
            unread_only=unread_only,
            cursor_created_at=None,
            cursor_id=cursor_id,
        )
        return items
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("", status_code=201)
async def create_notification(payload: NotificationCreate):
    """Create a new notification and return the stored representation."""
    store = NotificationsStore()
    await store.ensure_schema()
    try:
        created = await store.create(
            tenant_id=payload.tenant_id,
            user_id=payload.user_id,
            ntype=payload.type,
            title=payload.title,
            body=payload.body,
            severity=payload.severity,
            ttl_seconds=payload.ttl_seconds,
            meta=payload.meta,
        )
        return created
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/{notif_id}/read")
async def mark_notification_read(
    notif_id: str,
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_id: Optional[str] = Query(None, description="Optional user identifier"),
):
    """Mark a specific notification as read."""
    store = NotificationsStore()
    await store.ensure_schema()
    try:
        success = await store.mark_read(tenant_id=tenant_id, notif_id=notif_id, user_id=user_id)
        if not success:
            raise HTTPException(status_code=404, detail="notification_not_found")
        return {"status": "read"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.delete("")
async def clear_notifications(
    tenant_id: str = Query(..., description="Tenant identifier"),
    user_id: Optional[str] = Query(None, description="Optional user identifier"),
):
    """Delete all notifications for a tenant (and optionally a user)."""
    store = NotificationsStore()
    await store.ensure_schema()
    try:
        deleted = await store.clear(tenant_id=tenant_id, user_id=user_id)
        return {"deleted": deleted}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


__all__ = ["router"]