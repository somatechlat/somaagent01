"""ChatService — Facade over split modules.

VIBE Rule 245 Compliant: Original 898 lines → ~150 lines (facade only).

This module provides backward compatibility by delegating to extracted services:
- ConversationService: create, get, list conversations
- MessageService: send_message (core LLM flow)
- SessionManager: initialize_agent_session
- ChatMemoryBridge: recall, store memory
- TitleGenerator: generate_title

Original functionality is preserved via composition.
"""

from __future__ import annotations

import logging
from typing import AsyncIterator, Optional

import httpx

from services.common.chat.conversation_service import ConversationService
from services.common.chat.memory_bridge import ChatMemoryBridge
from services.common.chat.message_service import MessageService
from services.common.chat.session_manager import SessionManager
from services.common.chat.title_generator import TitleGenerator
from services.common.chat_schemas import AgentSession, Conversation, Memory, Message

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat operations with SomaBrain integration.

    VIBE Rule 245 Compliant: Facade over extracted service modules.
    Original 898-line file split into 5 modules, each < 650 lines.
    """

    def __init__(
        self,
        somabrain_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """Initialize ChatService.

        Memory operations use SomaBrainClient directly (no direct SFM access).
        """
        from django.conf import settings

        self.somabrain_url = somabrain_url or getattr(
            settings, "SOMABRAIN_URL", "http://localhost:9696"
        )
        self.timeout = timeout
        self._http_client: Optional[httpx.AsyncClient] = None

        # Composed services
        self._conversation_service = ConversationService()
        self._message_service = MessageService(timeout=timeout)
        self._session_manager = SessionManager()
        self._memory_bridge = ChatMemoryBridge()
        self._title_generator = TitleGenerator()

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()

    # =========================================================================
    # CONVERSATION MANAGEMENT (delegated)
    # =========================================================================

    async def create_conversation(
        self, agent_id: str, user_id: str, tenant_id: str
    ) -> Conversation:
        """Create new conversation record in PostgreSQL."""
        return await self._conversation_service.create_conversation(
            agent_id, user_id, tenant_id
        )

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        return await self._conversation_service.get_conversation(
            conversation_id, user_id
        )

    async def list_conversations(
        self,
        user_id: str,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        """List user's conversations."""
        return await self._conversation_service.list_conversations(
            user_id, tenant_id, limit, offset
        )

    # =========================================================================
    # SESSION MANAGEMENT (delegated)
    # =========================================================================

    async def initialize_agent_session(
        self, agent_id: str, conversation_id: str, user_context: dict
    ) -> AgentSession:
        """Initialize agent session in local session store."""
        return await self._session_manager.initialize_agent_session(
            agent_id, conversation_id, user_context
        )

    # =========================================================================
    # MESSAGE SENDING (delegated)
    # =========================================================================

    async def send_message(
        self, conversation_id: str, agent_id: str, content: str, user_id: str
    ) -> AsyncIterator[str]:
        """Send message and stream response tokens from LLM provider."""
        async for token in self._message_service.send_message(
            conversation_id, agent_id, content, user_id
        ):
            yield token

    # =========================================================================
    # MEMORY INTEGRATION (delegated)
    # =========================================================================

    async def recall_memories(
        self,
        agent_id: str,
        user_id: str,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> list[Memory]:
        """Recall relevant memories via SomaBrain."""
        return await self._memory_bridge.recall_memories(
            agent_id, user_id, query, limit, tenant_id
        )

    async def store_memory(
        self,
        agent_id: str,
        user_id: str,
        content: str,
        metadata: dict,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Store interaction via SomaBrain."""
        await self._memory_bridge.store_memory(
            agent_id, user_id, content, metadata, tenant_id
        )

    async def store_interaction(
        self,
        *,
        agent_id: str,
        user_id: str,
        conversation_id: str,
        user_message: str,
        assistant_response: str,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Store a full interaction in memory via SomaBrain."""
        await self._memory_bridge.store_interaction(
            agent_id=agent_id,
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=assistant_response,
            tenant_id=tenant_id,
        )

    # =========================================================================
    # TITLE GENERATION (delegated)
    # =========================================================================

    async def generate_title(
        self, conversation_id: str, messages: list[Message]
    ) -> str:
        """Generate conversation title using utility model."""
        return await self._title_generator.generate_title(conversation_id, messages)


# Singleton
_chat_service_instance: Optional[ChatService] = None


async def get_chat_service() -> ChatService:
    """Get or create the singleton ChatService."""
    global _chat_service_instance
    if _chat_service_instance is None:
        _chat_service_instance = ChatService()
    return _chat_service_instance


__all__ = [
    "ChatService",
    "Conversation",
    "Message",
    "AgentSession",
    "Memory",
    "get_chat_service",
]
