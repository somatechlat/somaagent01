"""General admin API endpoints.

Migrated from: services/gateway/routers/admin.py
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from django.http import HttpRequest, HttpResponse
from ninja import Router

from admin.common.auth import RoleRequired

router = Router(tags=["admin-general"])
logger = logging.getLogger(__name__)


@router.get("/ping", summary="Ping the server")
async def ping() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.get(
    "/audit/export",
    summary="Export audit logs as NDJSON",
    auth=RoleRequired("admin", "saas_admin"),
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
    from integrations.repositories import get_audit_store

    store = get_audit_store()
    try:
        await store.ensure_schema()
    except Exception:
        logger.debug("audit ensure_schema failed", exc_info=True)

    records = await store.list(action=action, limit=1000)

    def _serialize(evt) -> dict:
        """Execute serialize.

            Args:
                evt: The evt.
            """

        return {
            "id": getattr(evt, "id", None),
            "timestamp": getattr(evt, "ts", None).isoformat() if getattr(evt, "ts", None) else None,
            "action": getattr(evt, "action", None),
            "resource": getattr(evt, "resource", None),
            "session_id": getattr(evt, "session_id", None),
            "tenant": getattr(evt, "tenant", None),
            "details": getattr(evt, "details", None),
            "trace_id": getattr(evt, "trace_id", None),
            "request_id": getattr(evt, "request_id", None),
            "ip": getattr(evt, "ip", None),
            "user_agent": getattr(evt, "user_agent", None),
        }

    payload = "\n".join(json.dumps(_serialize(evt), default=str) for evt in records)
    return HttpResponse(content=payload, content_type="text/plain")