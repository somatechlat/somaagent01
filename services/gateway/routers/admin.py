"""Admin router - real implementations only (VIBE compliant)."""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, Response

from services.common.audit_store import from_env as get_audit_store
from services.common.authorization import _require_admin_scope, authorize_request

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/ping")
async def ping() -> dict[str, str]:
    """Health check endpoint - no auth required."""
    return {"status": "ok"}


@router.get("/audit/export")
async def audit_export(
    request: Request,
    action: Optional[str] = Query(None, description="Filter by action type"),
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    tenant: Optional[str] = Query(None, description="Filter by tenant"),
    limit: int = Query(1000, ge=1, le=10000, description="Max records to return"),
    after_id: Optional[int] = Query(None, description="Pagination cursor"),
):
    """
    Export audit logs as newline-delimited JSON from real PostgreSQL AuditStore.
    
    Requires admin authorization.
    
    Args:
        request: FastAPI request for authorization
        action: Filter by specific action (e.g., "llm.invoke")
        session_id: Filter by session ID
        tenant: Filter by tenant
        limit: Maximum number of records (default 1000, max 10000)
        after_id: Return records after this ID for pagination
    
    Returns:
        Newline-delimited JSON response of real audit records from database
    
    Raises:
        HTTPException 403: If admin authorization fails
        HTTPException 503: If AuditStore is unavailable
    """
    # Authorize request - require admin scope
    auth = await authorize_request(request, {"action": "audit.export"})
    _require_admin_scope(auth)
    
    # Get real AuditStore instance
    store = get_audit_store()
    
    try:
        # Query real audit records from PostgreSQL
        records = await store.list(
            action=action,
            session_id=session_id,
            tenant=tenant,
            limit=limit,
            after_id=after_id,
        )
    except Exception as exc:
        LOGGER.error("AuditStore query failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Audit store unavailable"
        ) from exc
    
    # Format as newline-delimited JSON from real database records
    lines = []
    for r in records:
        lines.append(json.dumps({
            "id": r.id,
            "timestamp": r.ts.isoformat() if r.ts else None,
            "action": r.action,
            "resource": r.resource,
            "details": r.details,
            "user": r.subject,
            "session_id": r.session_id,
            "tenant": r.tenant,
            "request_id": r.request_id,
            "trace_id": r.trace_id,
            "target_id": r.target_id,
            "ip": r.ip,
            "user_agent": r.user_agent,
        }))
    
    return Response(
        content="\n".join(lines),
        media_type="text/plain"
    )
