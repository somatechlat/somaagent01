"""Admin router skeleton."""

from __future__ import annotations

from fastapi import APIRouter, Query
import json
import time
from typing import Optional

from integrations.repositories import get_audit_store

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/audit/export")
async def audit_export(action: Optional[str] = Query(None)):
    """
    Export audit logs as newline-delimited JSON.
    
    Args:
        action: Filter by specific action (e.g., "llm.invoke")
    
    Returns:
        Newline-delimited JSON response of audit records
    """
    from fastapi import Response

    store = get_audit_store()
    try:
        await store.ensure_schema()
    except Exception:
        # If schema ensure fails we still attempt list; log at debug level.
        import logging

        logging.getLogger(__name__).debug("audit ensure_schema failed", exc_info=True)

    records = await store.list(action=action, limit=1000)

    def _serialize(evt) -> dict:
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
    return Response(content=payload, media_type="text/plain")
