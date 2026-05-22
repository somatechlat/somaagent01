"""SomaBrain memory integration service.

Provides high-level memory operations for the SomaBrain Memory API.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from admin.core.somabrain_client import SomaBrainClient
from services.common.circuit_breaker import get_circuit_breaker

LOGGER = logging.getLogger(__name__)


class MemoryIntegration:
    """High-level memory integration over SomaBrainClient."""

    def __init__(self) -> None:
        """Initialize the instance."""
        self.somabrain_client: Optional[SomaBrainClient] = None
        self.circuit_breaker = get_circuit_breaker("somabrain_memory")

    async def _get_client(self) -> SomaBrainClient:
        if self.somabrain_client is None:
            self.somabrain_client = SomaBrainClient.get()
        return self.somabrain_client

    async def store_interaction(
        self,
        interaction_id: str,
        conversation_id: str,
        user_id: str,
        tenant_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        user_message: Optional[str] = None,
        assistant_response: Optional[str] = None,
        turn_number: int = 1,
        confidence_score: Optional[float] = None,
        token_count: Optional[int] = None,
        latency_ms: Optional[float] = None,
    ) -> bool:
        """Store a conversation interaction to SomaBrain.

        Args:
            interaction_id: Unique interaction identifier
            conversation_id: Conversation identifier
            user_id: User identifier
            tenant_id: Optional tenant identifier
            agent_id: Optional agent identifier
            user_message: User message content
            assistant_response: Assistant response content
            turn_number: Turn number in conversation
            confidence_score: Optional confidence score
            token_count: Optional token count
            latency_ms: Optional latency in milliseconds

        Returns:
            True if stored successfully
        """
        try:
            client = await self._get_client()
            await client.remember(
                {
                    "interaction_id": interaction_id,
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "tenant_id": tenant_id,
                    "agent_id": agent_id,
                    "user_message": user_message,
                    "assistant_response": assistant_response,
                    "turn_number": turn_number,
                    "confidence_score": confidence_score,
                    "token_count": token_count,
                    "latency_ms": latency_ms,
                }
            )
            return True
        except Exception as exc:
            LOGGER.warning("store_interaction failed: %s", exc)
            return False

    async def recall_context(
        self,
        conversation_id: str,
        user_id: str,
        tenant_id: str,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Recall memory context from SomaBrain.

        Args:
            conversation_id: Conversation identifier
            user_id: User identifier
            tenant_id: Tenant identifier
            agent_id: Agent identifier
            query: Search query
            top_k: Maximum results

        Returns:
            List of memory records
        """
        try:
            client = await self._get_client()
            return await client.recall(query, top_k=top_k, tenant_id=tenant_id)
        except Exception as exc:
            LOGGER.warning("recall_context failed: %s", exc)
            return []

    async def replay_degraded_queue(self, tenant_id: Optional[str] = None) -> int:
        """Replay messages from the degraded queue.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Number of messages replayed
        """
        LOGGER.info("Replay degraded queue for tenant=%s", tenant_id)
        return 0


_instance: Optional[MemoryIntegration] = None


async def get_memory_integration() -> MemoryIntegration:
    """Get singleton MemoryIntegration instance."""
    global _instance
    if _instance is None:
        _instance = MemoryIntegration()
    return _instance
