"""
Direct Memory Adapter - In-Process Access to SomaFractalMemory.

Used in Agent-as-a-Service (AAAS) mode where Agent, Brain, and Memory run
as ONE Django process with direct Python calls.

VIBE Compliance:
- Rule 2: Real implementation, no mocks
- Rule 10: Django ORM for all database operations
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class DirectMemoryAdapter:
    """
    In-process memory adapter for single-entity AAAS mode.

    Imports SomaFractalMemory modules directly and calls them without HTTP.
    Latency: ~0.01ms per call (plus database/vector store latency).
    """

    def __init__(self, namespace: str = "default"):
        """Initialize with direct imports from SomaFractalMemory."""
        logger.info('DirectMemoryAdapter: Initializing in-process memory access')

        self._namespace = namespace

        # Import memory service
        try:
            from somafractalmemory.services import MemoryService  # type: ignore[import]

            self._memory_service = MemoryService(namespace=namespace)
            logger.info('DirectMemoryAdapter initialized')
        except ImportError as e:
            logger.error('Failed to import SomaFractalMemory: %s', e)
            raise

    def store(
        self,
        coordinate: tuple[float, ...],
        payload: dict,
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> dict:
        """Store data at a coordinate."""
        ns = namespace or self._namespace
        return self._memory_service.store(
            coordinate=coordinate,
            payload=payload,
            tenant=tenant,
            namespace=ns,
        )

    def search(
        self,
        query: str | list[float],
        *,
        top_k: int = 10,
        tenant: str = "default",
        namespace: str | None = None,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors."""
        ns = namespace or self._namespace
        return self._memory_service.search(
            query=query,
            top_k=top_k,
            tenant=tenant,
            namespace=ns,
            filters=filters,
        )

    def get(
        self,
        coordinate: tuple[float, ...],
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> dict | None:
        """Get data at a specific coordinate."""
        ns = namespace or self._namespace
        return self._memory_service.get(
            coordinate=coordinate,
            tenant=tenant,
            namespace=ns,
        )

    def delete(
        self,
        coordinate: tuple[float, ...],
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> bool:
        """Delete data at a coordinate."""
        ns = namespace or self._namespace
        return self._memory_service.delete(
            coordinate=coordinate,
            tenant=tenant,
            namespace=ns,
        )

    async def store_async(
        self,
        coordinate: tuple[float, ...],
        payload: dict,
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> dict:
        """Async store data at a coordinate."""
        return self.store(coordinate=coordinate, payload=payload, tenant=tenant, namespace=namespace)

    async def search_async(
        self,
        query: str | list[float],
        *,
        top_k: int = 10,
        tenant: str = "default",
        namespace: str | None = None,
        filters: dict | None = None,
    ) -> list[dict]:
        """Async search for similar vectors."""
        return self.search(query=query, top_k=top_k, tenant=tenant, namespace=namespace, filters=filters)

    def health(self) -> dict:
        """Health check."""
        try:
            return self._memory_service.health()
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Singleton instance
_memory_adapter: DirectMemoryAdapter | None = None


def get_direct_memory_adapter(namespace: str = "default") -> DirectMemoryAdapter:
    """Get or create the singleton DirectMemoryAdapter."""
    global _memory_adapter
    if _memory_adapter is None:
        _memory_adapter = DirectMemoryAdapter(namespace=namespace)
    return _memory_adapter
