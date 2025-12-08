"""Session cache adapter wrapping RedisSessionCache.

This adapter implements SessionCachePort by delegating ALL operations
to the existing production RedisSessionCache implementation.
"""

from typing import Any, Dict, Optional

from services.common.session_repository import RedisSessionCache
from src.core.domain.ports.repositories.session_cache import SessionCachePort


class RedisSessionCacheAdapter(SessionCachePort):
    """Implements SessionCachePort using existing RedisSessionCache.
    
    Delegates ALL operations to services.common.session_repository.RedisSessionCache.
    """
    
    def __init__(
        self,
        cache: Optional[RedisSessionCache] = None,
        url: Optional[str] = None,
        default_ttl: Optional[int] = None,
    ):
        """Initialize adapter with existing cache or create new one.
        
        Args:
            cache: Existing RedisSessionCache instance (preferred)
            url: Redis URL (used if cache not provided)
            default_ttl: Default TTL in seconds
        """
        self._cache = cache or RedisSessionCache(url=url, default_ttl=default_ttl)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        return await self._cache.get(key)
    
    async def set(self, key: str, value: Dict[str, Any], ttl: int = 0) -> None:
        await self._cache.set(key, value, ttl)
    
    async def delete(self, key: str) -> None:
        await self._cache.delete(key)
    
    async def ping(self) -> None:
        await self._cache.ping()
    
    def format_key(self, session_id: str) -> str:
        return self._cache.format_key(session_id)
    
    async def write_context(
        self,
        session_id: str,
        persona_id: Optional[str],
        metadata: Optional[Dict[str, Any]],
        *,
        ttl: int = 0,
    ) -> None:
        await self._cache.write_context(session_id, persona_id, metadata, ttl=ttl)
