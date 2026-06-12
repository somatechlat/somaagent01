"""ChatService facade — thin wrapper around V3ChatOrchestrator.

Provides the legacy ChatService interface expected by integration tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, List, Optional

from asgiref.sync import sync_to_async

from admin.core.chat_orchestrator import ChatTurn, V3ChatOrchestrator
from admin.core.models import Capsule


@dataclass
class Message:
    """Simple message DTO for test compatibility."""

    id: str
    conversation_id: str
    role: str
    content: str
    token_count: int = 0
    created_at: Optional[str] = None


class ChatService:
    """Production chat service backed by V3ChatOrchestrator."""

    def __init__(self, somabrain_url: str = "", timeout: float = 30.0) -> None:
        self._orchestrator = V3ChatOrchestrator()
        self._somabrain_url = somabrain_url
        self._timeout = timeout

    async def create_conversation(
        self,
        agent_id: str,
        user_id: str,
        tenant_id: str,
    ) -> Any:
        """Create a new conversation."""
        return await self._orchestrator.create_conversation(agent_id, user_id, tenant_id)

    async def send_message(
        self,
        conversation_id: str,
        agent_id: str,
        content: str,
        user_id: str,
    ) -> AsyncIterator[str]:
        """Stream an assistant response for the given message."""
        capsule = await self._load_capsule(agent_id)
        if not capsule:
            raise ValueError(f"Capsule not found: {agent_id}")

        turn = ChatTurn(
            capsule=capsule,
            user_id=user_id,
            tenant_id="",
            user_message=content,
            conversation_id=conversation_id,
        )

        async for token in self._orchestrator.stream_turn(turn):
            yield token

    async def get_messages(self, conversation_id: str, user_id: str) -> List[Message]:
        """Retrieve messages for a conversation."""
        from admin.chat.models import Message as MessageModel

        @sync_to_async
        def _load():
            qs = MessageModel.objects.filter(conversation_id=conversation_id).order_by("created_at")
            return [
                Message(
                    id=str(m.id),
                    conversation_id=str(m.conversation_id),
                    role=m.role,
                    content=m.content,
                    token_count=m.token_count or 0,
                    created_at=m.created_at.isoformat() if m.created_at else None,
                )
                for m in qs
            ]

        return await _load()

    async def recall_memories(
        self,
        agent_id: str,
        user_id: str,
        query: str,
        limit: int,
        tenant_id: str,
    ) -> List[dict]:
        """Recall memories from SomaBrain."""
        from admin.core.somabrain_client import SomaBrainClient

        client = await SomaBrainClient.get_async()
        if client:
            results = await client.recall(query=query, top_k=limit, tenant=tenant_id)
            return results or []
        return []

    async def _load_capsule(self, capsule_id: str) -> Optional[Any]:
        """Load a Capsule by ID."""

        @sync_to_async
        def _get():
            return Capsule.objects.filter(id=capsule_id).first()

        return await _get()
