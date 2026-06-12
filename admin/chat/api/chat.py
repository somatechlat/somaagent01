"""Chat Session API Router - 100% Django ORM.


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

from admin.chat.models import Conversation, Message
from admin.common.auth import AuthBearer, get_current_user
from admin.common.exceptions import NotFoundError, ServiceError
from admin.common.responses import paginated_response
from admin.core.models import Session
from admin.common.messages import ErrorCode, SuccessCode, get_message

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
    """Chat message (metadata only - content in SomaBrain)."""

    id: str
    conversation_id: str
    role: str  # user, assistant, system
    coordinate: str  # SomaBrain coordinate reference
    token_count: int = 0
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
    tenant_id = user.effective_tenant_id or settings.AAAS_DEFAULT_TENANT_ID

    @sync_to_async
    def _get_conversations():
        # Query Conversation model
        """Execute get conversations."""

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
                    last_message=f"{conv.message_count} messages" if last_msg else None,
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
    from django.conf import settings

    from admin.core.chat_orchestrator import get_chat_orchestrator

    user = get_current_user(request)
    user_id = user.sub
    tenant_id = user.effective_tenant_id or settings.AAAS_DEFAULT_TENANT_ID
    agent_id = payload.agent_id or str(uuid4())

    orchestrator = await get_chat_orchestrator()

    try:
        conversation = await orchestrator.create_conversation(
            agent_id=agent_id,
            user_id=user_id,
            tenant_id=tenant_id,
            title=payload.title,
        )

        try:
            await orchestrator.initialize_session(
                agent_id=agent_id,
                conversation_id=conversation.id,
                user_context={
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                },
            )
        except Exception as e:
            logger.warning('Agent session init failed (non-critical): %s', e)

        title = payload.title or f"Conversation {conversation.id[:8]}"

        # Update title if provided
        if payload.title:

            @sync_to_async
            def update_title():
                """Execute update title."""
                from django.db import transaction
                with transaction.atomic():
                    Conversation.objects.filter(id=conversation.id).update(title=payload.title)

            await update_title()

        return ConversationDetailOut(
            id=conversation.id,
            title=conversation.title,
            agent_id=agent_id,
            agent_name=None,
            memory_mode=payload.memory_mode,
            message_count=0,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
        ).model_dump()

    except Exception as e:
        logger.error('Conversation creation failed: %s', e)
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
        """Execute get."""

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
    from django.conf import settings

    user = get_current_user(request)
    user_id = user.sub
    tenant_id = user.effective_tenant_id or settings.AAAS_DEFAULT_TENANT_ID

    @sync_to_async
    def _get_messages():
        # Verify conversation exists AND belongs to current user/tenant
        """Execute get messages."""

        if not Conversation.objects.filter(
            id=conversation_id, user_id=user_id, tenant_id=tenant_id
        ).exists():
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
                    coordinate=msg.coordinate,  # SomaBrain reference
                    token_count=msg.token_count,
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


    - Real ChatService integration
    - Degradation handling ready
    - ZDL via OutboxMessage
    """
    from asgiref.sync import sync_to_async
    from django.conf import settings

    from admin.core.chat_orchestrator import ChatTurn, get_chat_orchestrator

    user = get_current_user(request)
    user_id = user.sub
    tenant_id = user.effective_tenant_id or settings.AAAS_DEFAULT_TENANT_ID

    orchestrator = await get_chat_orchestrator()

    conv = await orchestrator.get_conversation(conversation_id, user_id)
    if not conv:
        raise NotFoundError("conversation", conversation_id)

    agent_id = str(conv.agent_id)

    # Load capsule for the orchestrator pipeline
    from admin.core.models import Capsule

    @sync_to_async
    def _get_capsule():
        return Capsule.objects.filter(id=agent_id).first()

    capsule = await _get_capsule()
    if not capsule:
        raise ServiceError("Agent capsule not found")

    # Sync mode: run full 12-phase pipeline and return complete response
    if not payload.stream:
        turn = ChatTurn(
            capsule=capsule,
            user_id=user_id,
            tenant_id=tenant_id or "",
            user_message=payload.content,
            conversation_id=conversation_id,
        )
        result = await orchestrator.process_turn(turn)

        if result.errors:
            raise ServiceError(f"Chat failed: {result.errors[0]}")

        return SendMessageResponse(
            id=str(uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=result.response,
            tokens_used=result.context_tokens,
            model=result.model_used,
            created_at=timezone.now().isoformat(),
        ).model_dump()

    # Stream mode: return WebSocket endpoint for true streaming
    stream_request_id = str(uuid4())
    return {
        "id": stream_request_id,
        "conversation_id": conversation_id,
        "status": "streaming",
        "message": get_message(SuccessCode.WEBSOCKET_STREAMING),
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
            """Execute get."""

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
        logger.error('Session error: %s', exc)
        raise ServiceError(f"session_error: {type(exc).__name__}")
