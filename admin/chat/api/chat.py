"""Chat Session API Router - 100% Django ORM.

VIBE COMPLIANT - Django ORM, no legacy session_repository.
"""

from __future__ import annotations

import logging
from typing import Optional

from ninja import Router
from pydantic import BaseModel

from admin.common.exceptions import NotFoundError, ServiceError
from admin.core.models import Session

router = Router(tags=["chat"])
logger = logging.getLogger(__name__)


class ChatSessionResponse(BaseModel):
    """Chat session details."""
    
    session_id: str
    persona_id: Optional[str] = None
    tenant: Optional[str] = None


@router.get("/session/{session_id}", response=ChatSessionResponse, summary="Get chat session")
async def get_chat_session(request, session_id: str) -> dict:
    """Fetch chat session metadata.
    
    Args:
        session_id: The session identifier
    
    Returns:
        Session metadata including persona and tenant
    """
    from asgiref.sync import sync_to_async
    
    try:
        @sync_to_async
        def _get():
            return Session.objects.filter(session_id=session_id).first()
        
        session = await _get()
        
        if session is None:
            raise NotFoundError("session", session_id)
        
        return {
            "session_id": session.session_id,
            "persona_id": session.persona_id,
            "tenant": session.tenant,
        }
    except NotFoundError:
        raise
    except Exception as exc:
        logger.error(f"Session error: {exc}")
        raise ServiceError(f"session_error: {type(exc).__name__}")
