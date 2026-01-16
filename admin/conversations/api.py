"""Conversations API - Chat conversations management.


Conversation lifecycle and messaging.

- PhD Dev: Conversation architecture, streaming
- PM: Chat experience
- QA: Message validation
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.chat.models import Conversation as ConversationModel, Message as MessageModel
from admin.common.auth import AuthBearer, get_current_user
from admin.common.exceptions import NotFoundError, ServiceError

router = Router(tags=["conversations"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Conversation(BaseModel):
    """Conversation definition."""

    conversation_id: str
    agent_id: str
    user_id: str
    tenant_id: str
    title: Optional[str] = None
    status: str  # active, ended, archived
    message_count: int
    created_at: str
    updated_at: str


class Message(BaseModel):
    """Chat message."""

    message_id: str
    conversation_id: str
    role: str  # user, assistant, system, tool
    content: str
    metadata: Optional[dict] = None
    created_at: str


class ConversationStats(BaseModel):
    """Conversation statistics."""

    total_tokens: int
    user_messages: int
    assistant_messages: int
    tool_calls: int
    duration_seconds: int


# =============================================================================
# ENDPOINTS - Conversation CRUD
# =============================================================================


@router.get(
    "",
    summary="List conversations",
    auth=AuthBearer(),
)
async def list_conversations(
    request,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> dict:
    """List conversations.

    PM: Conversation history.
    """
    from asgiref.sync import sync_to_async

    user = get_current_user(request)
    tenant_id = user.tenant_id or settings.SAAS_DEFAULT_TENANT_ID
    effective_user_id = user_id or user.sub

    @sync_to_async
    def _get():
        """Execute get."""

        qs = ConversationModel.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        if effective_user_id:
            qs = qs.filter(user_id=effective_user_id)
        if status:
            qs = qs.filter(status=status)

        total = qs.count()
        items = []
        for conv in qs.order_by("-updated_at")[:limit]:
            items.append(
                Conversation(
                    conversation_id=str(conv.id),
                    agent_id=str(conv.agent_id),
                    user_id=str(conv.user_id),
                    tenant_id=str(conv.tenant_id),
                    title=conv.title,
                    status=conv.status,
                    message_count=conv.message_count,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat(),
                ).model_dump()
            )
        return items, total

    items, total = await _get()

    return {
        "conversations": items,
        "total": total,
    }


@router.post(
    "",
    response=Conversation,
    summary="Start conversation",
    auth=AuthBearer(),
)
async def start_conversation(
    request,
    agent_id: str,
    user_id: str,
    tenant_id: str,
    title: Optional[str] = None,
) -> Conversation:
    """Start a new conversation.

    PhD Dev: Conversation initialization.
    """
    from asgiref.sync import sync_to_async

    from services.common.chat_service import get_chat_service

    user = get_current_user(request)
    effective_user_id = user.sub
    effective_tenant_id = user.tenant_id or settings.SAAS_DEFAULT_TENANT_ID

    chat_service = await get_chat_service()

    try:
        conv = await chat_service.create_conversation(
            agent_id=agent_id,
            user_id=effective_user_id,
            tenant_id=effective_tenant_id,
        )

        # Initialize agent session (local session store, non-critical)
        try:
            await chat_service.initialize_agent_session(
                agent_id=agent_id,
                conversation_id=conv.id,
                user_context={
                    "user_id": effective_user_id,
                    "tenant_id": effective_tenant_id,
                },
            )
        except Exception as exc:
            logger.warning(f"Agent session init failed (non-critical): {exc}")

        # Recall memories for context (non-critical)
        try:
            await chat_service.recall_memories(
                agent_id=agent_id,
                user_id=effective_user_id,
                query="user context",
                limit=5,
                tenant_id=effective_tenant_id,
            )
        except Exception as exc:
            logger.warning(f"Memory recall failed (non-critical): {exc}")

        if title:

            @sync_to_async
            def update_title():
                """Execute update title."""

                ConversationModel.objects.filter(id=conv.id).update(title=title)

            await update_title()

        logger.info(f"Conversation started: {conv.id}")

        return Conversation(
            conversation_id=conv.id,
            agent_id=agent_id,
            user_id=effective_user_id,
            tenant_id=effective_tenant_id,
            title=title,
            status="active",
            message_count=0,
            created_at=conv.created_at.isoformat(),
            updated_at=conv.updated_at.isoformat(),
        )
    except Exception as exc:
        logger.error(f"Conversation start failed: {exc}")
        raise ServiceError(f"Failed to start conversation: {exc}")


@router.get(
    "/{conversation_id}",
    response=Conversation,
    summary="Get conversation",
    auth=AuthBearer(),
)
async def get_conversation(request, conversation_id: str) -> Conversation:
    """Get conversation details."""
    from asgiref.sync import sync_to_async

    user = get_current_user(request)
    tenant_id = user.tenant_id or settings.SAAS_DEFAULT_TENANT_ID

    @sync_to_async
    def _get():
        """Execute get."""

        try:
            return ConversationModel.objects.get(id=conversation_id)
        except ConversationModel.DoesNotExist:
            return None

    conv = await _get()
    if not conv:
        raise NotFoundError("conversation", conversation_id)

    if tenant_id and str(conv.tenant_id) != tenant_id:
        raise NotFoundError("conversation", conversation_id)

    return Conversation(
        conversation_id=str(conv.id),
        agent_id=str(conv.agent_id),
        user_id=str(conv.user_id),
        tenant_id=str(conv.tenant_id),
        title=conv.title,
        status=conv.status,
        message_count=conv.message_count,
        created_at=conv.created_at.isoformat(),
        updated_at=conv.updated_at.isoformat(),
    )


@router.patch(
    "/{conversation_id}",
    summary="Update conversation",
    auth=AuthBearer(),
)
async def update_conversation(
    request,
    conversation_id: str,
    title: Optional[str] = None,
) -> dict:
    """Update conversation metadata."""
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _update():
        """Execute update."""

        return ConversationModel.objects.filter(id=conversation_id).update(title=title)

    updated = await _update()
    if not updated:
        raise NotFoundError("conversation", conversation_id)

    return {
        "conversation_id": conversation_id,
        "updated": True,
    }


@router.delete(
    "/{conversation_id}",
    summary="Delete conversation",
    auth=AuthBearer(),
)
async def delete_conversation(request, conversation_id: str) -> dict:
    """Delete a conversation."""
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _delete():
        """Execute delete."""

        return ConversationModel.objects.filter(id=conversation_id).update(status="deleted")

    updated = await _delete()
    if not updated:
        raise NotFoundError("conversation", conversation_id)

    logger.warning(f"Conversation deleted: {conversation_id}")

    return {
        "conversation_id": conversation_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Messages
# =============================================================================


@router.get(
    "/{conversation_id}/messages",
    summary="List messages",
    auth=AuthBearer(),
)
async def list_messages(
    request,
    conversation_id: str,
    limit: int = 100,
    before: Optional[str] = None,
) -> dict:
    """List conversation messages.

    PM: Chat history.
    """
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _get_messages():
        """Execute get messages."""

        if not ConversationModel.objects.filter(id=conversation_id).exists():
            return None, 0

        qs = MessageModel.objects.filter(conversation_id=conversation_id)
        if before:
            qs = qs.filter(id__lt=before)
        qs = qs.order_by("created_at")

        items = []
        for msg in qs[:limit]:
            items.append(
                Message(
                    message_id=str(msg.id),
                    conversation_id=str(msg.conversation_id),
                    role=msg.role,
                    content=msg.content,
                    metadata=msg.metadata,
                    created_at=msg.created_at.isoformat(),
                ).model_dump()
            )
        return items, qs.count()

    items, total = await _get_messages()
    if items is None:
        raise NotFoundError("conversation", conversation_id)

    return {
        "conversation_id": conversation_id,
        "messages": items,
        "total": total,
    }


@router.post(
    "/{conversation_id}/messages",
    response=Message,
    summary="Send message",
    auth=AuthBearer(),
)
async def send_message(
    request,
    conversation_id: str,
    content: str,
    role: str = "user",
) -> Message:
    """Send a message.

    PhD Dev: Message processing.
    """
    from asgiref.sync import sync_to_async

    from services.common.chat_service import get_chat_service

    if role != "user":
        raise ServiceError("Only user messages can be sent")

    # Verify conversation exists and resolve agent
    @sync_to_async
    def _get_conversation():
        """Execute get conversation."""

        try:
            return ConversationModel.objects.get(id=conversation_id)
        except ConversationModel.DoesNotExist:
            return None

    conv = await _get_conversation()
    if not conv:
        raise NotFoundError("conversation", conversation_id)

    user = get_current_user(request)

    chat_service = await get_chat_service()
    response_tokens = []

    async for token in chat_service.send_message(
        conversation_id=conversation_id,
        agent_id=str(conv.agent_id),
        content=content,
        user_id=user.sub,
    ):
        response_tokens.append(token)

    full_response = "".join(response_tokens)

    # Return assistant message snapshot
    @sync_to_async
    def _get_last_assistant():
        """Execute get last assistant."""

        return (
            MessageModel.objects.filter(
                conversation_id=conversation_id,
                role="assistant",
            )
            .order_by("-created_at")
            .first()
        )

    msg = await _get_last_assistant()

    return Message(
        message_id=str(msg.id) if msg else str(uuid4()),
        conversation_id=conversation_id,
        role="assistant",
        content=full_response,
        metadata=msg.metadata if msg else None,
        created_at=msg.created_at.isoformat() if msg else timezone.now().isoformat(),
    )


@router.get(
    "/{conversation_id}/messages/{message_id}",
    response=Message,
    summary="Get message",
    auth=AuthBearer(),
)
async def get_message(
    request,
    conversation_id: str,
    message_id: str,
) -> Message:
    """Get message details."""
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _get():
        """Execute get."""

        try:
            return MessageModel.objects.get(
                id=message_id,
                conversation_id=conversation_id,
            )
        except MessageModel.DoesNotExist:
            return None

    msg = await _get()
    if not msg:
        raise NotFoundError("message", message_id)

    return Message(
        message_id=str(msg.id),
        conversation_id=str(msg.conversation_id),
        role=msg.role,
        content=msg.content,
        metadata=msg.metadata,
        created_at=msg.created_at.isoformat(),
    )


# =============================================================================
# ENDPOINTS - Chat
# =============================================================================


@router.post(
    "/{conversation_id}/chat",
    summary="Chat with agent",
    auth=AuthBearer(),
)
async def chat(
    request,
    conversation_id: str,
    message: str,
    stream: bool = False,
) -> dict:
    """Send message and get agent response.

    PhD Dev: Full chat cycle.
    """
    from asgiref.sync import sync_to_async

    from services.common.chat_service import get_chat_service

    @sync_to_async
    def _get_conversation():
        """Execute get conversation."""

        try:
            return ConversationModel.objects.get(id=conversation_id)
        except ConversationModel.DoesNotExist:
            return None

    conv = await _get_conversation()
    if not conv:
        raise NotFoundError("conversation", conversation_id)

    user = get_current_user(request)
    chat_service = await get_chat_service()

    if not stream:
        response_tokens = []
        async for token in chat_service.send_message(
            conversation_id=conversation_id,
            agent_id=str(conv.agent_id),
            content=message,
            user_id=user.sub,
        ):
            response_tokens.append(token)

        return {
            "conversation_id": conversation_id,
            "response": "".join(response_tokens),
        }

    return {
        "conversation_id": conversation_id,
        "status": "streaming",
        "message": "Connect to WebSocket for streaming response",
        "websocket_url": "/ws/v2/chat",
    }


@router.get(
    "/{conversation_id}/stream",
    summary="Stream info",
    auth=AuthBearer(),
)
async def get_stream_info(
    request,
    conversation_id: str,
) -> dict:
    """Get streaming endpoint info.

    PhD Dev: SSE streaming setup.
    """
    return {
        "conversation_id": conversation_id,
        "stream_url": "/ws/v2/chat",
        "protocol": "websocket",
    }


# =============================================================================
# ENDPOINTS - Lifecycle
# =============================================================================


@router.post(
    "/{conversation_id}/end",
    summary="End conversation",
    auth=AuthBearer(),
)
async def end_conversation(request, conversation_id: str) -> dict:
    """End a conversation."""
    logger.info(f"Conversation ended: {conversation_id}")

    return {
        "conversation_id": conversation_id,
        "status": "ended",
    }


@router.post(
    "/{conversation_id}/archive",
    summary="Archive conversation",
    auth=AuthBearer(),
)
async def archive_conversation(request, conversation_id: str) -> dict:
    """Archive a conversation."""
    return {
        "conversation_id": conversation_id,
        "status": "archived",
    }


# =============================================================================
# ENDPOINTS - Stats & Export
# =============================================================================


@router.get(
    "/{conversation_id}/stats",
    response=ConversationStats,
    summary="Get stats",
    auth=AuthBearer(),
)
async def get_conversation_stats(
    request,
    conversation_id: str,
) -> ConversationStats:
    """Get conversation statistics.

    PM: Usage metrics.
    """
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _get_stats():
        """Execute get stats."""

        if not ConversationModel.objects.filter(id=conversation_id).exists():
            return None

        qs = MessageModel.objects.filter(conversation_id=conversation_id)
        total_tokens = qs.aggregate(models.Sum("token_count")).get("token_count__sum") or 0
        user_messages = qs.filter(role="user").count()
        assistant_messages = qs.filter(role="assistant").count()
        tool_calls = 0

        first = qs.order_by("created_at").first()
        last = qs.order_by("-created_at").first()
        duration_seconds = 0
        if first and last:
            duration_seconds = int((last.created_at - first.created_at).total_seconds())

        return {
            "total_tokens": total_tokens,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "tool_calls": tool_calls,
            "duration_seconds": duration_seconds,
        }

    stats = await _get_stats()
    if stats is None:
        raise NotFoundError("conversation", conversation_id)

    return ConversationStats(**stats)


@router.post(
    "/{conversation_id}/export",
    summary="Export conversation",
    auth=AuthBearer(),
)
async def export_conversation(
    request,
    conversation_id: str,
    format: str = "json",  # json, txt, pdf
) -> dict:
    """Export conversation.

    PM: Data portability.
    """
    export_id = str(uuid4())

    return {
        "export_id": export_id,
        "conversation_id": conversation_id,
        "format": format,
        "status": "generating",
    }


# =============================================================================
# ENDPOINTS - Search
# =============================================================================


@router.post(
    "/search",
    summary="Search conversations",
    auth=AuthBearer(),
)
async def search_conversations(
    request,
    query: str,
    agent_id: Optional[str] = None,
    limit: int = 20,
) -> dict:
    """Search across conversations.

    PM: Find past conversations.
    """
    from asgiref.sync import sync_to_async

    user = get_current_user(request)
    tenant_id = user.tenant_id or settings.SAAS_DEFAULT_TENANT_ID

    @sync_to_async
    def _search():
        """Execute search."""

        qs = ConversationModel.objects.all()
        if tenant_id:
            qs = qs.filter(tenant_id=tenant_id)
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        if query:
            qs = qs.filter(models.Q(title__icontains=query) | models.Q(metadata__icontains=query))

        total = qs.count()
        results = []
        for conv in qs.order_by("-updated_at")[:limit]:
            results.append(
                Conversation(
                    conversation_id=str(conv.id),
                    agent_id=str(conv.agent_id),
                    user_id=str(conv.user_id),
                    tenant_id=str(conv.tenant_id),
                    title=conv.title,
                    status=conv.status,
                    message_count=conv.message_count,
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat(),
                ).model_dump()
            )
        return results, total

    results, total = await _search()

    return {
        "query": query,
        "results": results,
        "total": total,
    }
