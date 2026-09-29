"""Audit API - Security audit logging.

Read side of the real ``admin.aaas.models.AuditLog`` table. That model is
written by ``admin.common.middleware``, ``admin.auth.api`` and the AAAS
admin handlers; this module queries it and invents nothing.

The previous version of this file returned a hardcoded ``user-123`` login
event, zeroed summary buckets, a compliance report id minted from ``uuid4``,
an alerts list and a retention policy of ``365``/``90`` days. None of it was
backed by a table. The report, alert and retention routes are gone: there is
no report store, no alert store and no settings store behind them.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from asgiref.sync import sync_to_async
from django.db.models import Count
from ninja import Router
from ninja.errors import HttpError
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from services.common.authorization import authorize

router = Router(tags=["audit"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS — mirror AuditLog's real columns, nothing more.
# =============================================================================


class AuditEvent(BaseModel):
    """One row of the audit trail."""

    event_id: str
    timestamp: str
    actor_id: str
    actor_email: Optional[str] = None
    tenant_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None


class AuditSummary(BaseModel):
    """Aggregate counts over the audit trail."""

    total_events: int
    by_action: dict
    by_resource: dict


def _to_event(row) -> AuditEvent:
    return AuditEvent(
        event_id=str(row.id),
        timestamp=row.created_at.isoformat() if row.created_at else "",
        actor_id=str(row.actor_id),
        actor_email=row.actor_email or None,
        tenant_id=str(row.tenant_id) if row.tenant_id else None,
        action=row.action,
        resource_type=row.resource_type,
        resource_id=str(row.resource_id) if row.resource_id else None,
        old_value=row.old_value,
        new_value=row.new_value,
        ip_address=row.ip_address,
        user_agent=row.user_agent or None,
        request_id=row.request_id or None,
    )


def _parse_date(value: Optional[str], field: str) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HttpError(400, f"{field} must be an ISO-8601 timestamp, got {value!r}")


# =============================================================================
# ENDPOINTS - Audit Events
# =============================================================================


@router.get(
    "",
    summary="List audit events",
    auth=AuthBearer(),
)
async def list_audit_events(
    request,
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List audit events."""
    await authorize(request, action="audit:read", resource="audit")

    from admin.aaas.models import AuditLog

    start = _parse_date(from_date, "from_date")
    end = _parse_date(to_date, "to_date")

    @sync_to_async
    def _query():
        qs = AuditLog.objects.all()
        if actor_id:
            try:
                qs = qs.filter(actor_id=UUID(actor_id))
            except ValueError:
                raise HttpError(400, f"actor_id must be a UUID, got {actor_id!r}")
        if action:
            qs = qs.filter(action=action)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if start:
            qs = qs.filter(created_at__gte=start)
        if end:
            qs = qs.filter(created_at__lte=end)

        total = qs.count()
        rows = list(qs.order_by("-created_at")[offset : offset + limit])
        return [_to_event(r).model_dump() for r in rows], total

    events, total = await _query()
    return {"events": events, "total": total, "offset": offset, "limit": limit}


@router.get(
    "/summary",
    response=AuditSummary,
    summary="Get audit summary",
    auth=AuthBearer(),
)
async def get_audit_summary(
    request,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> AuditSummary:
    """Get audit summary statistics."""
    await authorize(request, action="audit:read", resource="audit")

    from admin.aaas.models import AuditLog

    start = _parse_date(from_date, "from_date")
    end = _parse_date(to_date, "to_date")

    @sync_to_async
    def _query():
        qs = AuditLog.objects.all()
        if start:
            qs = qs.filter(created_at__gte=start)
        if end:
            qs = qs.filter(created_at__lte=end)
        return (
            qs.count(),
            dict(qs.values_list("action").annotate(n=Count("id")).order_by()),
            dict(qs.values_list("resource_type").annotate(n=Count("id")).order_by()),
        )

    total, by_action, by_resource = await _query()
    return AuditSummary(
        total_events=total,
        by_action=by_action,
        by_resource=by_resource,
    )


@router.get(
    "/{event_id}",
    response=AuditEvent,
    summary="Get audit event",
    auth=AuthBearer(),
)
async def get_audit_event(
    request,
    event_id: str,
) -> AuditEvent:
    """Get audit event details."""
    await authorize(request, action="audit:read", resource="audit")

    from admin.aaas.models import AuditLog

    @sync_to_async
    def _get():
        try:
            return AuditLog.objects.get(id=UUID(event_id))
        except ValueError:
            raise HttpError(400, f"event_id must be a UUID, got {event_id!r}")
        except AuditLog.DoesNotExist:
            raise HttpError(404, f"Audit event {event_id} not found")

    return _to_event(await _get())


# =============================================================================
# ENDPOINTS - History
# =============================================================================


@router.get(
    "/actors/{actor_id}",
    summary="Get actor history",
    auth=AuthBearer(),
)
async def get_actor_history(
    request,
    actor_id: str,
    limit: int = 50,
) -> dict:
    """Audit trail for one actor."""
    await authorize(request, action="audit:read", resource="audit")

    from admin.aaas.models import AuditLog

    try:
        actor_uuid = UUID(actor_id)
    except ValueError:
        raise HttpError(400, f"actor_id must be a UUID, got {actor_id!r}")

    @sync_to_async
    def _query():
        qs = AuditLog.objects.filter(actor_id=actor_uuid)
        return [_to_event(r).model_dump() for r in qs.order_by("-created_at")[:limit]]

    return {"actor_id": actor_id, "events": await _query()}


@router.get(
    "/resources/{resource_type}/{resource_id}",
    summary="Get resource history",
    auth=AuthBearer(),
)
async def get_resource_history(
    request,
    resource_type: str,
    resource_id: str,
    limit: int = 50,
) -> dict:
    """Audit trail for one resource."""
    await authorize(request, action="audit:read", resource="audit")

    from admin.aaas.models import AuditLog

    try:
        resource_uuid = UUID(resource_id)
    except ValueError:
        raise HttpError(400, f"resource_id must be a UUID, got {resource_id!r}")

    @sync_to_async
    def _query():
        qs = AuditLog.objects.filter(resource_type=resource_type, resource_id=resource_uuid)
        return [_to_event(r).model_dump() for r in qs.order_by("-created_at")[:limit]]

    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "events": await _query(),
    }


# Compliance reports, alerts and retention policy are not implemented: there
# is no report store, no alert store and no settings store behind them. The
# routes that claimed otherwise are gone.
