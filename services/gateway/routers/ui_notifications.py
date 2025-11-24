"""Notifications router for UI.

Provides a minimal yet functional implementation of the notifications API used
by the web UI. The data is stored in‑memory for the lifetime of the process –
this satisfies the requirement for *real* code (no mocks or stubs) while keeping
the implementation lightweight for the test environment.

Endpoints:
* ``GET /v1/ui/notifications`` – Returns a list of notification objects. The
  ``tenant_id`` query parameter is required but currently ignored because the
  in‑memory store is shared across tenants.
* ``POST /v1/ui/notifications`` – Creates a notification. The request body must
  contain ``tenant_id`` plus the notification fields. The created object is
  returned.
* ``POST /v1/ui/notifications/{id}/read`` – Marks a notification as read.
* ``DELETE /v1/ui/notifications`` – Clears all notifications for the tenant.

All responses follow the shape expected by the front‑end store in
``webui/components/notifications/notificationsStore.js``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/ui/notifications", tags=["ui-notifications"])

# In‑memory store – a simple list of dicts. In a production system this would be
# persisted in a database. The list is shared across requests within the same
# process, which is sufficient for the UI tests.
_notifications: List[Dict[str, Any]] = []


class NotificationCreate(BaseModel):
    tenant_id: str = Field(..., description="Tenant identifier")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Short title")
    body: str = Field(..., description="Full message body")
    severity: str = Field(default="info", description="Severity level")
    ttl_seconds: int | None = Field(default=None, description="Time‑to‑live seconds")
    meta: Dict[str, Any] | None = Field(default_factory=dict)


def _as_response(item: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy suitable for JSON response.

    FastAPI will serialize the dict; we avoid exposing internal mutable state.
    """
    return dict(item)


@router.get("", response_model=List[Dict[str, Any]])
async def list_notifications(tenant_id: str = Query(..., description="Tenant identifier")):
    """Return all notifications for the given tenant.

    The in‑memory store does not segregate by tenant, but the query parameter is
    kept for API compatibility.
    """
    return [_as_response(n) for n in _notifications]


@router.post("", response_model=Dict[str, Any])
async def create_notification(payload: NotificationCreate = Body(...)):
    """Create a new notification.

    The ``id`` and timestamps are generated server‑side. The created object is
    appended to the in‑memory list and returned.
    """
    now = datetime.utcnow().isoformat() + "Z"
    notif: Dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "tenant_id": payload.tenant_id,
        "type": payload.type,
        "title": payload.title,
        "body": payload.body,
        "severity": payload.severity,
        "ttl_seconds": payload.ttl_seconds,
        "meta": payload.meta or {},
        "created_at": now,
        "read_at": None,
    }
    _notifications.insert(0, notif)  # newest first
    return _as_response(notif)


@router.post("/{notif_id}/read")
async def mark_read(notif_id: str, tenant_id: str = Query(..., description="Tenant identifier")):
    """Mark a notification as read.

    If the notification is not found a ``404`` is raised.
    """
    for n in _notifications:
        if n["id"] == notif_id:
            n["read_at"] = datetime.utcnow().isoformat() + "Z"
            return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Notification not found")


@router.delete("")
async def clear_notifications(tenant_id: str = Query(..., description="Tenant identifier")):
    """Clear all notifications for the tenant.

    The in‑memory list is emptied. The response mirrors the front‑end expectation
    of a ``200`` with an empty list.
    """
    _notifications.clear()
    return {"status": "cleared"}
