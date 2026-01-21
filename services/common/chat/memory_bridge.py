"""Memory bridge for ChatService.

Extracted from chat_service.py per VIBE Rule 245 (650-line max).
Provides thin delegation layer to chat_memory.py.
"""

from __future__ import annotations

from typing import Optional

from services.common.chat_schemas import Memory


class ChatMemoryBridge:
    """Bridge to memory operations via SomaBrain.

    Extracted from ChatService to enforce 650-line limit.
    Delegates all operations to chat_memory.py.
    """

    async def recall_memories(
        self,
        agent_id: str,
        user_id: str,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> list[Memory]:
        """Recall relevant memories via SomaBrain."""
        from services.common.chat_memory import recall_memories

        return await recall_memories(agent_id, user_id, query, limit, tenant_id)

    async def store_memory(
        self,
        agent_id: str,
        user_id: str,
        content: str,
        metadata: dict,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Store interaction via SomaBrain."""
        from services.common.chat_memory import store_memory

        await store_memory(agent_id, user_id, content, metadata, tenant_id)

    async def store_interaction(
        self,
        *,
        agent_id: str,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        tenant_id: Optional[str] = None,
        model: Optional[str] = None,
        latency_ms: Optional[int] = None,
    ) -> None:
        """Store a full interaction in memory via SomaBrain."""
        from services.common.chat_memory import store_interaction

        await store_interaction(
            agent_id=agent_id,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=assistant_response,
            tenant_id=tenant_id,
            model=model,
            latency_ms=latency_ms,
        )


__all__ = ["ChatMemoryBridge"]
