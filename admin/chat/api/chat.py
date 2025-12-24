"""Chat Session API Router - 100% Django.

VIBE COMPLIANT - Django patterns, centralized settings, no legacy cfg.
"""

from __future__ import annotations

import logging
from typing import Optional

from django.conf import settings
from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import NotFoundError, ServiceError

router = Router(tags=["chat"])
logger = logging.getLogger(__name__)


class ChatSessionResponse(BaseModel):
    """Chat session details."""
    
    session_id: str
    persona_id: Optional[str] = None
    tenant: Optional[str] = None


async def _get_session_store():
    """Get PostgreSQL session store using Django settings."""
    from services.common.session_repository import ensure_schema, PostgresSessionStore
    
    store = PostgresSessionStore(settings.DATABASE_DSN)
    await ensure_schema(store)
    return store


@router.get("/session/{session_id}", response=ChatSessionResponse, summary="Get chat session")
async def get_chat_session(request, session_id: str) -> dict:
    """Fetch chat session metadata.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Session metadata including persona and tenant
    """
    try:
        store = await _get_session_store()
        envelope = await store.get_envelope(session_id)
        
        if envelope is None:
            raise NotFoundError("session", session_id)
        
        return {
            "session_id": session_id,
            "persona_id": envelope.persona_id,
            "tenant": envelope.tenant,
        }
    except NotFoundError:
        raise
    except Exception as exc:
        logger.error(f"Session error: {exc}")
        raise ServiceError(f"session_error: {type(exc).__name__}")
