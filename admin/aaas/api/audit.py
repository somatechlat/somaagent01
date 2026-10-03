"""Audit Log API Router.


Per AAAS_ADMIN_SRS.md Section 4.8 - Audit Trail
"""

from __future__ import annotations

import csv
from datetime import timedelta
from io import StringIO
from typing import Optional

from django.http import HttpResponse
from django.utils import timezone
from ninja import Query, Router
from pydantic import BaseModel

from admin.aaas.models import AuditLog
from admin.common.auth import AuthBearer
from admin.common.responses import paginated_response
from services.common.authorization import authorize_sync

router = Router(tags=["audit"])


# =============================================================================
# SCHEMAS
# =============================================================================


class AuditLogOut(BaseModel):
    """Audit log entry output. Mirrors ``AuditLog``'s real columns.

    One schema for the whole module. The former ``AuditEvent`` twin in
    ``admin/audit/api.py`` carried ``user_agent`` and ``request_id`` while this
    one dropped them; the model has both, so both are here and the twin is gone.
    """

    id: str
    actor_id: str
    actor_email: str
    tenant_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    old_value: Optional[dict] = None
    new_value: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: str = ""
    request_id: str = ""
    created_at: str


class AuditLogFilters(BaseModel):
    """Filters for audit log queries."""

    action: Optional[str] = None
    resource_type: Optional[str] = None
    actor_id: Optional[str] = None
    tenant_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def _to_out(log: AuditLog) -> AuditLogOut:
    """One row -> one output schema. Every read path goes through here."""
    return AuditLogOut(
        id=str(log.id),
        actor_id=str(log.actor_id),
        actor_email=log.actor_email or "",
        tenant_id=str(log.tenant_id) if log.tenant_id else None,  # type: ignore[reportAttributeAccessIssue]
        action=log.action,
        resource_type=log.resource_type,
        resource_id=str(log.resource_id) if log.resource_id else None,
        old_value=log.old_value,
        new_value=log.new_value,
        ip_address=log.ip_address,
        user_agent=log.user_agent or "",
        request_id=log.request_id or "",
        created_at=log.created_at.isoformat() if log.created_at else "",
    )


# =============================================================================
# ENDPOINTS
# =============================================================================


@router.get(
    "",
    summary="List audit logs",
    auth=AuthBearer(),
)
def list_audit_logs(
    request,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> dict:
    """List audit log entries with filtering.

    Per SRS Section 4.8 - Audit Trail:
    - Filter by action, resource type, actor, tenant
    - Date range filtering
    - Paginated results
    """
    authorize_sync(request, action="audit:read", resource="audit")

    qs = AuditLog.objects.all()

    # Apply filters
    if action:
        qs = qs.filter(action=action)
    if resource_type:
        qs = qs.filter(resource_type=resource_type)
    if actor_id:
        qs = qs.filter(actor_id=actor_id)
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__lte=end_date)

    total = qs.count()
    offset = (page - 1) * per_page
    logs = qs.order_by("-created_at")[offset : offset + per_page]

    return paginated_response(
        items=[_to_out(log).model_dump() for log in logs],
        total=total,
        page=page,
        page_size=per_page,
    )


@router.get(
    "/export",
    summary="Export audit logs to CSV",
    auth=AuthBearer(),
)
def export_audit_logs(
    request,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    tenant_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(1000, ge=1, le=10000),
) -> HttpResponse:
    """Export audit logs to CSV format.

    Per SRS Section 4.8 - CSV export for compliance.
    """
    # Exporting the evidence trail is a stricter authority than reading it.
    authorize_sync(request, action="audit:export", resource="audit")

    qs = AuditLog.objects.all()

    if action:
        qs = qs.filter(action=action)
    if resource_type:
        qs = qs.filter(resource_type=resource_type)
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__lte=end_date)

    logs = qs.order_by("-created_at")[:limit]

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "id",
            "created_at",
            "actor_id",
            "actor_email",
            "action",
            "resource_type",
            "resource_id",
            "tenant_id",
            "ip_address",
        ]
    )

    # Data rows
    for log in logs:
        writer.writerow(
            [
                str(log.id),
                log.created_at.isoformat() if log.created_at else "",
                str(log.actor_id),
                log.actor_email or "",
                log.action,
                log.resource_type,
                str(log.resource_id) if log.resource_id else "",
                str(log.tenant_id) if log.tenant_id else "",  # type: ignore[reportAttributeAccessIssue]
                log.ip_address or "",
            ]
        )

    response = HttpResponse(output.getvalue(), content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="audit_log_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    )
    return response


@router.get(
    "/actions",
    summary="Get distinct action types",
    auth=AuthBearer(),
)
def get_audit_actions(request) -> dict:
    """Get list of distinct action types for filtering."""
    # Gate before the query: an unauthenticated caller must not learn which
    # action names exist in the log.
    authorize_sync(request, action="audit:read", resource="audit")

    actions = AuditLog.objects.values_list("action", flat=True).distinct()
    return {"actions": list(actions)}


@router.get(
    "/resource-types",
    summary="Get distinct resource types",
    auth=AuthBearer(),
)
def get_resource_types(request) -> dict:
    """Get list of distinct resource types for filtering."""
    # Same rule as action names: the vocabulary is part of the evidence.
    authorize_sync(request, action="audit:read", resource="audit")

    types = AuditLog.objects.values_list("resource_type", flat=True).distinct()
    return {"resource_types": list(types)}


@router.get(
    "/stats",
    summary="Get audit log statistics",
    auth=AuthBearer(),
)
def get_audit_stats(
    request,
    tenant_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=30),
) -> dict:
    """Get audit log statistics for dashboard.

    Returns action counts, top actors, etc.
    """
    authorize_sync(request, action="audit:read", resource="audit")

    from django.db.models import Count

    start_date = timezone.now() - timedelta(days=days)
    qs = AuditLog.objects.filter(created_at__gte=start_date)

    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)

    total = qs.count()

    # Actions by type
    by_action = list(qs.values("action").annotate(count=Count("id")).order_by("-count")[:10])

    # Top actors
    by_actor = list(qs.values("actor_email").annotate(count=Count("id")).order_by("-count")[:5])

    return {
        "total_actions": total,
        "period_days": days,
        "by_action": by_action,
        "by_actor": by_actor,
    }

# =============================================================================
# ENDPOINTS - Event detail & history
# =============================================================================
#
# These four lived in ``admin/audit/api.py``, a second audit API mounted at
# ``/audit`` with zero callers. Audit has one home now: this module. They are
# registered after every literal path so ``/{event_id}`` cannot swallow them.


class AuditSummaryOut(BaseModel):
    """Aggregate counts over the audit trail."""

    total_events: int
    by_action: dict
    by_resource: dict


@router.get("/summary", response=AuditSummaryOut, summary="Audit summary", auth=AuthBearer())
def get_audit_summary(
    request,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> AuditSummaryOut:
    """Aggregate counts by action and resource type."""
    authorize_sync(request, action="audit:read", resource="audit")

    from django.db.models import Count

    qs = AuditLog.objects.all()
    if start_date:
        qs = qs.filter(created_at__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__lte=end_date)

    return AuditSummaryOut(
        total_events=qs.count(),
        by_action=dict(qs.values_list("action").annotate(n=Count("id")).order_by()),
        by_resource=dict(qs.values_list("resource_type").annotate(n=Count("id")).order_by()),
    )


@router.get(
    "/actors/{actor_id}",
    summary="Audit trail for one actor",
    auth=AuthBearer(),
)
def get_actor_history(
    request,
    actor_id: str,
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    """Every recorded action by one actor."""
    authorize_sync(request, action="audit:read", resource="audit")

    rows = AuditLog.objects.filter(actor_id=actor_id).order_by("-created_at")[:limit]
    return {"actor_id": actor_id, "events": [_to_out(r).model_dump() for r in rows]}


@router.get(
    "/resources/{resource_type}/{resource_id}",
    summary="Audit trail for one resource",
    auth=AuthBearer(),
)
def get_resource_history(
    request,
    resource_type: str,
    resource_id: str,
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    """Every recorded action against one resource."""
    authorize_sync(request, action="audit:read", resource="audit")

    rows = AuditLog.objects.filter(
        resource_type=resource_type, resource_id=resource_id
    ).order_by("-created_at")[:limit]
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "events": [_to_out(r).model_dump() for r in rows],
    }


@router.get(
    "/events/{event_id}",
    response=AuditLogOut,
    summary="Get one audit event",
    auth=AuthBearer(),
)
def get_audit_event(request, event_id: str) -> AuditLogOut:
    """One audit row by id.

    Mounted at ``/events/{event_id}``, not ``/{event_id}``: a bare
    single-segment wildcard would shadow ``/summary``, ``/export``,
    ``/actions``, ``/stats`` and ``/resource-types``, which are all literals
    that must keep winning.
    """
    authorize_sync(request, action="audit:read", resource="audit")

    from uuid import UUID

    from admin.common.exceptions import NotFoundError

    try:
        pk = UUID(event_id)
    except ValueError:
        raise NotFoundError("audit event", event_id)
    try:
        log = AuditLog.objects.get(id=pk)
    except AuditLog.DoesNotExist:
        raise NotFoundError("audit event", event_id)
    return _to_out(log)

