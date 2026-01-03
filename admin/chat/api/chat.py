"""Chat Session API Router - 100% Django ORM.

VIBE COMPLIANT - Django ORM, no legacy session_repository.
Per CANONICAL_USER_JOURNEYS_SRS.md UC-01: Chat with AI Agent
Per login-to-chat-journey design.md Section 6.1
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Query, Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer, get_current_user
from admin.common.exceptions import NotFoundError, ServiceError
from admin.common.responses import paginated_response
from admin.chat.models import Conversation, Message
from admin.core.models import Session

router = Router(tags=["chat"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS - Per SRS UC-01
# =============================================================================


class ChatSessionResponse(BaseModel):
    """Chat session details."""

    session_id: str
    persona_id: Optional[str] = None
    tenant: Optional[str] = None


class ConversationOut(BaseModel):
    """Conversation list item."""

    id: str
    title: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    last_message: Optional[str] = None
    message_count: int = 0
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    """Chat message."""

    id: str
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    metadata: Optional[dict] = None
    created_at: str


class SendMessageRequest(BaseModel):
    """Send message request."""

    content: str
    stream: bool = True
    mode: str = "STD"  # STD, DEV, TRN, ADM, RO, DGR


class SendMessageResponse(BaseModel):
    """Send message response (sync mode)."""

    id: str
    conversation_id: str
    role: str = "assistant"
    content: str
    tokens_used: int = 0
    model: str = ""
    created_at: str


class CreateConversationRequest(BaseModel):
    """Create new conversation."""

    title: Optional[str] = None
    agent_id: Optional[str] = None
    memory_mode: str = "persistent"  # session, persistent


class ConversationDetailOut(BaseModel):
    """Full conversation details."""

    id: str
    title: str
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    memory_mode: str
    message_count: int
    created_at: str
    updated_at: str


# =============================================================================
# CONVERSATIONS - Per SRS UC-02
# =============================================================================


@router.get(
    "/conversations",
    summary="List conversations",
    auth=AuthBearer(),
)
async def list_conversations(
    request,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> dict:
    """List user's conversations.

    Per SRS UC-01 Section 4.3:
    GET /api/v2/chat/conversations

    Per login-to-chat-journey design.md Section 6.2
    """
    from asgiref.sync import sync_to_async

    from django.conf import settings

    user = get_current_user(request)
    user_id = user.sub
    tenant_id = user.tenant_id or settings.SAAS_DEFAULT_TENANT_ID

    @sync_to_async
    def _get_conversations():
        # Query Conversation model
        qs = Conversation.objects.filter(status="active")

        if user_id:
            qs = qs.filter(user_id=user_id)
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)

        qs = qs.order_by("-updated_at")
        total = qs.count()

        offset = (page - 1) * per_page
        items = []

        for conv in qs[offset : offset + per_page]:
            # Get last message
            last_msg = (
                Message.objects.filter(conversation_id=conv.id).order_by("-created_at").first()
            )

            items.append(
                ConversationOut(
                    id=str(conv.id),
                    title=conv.title or f"Conversation {str(conv.id)[:8]}...",
                    agent_id=str(conv.agent_id) if conv.agent_id else None,
                    agent_name=None,  # Would join with Agent model
                    last_message=last_msg.content[:100] if last_msg else None,
                    message_count=conv.message_count,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat(),
                ).model_dump()
            )

        return items, total

    items, total = await _get_conversations()

    return paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=per_page,
    )


@router.post(
    "/conversations",
    summary="Create conversation",
    auth=AuthBearer(),
)
async def create_conversation(request, payload: CreateConversationRequest) -> dict:
    """Create a new conversation.

    Per SRS UC-02 Section 5.3:
    POST /api/v2/chat/conversations

    Per login-to-chat-journey design.md Section 6.2:
    - Creates conversation in PostgreSQL
    - Initializes agent session in SomaBrain
    - Recalls memories from SomaFractalMemory
    """
    from asgiref.sync import sync_to_async
    from services.common.chat_service import get_chat_service

    from django.conf import settings

    user = get_current_user(request)
    user_id = user.sub
    tenant_id = user.tenant_id or settings.SAAS_DEFAULT_TENANT_ID
    agent_id = payload.agent_id or str(uuid4())

    # Create conversation using ChatService
    chat_service = await get_chat_service()

    try:
        conversation = await chat_service.create_conversation(
            agent_id=agent_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )

        # Initialize agent session (local session store)
        try:
            await chat_service.initialize_agent_session(
                agent_id=agent_id,
                conversation_id=conversation.id,
                user_context={
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                },
            )
        except Exception as e:
            # Non-critical - log and continue
            logger.warning(f"Agent session init failed (non-critical): {e}")

        # Recall memories for context
        try:
            memories = await chat_service.recall_memories(
                agent_id=agent_id,
                user_id=user_id,
                query="user context",
                limit=5,
                tenant_id=tenant_id,
            )
            logger.debug(f"Recalled {len(memories)} memories for conversation")
        except Exception as e:
            logger.warning(f"Memory recall failed (non-critical): {e}")

        title = payload.title or f"Conversation {conversation.id[:8]}"

        # Update title if provided
        if payload.title:

            @sync_to_async
            def update_title():
                Conversation.objects.filter(id=conversation.id).update(title=payload.title)

            await update_title()

        return ConversationDetailOut(
            id=conversation.id,
            title=title,
            agent_id=agent_id,
            agent_name=None,
            memory_mode=payload.memory_mode,
            message_count=0,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
        ).model_dump()

    except Exception as e:
        logger.error(f"Conversation creation failed: {e}")
        raise ServiceError(f"Failed to create conversation: {e}")


@router.get(
    "/conversations/{conversation_id}",
    summary="Get conversation",
    auth=AuthBearer(),
)
async def get_conversation(request, conversation_id: str) -> dict:
    """Get conversation details.

    Per SRS UC-01 Section 4.3.
    Per login-to-chat-journey design.md Section 6.2
    """
    from asgiref.sync import sync_to_async

    user = get_current_user(request)
    user_id = user.sub

    @sync_to_async
    def _get():
        try:
            conv = Conversation.objects.get(id=conversation_id)
            # Verify ownership if user_id available
            if user_id and str(conv.user_id) != user_id:
                return None
            return conv
        except Conversation.DoesNotExist:
            return None

    conv = await _get()

    if not conv:
        raise NotFoundError("conversation", conversation_id)

    return ConversationDetailOut(
        id=str(conv.id),
        title=conv.title or f"Conversation {str(conv.id)[:8]}...",
        agent_id=str(conv.agent_id) if conv.agent_id else None,
        agent_name=None,
        memory_mode=conv.memory_mode,
        message_count=conv.message_count,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    ).model_dump()


# =============================================================================
# MESSAGES - Per SRS UC-01
# =============================================================================


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get messages",
    auth=AuthBearer(),
)
async def get_messages(
    request,
    conversation_id: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> dict:
    """Get messages in a conversation.

    Per SRS UC-01 Section 4.3:
    GET /api/v2/chat/messages/{conv_id}

    Per login-to-chat-journey design.md Section 6.2
    """
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _get_messages():
        # Verify conversation exists
        if not Conversation.objects.filter(id=conversation_id).exists():
            return None, 0

        qs = Message.objects.filter(conversation_id=conversation_id).order_by("created_at")
        total = qs.count()

        offset = (page - 1) * per_page
        items = []

        for msg in qs[offset : offset + per_page]:
            items.append(
                MessageOut(
                    id=str(msg.id),
                    conversation_id=str(msg.conversation_id),
                    role=msg.role,
                    content=msg.content,
                    metadata=msg.metadata,
                    created_at=msg.created_at.isoformat(),
                ).model_dump()
            )

        return items, total

    items, total = await _get_messages()

    if items is None:
        raise NotFoundError("conversation", conversation_id)

    return paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=per_page,
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    summary="Send message",
    auth=AuthBearer(),
)
async def send_message(
    request,
    conversation_id: str,
    payload: SendMessageRequest,
) -> dict:
    """Send a message and get AI response.

    Per SRS UC-01 Section 4.3:
    POST /api/v2/chat/messages

    Per login-to-chat-journey design.md Section 6.1:
    - Sends message to SomaBrain
    - Stores messages in database
    - Returns response (sync mode) or initiates stream

    VIBE COMPLIANT:
    - Real ChatService integration
    - Degradation handling ready
    - ZDL via OutboxMessage
    """
    from asgiref.sync import sync_to_async
    from services.common.chat_service import get_chat_service

    user = get_current_user(request)
    user_id = user.sub

    # Verify conversation exists and get agent_id
    @sync_to_async
    def _get_conversation():
        try:
            conv = Conversation.objects.get(id=conversation_id)
            return conv
        except Conversation.DoesNotExist:
            return None

    conv = await _get_conversation()

    if not conv:
        raise NotFoundError("conversation", conversation_id)

    agent_id = str(conv.agent_id)

    # For sync mode, collect full response
    if not payload.stream:
        chat_service = await get_chat_service()

        response_content = []
        token_count = 0

        try:
            async for token in chat_service.send_message(
                conversation_id=conversation_id,
                agent_id=agent_id,
                content=payload.content,
                user_id=user_id,
            ):
                response_content.append(token)
                token_count += 1

            full_response = "".join(response_content)

            # Get the created message
            @sync_to_async
            def get_last_message():
                return (
                    Message.objects.filter(
                        conversation_id=conversation_id,
                        role="assistant",
                    )
                    .order_by("-created_at")
                    .first()
                )

            msg = await get_last_message()

            return SendMessageResponse(
                id=str(msg.id) if msg else str(uuid4()),
                conversation_id=conversation_id,
                role="assistant",
                content=full_response,
                tokens_used=token_count,
                model=msg.model if msg else "",
                created_at=msg.created_at.isoformat() if msg else timezone.now().isoformat(),
            ).model_dump()

        except Exception as e:
            logger.error(f"Message send failed: {e}")
            raise ServiceError(f"Failed to send message: {e}")

    # For stream mode, return acknowledgment (actual streaming via WebSocket)
    message_id = str(uuid4())

    # Store user message
    @sync_to_async
    def store_user_message():
        msg = Message.objects.create(
            conversation_id=conversation_id,
            role="user",
            content=payload.content,
            token_count=len(payload.content.split()),
        )
        Conversation.objects.filter(id=conversation_id).update(
            message_count=Message.objects.filter(conversation_id=conversation_id).count()
        )
        return str(msg.id)

    user_msg_id = await store_user_message()

    return {
        "id": user_msg_id,
        "conversation_id": conversation_id,
        "status": "streaming",
        "message": "Connect to WebSocket for streaming response",
        "websocket_url": f"/ws/chat/{agent_id}",
    }


# =============================================================================
# LEGACY ENDPOINT - Keep for backward compatibility
# =============================================================================


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
