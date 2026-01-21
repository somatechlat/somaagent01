"""Message endpoints for conversation messages.

Handles message CRUD operations within conversations.

- PhD Dev: Message processing
- PM: Chat history
- QA: Message validation
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from asgiref.sync import sync_to_async
from django.utils import timezone
from ninja import Router

from admin.chat.models import Conversation as ConversationModel, Message as MessageModel
from admin.common.auth import AuthBearer, get_current_user
from admin.common.exceptions import NotFoundError, ServiceError
from admin.conversations.schemas import Message

router = Router(tags=["messages"])
logger = logging.getLogger(__name__)


# =============================================================================
# MESSAGE ENDPOINTS
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
