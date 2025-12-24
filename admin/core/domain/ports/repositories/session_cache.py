"""Session cache port interface.

This port defines the contract for session caching operations.
The interface matches the existing RedisSessionCache methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    services.common.session_repository.RedisSessionCache
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SessionCachePort(ABC):
    """Abstract interface for session caching.

    This port wraps the existing RedisSessionCache implementation.
    All methods match the production implementation signature exactly.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        ...

    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 0) -> None:
        """Set a cached value.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (0 for default)
        """
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a cached value.

        Args:
            key: Cache key to delete
        """
        ...

    @abstractmethod
    async def ping(self) -> None:
        """Health check - verify cache connectivity."""
        ...

    @abstractmethod
    def format_key(self, session_id: str) -> str:
        """Format a session ID into a cache key.

        Args:
            session_id: The session identifier

        Returns:
            Formatted cache key
        """
        ...

    @abstractmethod
    async def write_context(
        self,
        session_id: str,
        persona_id: Optional[str],
        metadata: Optional[Dict[str, Any]],
        *,
        ttl: int = 0,
    ) -> None:
        """Write session context to cache.

        Args:
            session_id: The session identifier
            persona_id: Persona identifier
            metadata: Session metadata
            ttl: Time-to-live in seconds
        """
        ...
