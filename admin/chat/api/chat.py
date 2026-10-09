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
from admin.common.messages import get_message, SuccessCode
from admin.common.responses import paginated_response
from admin.core.models import Session
from services.common.authorization import authorize

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
    """Chat message.

    ``content`` is the turn text (``Message.content`` — the conversation
    transcript, ARCH-INVARIANTS §3). ``coordinate`` is the seam coordinate
    for the semantic-memory twin of this turn.
    """

    id: str
    conversation_id: str
    role: str  # user, assistant, system
    coordinate: str  # SomaBrain coordinate reference
    content: str = ""
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


class RenameConversationRequest(BaseModel):
    """Rename a conversation (CH-07 manual naming)."""

    title: str


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
    await authorize(request, action="resource:conversation_read", resource="chat")
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
    await authorize(request, action="resource:conversation_create", resource="chat")
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
            logger.warning("Agent session init failed (non-critical): %s", e)

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
        logger.error("Conversation creation failed: %s", e)
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
    await authorize(request, action="resource:conversation_read", resource="chat")
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


class ConversationRenameIn(BaseModel):
    """Rename conversation payload."""

    title: str


@router.patch(
    "/conversations/{conversation_id}",
    summary="Rename conversation",
    auth=AuthBearer(),
)
async def rename_conversation(request, conversation_id: str, payload: ConversationRenameIn) -> dict:
    """Rename a conversation (C6 / CH-07)."""
    await authorize(request, action="resource:conversation_update", resource="chat")
    from asgiref.sync import sync_to_async

    user = get_current_user(request)
    title = (payload.title or "").strip()
    if not title:
        raise ServiceError("title is required")

    @sync_to_async
    def _rename():
        """Execute rename."""
        try:
            conv = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None
        if user.sub and str(conv.user_id) != user.sub:
            return None
        conv.title = title[:200]
        conv.save(update_fields=["title", "updated_at"])
        return conv

    conv = await _rename()
    if not conv:
        raise NotFoundError("conversation", conversation_id)
    return {"id": str(conv.id), "title": conv.title}


@router.delete(
    "/conversations/{conversation_id}",
    summary="Delete conversation",
    auth=AuthBearer(),
)
async def delete_conversation(request, conversation_id: str) -> dict:
    """Hard-delete a conversation and its messages (C6 / CH-08)."""
    await authorize(request, action="resource:conversation_delete", resource="chat")
    from asgiref.sync import sync_to_async

    user = get_current_user(request)

    @sync_to_async
    def _delete():
        """Execute delete."""
        try:
            conv = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None
        if user.sub and str(conv.user_id) != user.sub:
            return None
        Message.objects.filter(conversation_id=conv.id).delete()
        conv.delete()
        return True

    deleted = await _delete()
    if not deleted:
        raise NotFoundError("conversation", conversation_id)
    return {"id": conversation_id, "deleted": True}


@router.get(
    "/conversations/{conversation_id}/export",
    summary="Export conversation as markdown",
    auth=AuthBearer(),
)
async def export_conversation(request, conversation_id: str) -> dict:
    """Export conversation transcript (C6 / CH-08)."""
    await authorize(request, action="resource:conversation_view_history", resource="chat")
    from asgiref.sync import sync_to_async

    user = get_current_user(request)

    @sync_to_async
    def _load():
        """Load conversation + messages."""
        try:
            conv = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return None
        if user.sub and str(conv.user_id) != user.sub:
            return None
        msgs = list(
            Message.objects.filter(conversation_id=conv.id).order_by("created_at")
        )
        return conv, msgs

    loaded = await _load()
    if not loaded:
        raise NotFoundError("conversation", conversation_id)

    conv, msgs = loaded
    lines = [f"# {conv.title or 'Conversation'}", ""]
    for m in msgs:
        role = getattr(m, "role", getattr(m, "sender", "user"))
        content = getattr(m, "content", "") or ""
        lines.append(f"## {role}")
        lines.append(content)
        lines.append("")
    return {
        "id": str(conv.id),
        "title": conv.title or "Conversation",
        "format": "markdown",
        "content": "\n".join(lines),
        "message_count": len(msgs),
    }


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
    await authorize(request, action="resource:conversation_read", resource="chat")
    from asgiref.sync import sync_to_async
    from django.conf import settings

    user = get_current_user(request)
    user_id = user.sub
    tenant_id = user.effective_tenant_id or settings.AAAS_DEFAULT_TENANT_ID

    @sync_to_async
    def _get_messages():
        # Verify conversation exists AND belongs to current user/tenant
        """Execute get messages."""
        import uuid as uuid_mod

        # Short hex (e.g. conversation *title* suffix) is not a conversation id.
        # Return not-found instead of a 500 from Django UUIDField.
        try:
            uuid_mod.UUID(str(conversation_id))
        except (ValueError, AttributeError, TypeError):
            return None, 0

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
                    coordinate=msg.coordinate,  # seam coordinate
                    content=msg.content or "",  # turn text (transcript)
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
    await authorize(request, action="resource:conversation_send_message", resource="chat")
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

    # Load capsule via Agent → primary_capsule (Agent ID ≠ Capsule ID)
    from admin.aaas.models import Agent
    from admin.core.models import Capsule

    @sync_to_async
    def _get_capsule():
        # Try direct Capsule lookup first (backward compat)
        capsule = Capsule.objects.filter(id=agent_id).first()
        if capsule:
            return capsule
        # Agent lookup: conversation stores Agent ID, capsule is on Agent
        agent = Agent.objects.filter(id=agent_id).select_related("primary_capsule").first()
        if agent and agent.primary_capsule:
            return agent.primary_capsule
        # Fallback: any active capsule for this tenant
        if tenant_id:
            return Capsule.objects.filter(tenant_id=tenant_id, status="active").first()
        return None

    capsule = await _get_capsule()
    if not capsule:
        raise ServiceError("Agent capsule not found")

    # Sync mode: run full 12-phase pipeline and return complete response
    if not payload.stream:
        turn = ChatTurn(
            capsule=capsule,
            roles=_principal_roles(request),
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


@router.get("/session/{session_id}", response=ChatSessionResponse, summary="Get chat session", auth=AuthBearer())
async def get_chat_session(request, session_id: str) -> dict:
    """Fetch chat session metadata.

    Args:
        session_id: The session identifier

    Returns:
        Session metadata including persona and tenant
    """
    await authorize(request, action="resource:chat_view", resource="chat")
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
        logger.error("Session error: %s", exc)
        raise ServiceError(f"session_error: {type(exc).__name__}")


def _principal_roles(request) -> list:
    """Roles the authenticated principal holds, from the token.

    ``TokenPayload.realm_access`` is the one place roles are surfaced from the
    identity record. Reading them from anywhere else is a second authority.
    """
    auth = getattr(request, "auth", None)
    if auth is None:
        return []
    realm = getattr(auth, "realm_access", None) or {}
    if isinstance(realm, dict):
        return list(realm.get("roles") or [])
    return list(getattr(auth, "roles", None) or [])
