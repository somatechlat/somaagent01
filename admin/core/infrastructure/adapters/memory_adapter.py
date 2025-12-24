"""Memory adapter wrapping SomaBrainClient.

This adapter implements MemoryAdapterPort by delegating ALL operations
to the existing production SomaBrainClient async functions.
"""

from typing import Any, Dict, List, Optional

import httpx

from admin.agents.services.somabrain_integration import (
    build_context_async,
    get_weights_async,
    publish_reward_async,
)
import os


class SomaBrainMemoryAdapter(MemoryAdapterPort):
    """Implements MemoryAdapterPort using existing SomaBrainClient functions.

    Delegates ALL operations to python.integrations.somabrain_client async functions.
    """

    def __init__(self, base_url: Optional[str] = None):
        """Initialize adapter.

        Args:
            base_url: SomaBrain base URL (uses config if not provided)
        """
        self._base_url = base_url

    def _get_base_url(self) -> str:
        """Get the base URL for SomaBrain service."""
        if self._base_url:
            return self._base_url
        return cfg.get_somabrain_url()

    async def build_context(
        self,
        payload: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        return await build_context_async(payload)

    async def get_weights(self) -> Dict[str, Any]:
        return await get_weights_async()

    async def publish_reward(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        return await publish_reward_async(payload)

    async def store_memory(
        self,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Store a memory item via HTTP POST."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._get_base_url()}/v1/memory/store",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def recall_memory(
        self,
        query: str,
        *,
        session_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Recall memories matching a query via HTTP POST."""
        payload: Dict[str, Any] = {"query": query, "limit": limit}
        if session_id:
            payload["session_id"] = session_id

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._get_base_url()}/v1/memory/recall",
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    async def health_check(self) -> bool:
        """Check if the memory service is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._get_base_url()}/health")
                return resp.status_code == 200
        except Exception:
            return False
