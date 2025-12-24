"""Memory adapter port interface.

This port defines the contract for memory/context operations.
The interface matches the existing SomaBrainClient async functions
to enable seamless wrapping of the production implementation.

Production Implementation:
    python.integrations.somabrain_client (async functions)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MemoryAdapterPort(ABC):
    """Abstract interface for memory operations.

    This port wraps the existing SomaBrainClient implementation.
    Methods match the production async function signatures.
    """

    @abstractmethod
    async def build_context(
        self,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build context for a conversation.

        Args:
            payload: Context request payload containing:
                - session_id: Session identifier
                - message: User message
                - persona_id: Persona identifier
                - tenant: Tenant identifier

        Returns:
            List of context items for LLM
        """
        ...

    @abstractmethod
    async def get_weights(self) -> Dict[str, Any]:
        """Get current memory weights configuration.

        Returns:
            Weight configuration dictionary
        """
        ...

    @abstractmethod
    async def publish_reward(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Publish a reward signal for memory reinforcement.

        Args:
            payload: Reward payload containing:
                - session_id: Session identifier
                - reward: Reward value
                - context: Additional context

        Returns:
            Response from reward publication
        """
        ...

    @abstractmethod
    async def store_memory(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Store a memory item.

        Args:
            payload: Memory payload to store

        Returns:
            Storage confirmation response
        """
        ...

    @abstractmethod
    async def recall_memory(
        self,
        query: str,
        *,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Recall memories matching a query.

        Args:
            query: Search query
            session_id: Optional session filter
            limit: Maximum results to return

        Returns:
            List of matching memory items
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the memory service is healthy.

        Returns:
            True if healthy, False otherwise
        """
        ...
