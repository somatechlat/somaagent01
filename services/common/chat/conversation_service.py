"""Conversation management service for ChatService.

Extracted from chat_service.py per VIBE Rule 245 (650-line max).
Handles CRUD operations for conversation records.
"""

from __future__ import annotations

import time
from typing import Optional

from asgiref.sync import sync_to_async

from services.common.chat.metrics import CHAT_LATENCY, CHAT_REQUESTS
from services.common.chat_schemas import Conversation


class ConversationService:
    """Service for conversation CRUD operations.

    Extracted from ChatService to enforce 650-line limit.
    """

    async def create_conversation(
        self, agent_id: str, user_id: str, tenant_id: str
    ) -> Conversation:
        """Create new conversation record in PostgreSQL."""
        from admin.chat.models import Conversation as ConversationModel

        start_time = time.perf_counter()
        try:

            @sync_to_async
            def create_in_db():
                return ConversationModel.objects.create(
                    agent_id=agent_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    status="active",
                    message_count=0,
                )

            db_conv = await create_in_db()
            conversation = Conversation(
                id=str(db_conv.id),
                agent_id=str(db_conv.agent_id),
                user_id=str(db_conv.user_id),
                tenant_id=str(db_conv.tenant_id),
                title=db_conv.title,
                status=db_conv.status,
                message_count=db_conv.message_count,
                created_at=db_conv.created_at,
                updated_at=db_conv.updated_at,
            )
            CHAT_LATENCY.labels(method="create_conversation").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="create_conversation", result="success").inc()
            return conversation
        except Exception:
            CHAT_LATENCY.labels(method="create_conversation").observe(
                time.perf_counter() - start_time
            )
            CHAT_REQUESTS.labels(method="create_conversation", result="error").inc()
            raise

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def get_from_db():
            try:
                return ConversationModel.objects.get(id=conversation_id, user_id=user_id)
            except ConversationModel.DoesNotExist:
                return None

        db_conv = await get_from_db()
        if db_conv is None:
            return None
        return Conversation(
            id=str(db_conv.id),
            agent_id=str(db_conv.agent_id),
            user_id=str(db_conv.user_id),
            tenant_id=str(db_conv.tenant_id),
            title=db_conv.title,
            status=db_conv.status,
            message_count=db_conv.message_count,
            created_at=db_conv.created_at,
            updated_at=db_conv.updated_at,
        )

    async def list_conversations(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """List user's conversations."""
        from admin.chat.models import Conversation as ConversationModel

        @sync_to_async
        def list_from_db():
            return list(
                ConversationModel.objects.filter(
                    user_id=user_id, tenant_id=tenant_id
                ).order_by("-updated_at")[offset : offset + limit]
            )

        db_convs = await list_from_db()
        return [
            Conversation(
                id=str(conv.id),
                agent_id=str(conv.agent_id),
                user_id=str(conv.user_id),
                tenant_id=str(conv.tenant_id),
                title=conv.title,
                status=conv.status,
                message_count=conv.message_count,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
            for conv in db_convs
        ]


__all__ = ["ConversationService"]
