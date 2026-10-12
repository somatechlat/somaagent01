"""General admin API endpoints.

Migrated from: services/gateway/routers/admin.py
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from django.http import HttpRequest, HttpResponse
from ninja import Router

from admin.common.auth import AuthBearer
from services.common.authorization import authorize

router = Router(tags=["admin-general"])
logger = logging.getLogger(__name__)


@router.get("/ping", summary="Ping the server")
async def ping() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.get(
    "/audit/export",
    summary="Export audit logs as NDJSON",
    auth=AuthBearer(),
)
async def audit_export(
    request: HttpRequest,
    action: Optional[str] = None,
) -> HttpResponse:
    """Export audit logs as newline-delimited JSON.

    Args:
        action: Filter by specific action (e.g., "llm.invoke")

    Returns:
        Newline-delimited JSON response of audit records
    """
    # The audit record is the evidence trail. Exporting it is its own authority
    # in the catalog — not "is this person a sysadmin", which is a role string
    # that lives outside the catalog and renames itself.
    await authorize(request, action="audit:export", resource="audit")
    from services.common.audit_store import AuditStore

    store = AuditStore()
    try:
        await store.ensure_schema()
    except Exception:
        logger.debug("audit ensure_schema failed", exc_info=True)

    records = await store.list(event_type=action, limit=1000)

    def _serialize(evt: dict) -> dict:
        """Project a store row onto the NDJSON export shape."""
        return {
            "id": evt.get("id"),
            "timestamp": evt.get("timestamp"),
            "action": evt.get("action"),
            "resource": evt.get("resource"),
            "session_id": evt.get("session_id"),
            "tenant": evt.get("tenant"),
            "details": evt.get("details"),
            "trace_id": evt.get("trace_id"),
            "request_id": evt.get("request_id"),
            "ip": evt.get("ip"),
            "user_agent": evt.get("user_agent"),
        }

    payload = "\n".join(json.dumps(_serialize(evt), default=str) for evt in records)
    return HttpResponse(content=payload, content_type="text/plain")
