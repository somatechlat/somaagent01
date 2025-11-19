"""
Session router – extracted from the original gateway monolith.

Provides the `/v1/sessions` endpoint used by the UI and tests. The implementation
mirrors the original behavior (including the default‑welcome‑session seeding)
but lives in a dedicated, testable module.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

# Import the data‑store abstractions from the original gateway.
from services.common.postgres_session_store import (
    PostgresSessionStore,
    get_session_store,
)

# Re‑use the Pydantic model defined in the monolith for compatibility.
from services.gateway.main import SessionSummary

LOGGER = logging.getLogger(__name__)

router = APIRouter()


@router.get("/v1/sessions", response_model=List[SessionSummary])
async def list_sessions_endpoint(
    store: PostgresSessionStore = Depends(get_session_store),
    limit: int = Query(50, ge=1, le=200),
    tenant: str | None = Query(None, description="Filter sessions by tenant identifier"),
):
    """List sessions, seeding a default welcome session when none exist.

    The original gateway created a welcome *assistant.final* event on first
    load when the store returned no sessions. This behavior is preserved so
    the UI and integration tests continue to work unchanged.
    """
    # Retrieve session envelopes from the store.
    envelopes = await store.list_sessions(limit=limit, tenant=tenant)

    # If the store is empty and no tenant filter is applied, create a welcome
    # session to match the legacy UI expectation.
    if not envelopes and tenant is None:
        try:
            sid = str(uuid.uuid4())
            welcome_event = {
                "session_id": sid,
                "role": "assistant",
                "type": "assistant.final",
                "message": "\ud83d\udc4b Welcome to Soma Agent. How can I help today?",
                "metadata": {"subject": "New chat"},
            }
            await store.append_event(sid, welcome_event)
            # Re‑query after seeding.
            envelopes = await store.list_sessions(limit=limit, tenant=tenant)
        except Exception as exc:
            LOGGER.debug("Failed to seed default welcome session", exc_info=True)

    # Convert envelopes to the SessionSummary model expected by the API.
    summaries: List[SessionSummary] = []
    for envelope in envelopes:
        # Normalise metadata and analysis fields – they may be stored as JSON strings.
        md = envelope.metadata
        if isinstance(md, str):
            try:
                from json import loads as _loads
                parsed = _loads(md)
                md = parsed if isinstance(parsed, dict) else {}
            except Exception:
                md = {}
        elif not isinstance(md, dict):
            md = {}

        an = envelope.analysis
        if isinstance(an, str):
            try:
                from json import loads as _loads
                parsed = _loads(an)
                an = parsed if isinstance(parsed, dict) else {}
            except Exception:
                an = {}
        elif not isinstance(an, dict):
            an = {}

        summaries.append(
            SessionSummary(
                session_id=str(envelope.session_id),
                persona_id=envelope.persona_id,
                tenant=envelope.tenant,
                subject=envelope.subject,
                issuer=envelope.issuer,
                scope=envelope.scope,
                metadata=md,
                analysis=an,
                created_at=envelope.created_at,
                updated_at=envelope.updated_at,
            )
        )

    return summaries
