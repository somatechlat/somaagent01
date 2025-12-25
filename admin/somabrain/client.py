"""SomaBrain API Client.

VIBE COMPLIANT - Async HTTP client for SomaBrain cognitive memory.
Per CANONICAL_USER_JOURNEYS_SRS.md UC-05: View/Manage Memories.

SomaBrain endpoints: http://localhost:9696
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class SomaBrainConfig:
    """SomaBrain API configuration."""
    base_url: str = "http://localhost:9696"
    timeout: float = 30.0
    
    @classmethod
    def from_settings(cls) -> "SomaBrainConfig":
        """Load config from Django settings."""
        return cls(
            base_url=getattr(settings, "SOMABRAIN_URL", "http://localhost:9696"),
            timeout=getattr(settings, "SOMABRAIN_TIMEOUT", 30.0),
        )


class SomaBrainClient:
    """Async client for SomaBrain cognitive memory API.
    
    VIBE COMPLIANT:
    - Full async support
    - Graceful degradation
    - ZDL pattern ready
    """
    
    def __init__(self, config: Optional[SomaBrainConfig] = None):
        self.config = config or SomaBrainConfig.from_settings()
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers={"Content-Type": "application/json"},
                timeout=self.config.timeout,
            )
        return self._client
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def health_check(self) -> dict:
        """Check SomaBrain health status."""
        client = await self._get_client()
        try:
            response = await client.get("/health")
            return {"status": "healthy", "latency_ms": response.elapsed.total_seconds() * 1000}
        except Exception as e:
            return {"status": "down", "error": str(e)}
    
    # =========================================================================
    # MEMORY OPERATIONS - Per UC-05
    # =========================================================================
    
    async def remember(
        self,
        content: str,
        tenant_id: str,
        user_id: str,
        memory_type: str = "episodic",
        metadata: Optional[dict] = None,
    ) -> dict:
        """Store a memory in SomaBrain.
        
        Args:
            content: Memory content (text)
            tenant_id: Tenant UUID
            user_id: User UUID
            memory_type: episodic, semantic, procedural
            metadata: Additional context
        """
        client = await self._get_client()
        
        payload = {
            "content": content,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "memory_type": memory_type,
            "metadata": metadata or {},
        }
        
        try:
            response = await client.post("/memory/remember", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain remember failed: {e}")
            raise SomaBrainError(f"Failed to store memory: {e}")
    
    async def recall(
        self,
        query: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 10,
        memory_type: Optional[str] = None,
    ) -> list[dict]:
        """Recall memories from SomaBrain (semantic search).
        
        Args:
            query: Search query
            tenant_id: Tenant UUID
            user_id: Optional user filter
            limit: Max results
            memory_type: Filter by type
        """
        client = await self._get_client()
        
        payload = {
            "query": query,
            "tenant_id": tenant_id,
            "limit": limit,
        }
        if user_id:
            payload["user_id"] = user_id
        if memory_type:
            payload["memory_type"] = memory_type
        
        try:
            response = await client.post("/memory/recall", json=payload)
            response.raise_for_status()
            return response.json().get("memories", [])
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain recall failed: {e}")
            raise SomaBrainError(f"Failed to recall memories: {e}")
    
    async def act(
        self,
        agent_id: str,
        input_text: str,
        context: Optional[dict] = None,
        mode: str = "FULL",
    ) -> dict:
        """Execute an agent action with SomaBrain.
        
        REAL SomaBrain call - NO MOCK DATA.
        
        Args:
            agent_id: Agent UUID
            input_text: User input
            context: Optional context dict
            mode: FULL, MINIMAL, LITE, ADMIN
        """
        client = await self._get_client()
        
        payload = {
            "agent_id": agent_id,
            "input": input_text,
            "context": context or {},
            "mode": mode,
        }
        
        try:
            response = await client.post("/act", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain act failed: {e}")
            raise SomaBrainError(f"Failed to execute action: {e}")
    
    async def forget(self, memory_id: str, tenant_id: str) -> bool:
        """Delete a memory from SomaBrain.
        
        Args:
            memory_id: Memory UUID
            tenant_id: Tenant UUID (for authorization)
        """
        client = await self._get_client()
        
        try:
            response = await client.delete(
                f"/memory/{memory_id}",
                params={"tenant_id": tenant_id},
            )
            return response.status_code == 200
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain forget failed: {e}")
            return False
    
    async def get_recent(
        self,
        tenant_id: str,
        user_id: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """Get recent memories.
        
        Args:
            tenant_id: Tenant UUID
            user_id: Optional user filter
            limit: Max results
        """
        client = await self._get_client()
        
        params = {"tenant_id": tenant_id, "limit": limit}
        if user_id:
            params["user_id"] = user_id
        
        try:
            response = await client.get("/memory/recent", params=params)
            response.raise_for_status()
            return response.json().get("memories", [])
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain get_recent failed: {e}")
            return []
    
    async def get_pending_count(self, tenant_id: str) -> int:
        """Get count of pending memory syncs.
        
        Used for degradation mode status display.
        """
        client = await self._get_client()
        
        try:
            response = await client.get(
                "/memory/pending",
                params={"tenant_id": tenant_id},
            )
            response.raise_for_status()
            return response.json().get("count", 0)
        except httpx.HTTPError:
            return 0
    
    # =========================================================================
    # COGNITIVE OPERATIONS - Per UC-06
    # =========================================================================
    
    async def get_cognitive_state(self, agent_id: str) -> dict:
        """Get agent's cognitive state.
        
        Returns neuromodulator levels, adaptation parameters.
        """
        client = await self._get_client()
        
        try:
            response = await client.get(f"/cognitive/state/{agent_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain get_cognitive_state failed: {e}")
            return {}
    
    async def update_cognitive_params(
        self,
        agent_id: str,
        params: dict,
    ) -> dict:
        """Update agent's cognitive parameters.
        
        Args:
            agent_id: Agent UUID
            params: Parameters to update (temperature, creativity, etc.)
        """
        client = await self._get_client()
        
        try:
            response = await client.patch(
                f"/cognitive/params/{agent_id}",
                json=params,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain update_cognitive_params failed: {e}")
            raise SomaBrainError(f"Failed to update params: {e}")
    
    async def trigger_sleep_cycle(self, agent_id: str) -> dict:
        """Trigger agent sleep cycle for memory consolidation.
        
        Per SomaBrain cognitive architecture.
        """
        client = await self._get_client()
        
        try:
            response = await client.post(f"/cognitive/sleep-cycle/{agent_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain trigger_sleep_cycle failed: {e}")
            raise SomaBrainError(f"Failed to trigger sleep: {e}")
    
    async def adaptation_reset(self, agent_id: str) -> dict:
        """Reset agent adaptation parameters to defaults."""
        client = await self._get_client()
        
        try:
            response = await client.post(f"/context/adaptation/reset/{agent_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"SomaBrain adaptation_reset failed: {e}")
            raise SomaBrainError(f"Failed to reset adaptation: {e}")


class SomaBrainError(Exception):
    """SomaBrain API error."""
    pass


# Singleton instance
_somabrain_client: Optional[SomaBrainClient] = None


def get_somabrain_client() -> SomaBrainClient:
    """Get the SomaBrain client singleton."""
    global _somabrain_client
    if _somabrain_client is None:
        _somabrain_client = SomaBrainClient()
    return _somabrain_client
