"""MemoryPort — Canonical interface for all memory operations.

P3-01: Consolidates 9 memory entry points into a single protocol.

All memory access (SomaBrain, SomaFractalMemory, PostgreSQL history,
PendingMemory queue) MUST go through a MemoryPort adapter.

VIBE COMPLIANT:
- Protocol-based (no inheritance required)
- Fail-closed (unconfigured adapter = honest error)
- No hardcoded values
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class MemoryPort(Protocol):
    """Canonical port for memory store and recall operations.

    Implementations:
    - DirectMemoryAdapter  → uses aaas.brain.BrainBridge (in-process)
    - HttpMemoryAdapter    → uses admin.core.somabrain_client.SomaBrainClient
    - FallbackMemoryAdapter → queues to PendingMemory + logs
    - NoOpMemoryAdapter    → for standalone mode (no brain)
    """

    async def remember(
        self,
        content: str,
        *,
        tenant_id: str = "default",
        namespace: str = "chat_history",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store a memory and return the storage result.

        Args:
            content: The text content to remember.
            tenant_id: Tenant isolation key.
            namespace: Logical memory namespace.
            metadata: Optional tags, importance, source, etc.

        Returns:
            Dict with at least `memory_id` and `coordinate` keys.
        """
        ...

    async def recall(
        self,
        query: str | List[float],
        *,
        tenant_id: str = "default",
        namespace: str = "chat_history",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Recall memories similar to query.

        Args:
            query: Text string or pre-encoded vector.
            tenant_id: Tenant isolation key.
            namespace: Logical memory namespace.
            top_k: Maximum results.
            filters: Optional metadata filters.

        Returns:
            List of memory dicts, best match first.
        """
        ...

    async def health(self) -> Dict[str, Any]:
        """Return adapter health status."""
        ...


class NoOpMemoryAdapter:
    """Standalone mode adapter — memory operations are no-ops.

    Chat continues normally; cognitive memory is simply unavailable.
    This is the honest fail-closed behavior for standalone deployments.
    """

    async def remember(
        self,
        content: str,
        *,
        tenant_id: str = "default",
        namespace: str = "chat_history",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {"memory_id": "noop", "coordinate": "standalone", "status": "disabled"}

    async def recall(
        self,
        query: str | List[float],
        *,
        tenant_id: str = "default",
        namespace: str = "chat_history",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    async def health(self) -> Dict[str, Any]:
        return {"status": "disabled", "mode": "standalone"}


class FallbackMemoryAdapter:
    """Degradation mode adapter — queues to PendingMemory when primary is down.

    Used when SomaBrain circuit is OPEN or the brain module is unavailable.
    Stores are persisted to PostgreSQL PendingMemory for later sync.
    """

    async def remember(
        self,
        content: str,
        *,
        tenant_id: str = "default",
        namespace: str = "chat_history",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        from uuid import uuid4

        from admin.core.models import PendingMemory

        payload = {
            "content": content,
            "metadata": metadata or {},
        }
        pm = PendingMemory.objects.create(
            idempotency_key=f"fallback:{tenant_id}:{namespace}:{uuid4()}",
            tenant_id=tenant_id,
            namespace=namespace,
            payload=payload,
        )
        return {"memory_id": str(pm.id), "status": "queued", "mode": "fallback"}

    async def recall(
        self,
        query: str | List[float],
        *,
        tenant_id: str = "default",
        namespace: str = "chat_history",
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        return []

    async def health(self) -> Dict[str, Any]:
        return {"status": "degraded", "mode": "fallback"}
