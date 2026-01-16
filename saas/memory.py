"""
FractalMemory Direct Access Bridge
==================================

Provides in-process access to SomaFractalMemory,
eliminating HTTP overhead for memory operations.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Detect saas mode
SAAS_MODE = os.getenv("SOMA_SAAS_MODE", "false").lower() == "true"


class MemoryBridge:
    """
    Direct in-process bridge to FractalMemory.

    In SAAS mode: Uses direct Python imports
    In DISTRIBUTED mode: Falls back to HTTP client
    """

    _instance: Optional["MemoryBridge"] = None
    _initialized: bool = False

    def __new__(cls) -> "MemoryBridge":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        if SAAS_MODE:
            self._init_direct()
        else:
            self._init_http()

    def _init_direct(self) -> None:
        """Initialize direct in-process access to FractalMemory."""
        logger.info("💾 MemoryBridge: Initializing DIRECT mode (in-process)")
        try:
            # Import FractalMemory directly
            from fractal_memory.service import FractalMemoryService
            from fractal_memory.stores.milvus_store import MilvusVectorStore
            from fractal_memory.stores.redis_store import RedisKVStore

            # VIBE Rule 100: Use centralized config instead of os.getenv
            try:
                from config import get_settings

                _settings = get_settings()
                milvus_host = _settings.milvus_host
                milvus_port = _settings.milvus_port
                redis_host = _settings.redis_host
                redis_port = _settings.redis_port
                logger.info(
                    "📦 Using centralized config: Milvus=%s:%s, Redis=%s:%s",
                    milvus_host,
                    milvus_port,
                    redis_host,
                    redis_port,
                )
            except ImportError:
                # Fallback for non-SaaS environments
                milvus_host = os.getenv("MILVUS_HOST", "somastack_milvus")
                milvus_port = int(os.getenv("MILVUS_PORT", "19530"))
                redis_host = os.getenv("REDIS_HOST", "somastack_redis")
                redis_port = int(os.getenv("REDIS_PORT", "6379"))
                logger.warning("⚠️ Centralized config not available, using environment")

            self._vector_store = MilvusVectorStore(host=milvus_host, port=milvus_port)
            self._kv_store = RedisKVStore(host=redis_host, port=redis_port)
            self._service = FractalMemoryService(
                vector_store=self._vector_store,
                kv_store=self._kv_store,
            )

            self._mode = "direct"
            logger.info("✅ MemoryBridge: Direct mode initialized")

        except ImportError as e:
            logger.error("❌ Failed to import FractalMemory: %s", e)
            raise RuntimeError(f"FractalMemory not available in saas: {e}")

    def _init_http(self) -> None:
        """Initialize HTTP client for distributed mode."""
        logger.info("🌐 MemoryBridge: Initializing HTTP mode (distributed)")

        import httpx

        self._base_url = os.getenv("SFM_URL", "http://somafractalmemory:10101")

        # VIBE Rule 164: No hardcoded secrets - require auth token from environment
        auth_token = os.getenv("SOMA_MEMORY_API_TOKEN") or os.getenv("SOMA_API_TOKEN")
        if not auth_token:
            logger.warning(
                "⚠️ SOMA_MEMORY_API_TOKEN not set - HTTP requests will be unauthenticated. "
                "Set SOMA_MEMORY_API_TOKEN or SOMA_API_TOKEN in production."
            )
            headers = {}
        else:
            headers = {"Authorization": f"Bearer {auth_token}"}

        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=30.0,
            headers=headers,
        )
        self._mode = "http"
        logger.info("✅ MemoryBridge: HTTP mode initialized -> %s", self._base_url)

    @property
    def mode(self) -> str:
        """Return current mode: 'direct' or 'http'."""
        return self._mode

    # =========================================================================
    # MEMORY OPERATIONS
    # =========================================================================

    async def store(
        self, coord: str, payload: Dict[str, Any], vector: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Store a memory at the given coordinate.

        Args:
            coord: Fractal coordinate (x,y,z format)
            payload: Memory payload data
            vector: Optional embedding vector

        Returns:
            Store result with coord and success status
        """
        if self._mode == "direct":
            result = await self._service.store(coord, payload, vector)
            return {"ok": True, "coord": coord, "result": result}
        else:
            resp = await self._client.post(
                "/memories", json={"coord": coord, "payload": payload, "vector": vector}
            )
            return resp.json()

    async def recall(
        self, query: str, top_k: int = 5, universe: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recall memories matching the query.

        Args:
            query: Search query string
            top_k: Number of results to return
            universe: Optional universe filter

        Returns:
            List of matching memories with scores
        """
        if self._mode == "direct":
            results = await self._service.recall(query, top_k=top_k, universe=universe)
            return results
        else:
            resp = await self._client.post(
                "/memories/search", json={"query": query, "limit": top_k, "universe": universe}
            )
            return resp.json().get("memories", [])

    async def get(self, coord: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific memory by coordinate.

        Args:
            coord: Fractal coordinate

        Returns:
            Memory data or None if not found
        """
        if self._mode == "direct":
            return await self._service.get(coord)
        else:
            resp = await self._client.get(f"/memories/{coord}")
            if resp.status_code == 404:
                return None
            return resp.json()

    async def delete(self, coord: str) -> bool:
        """
        Delete a memory by coordinate.

        Args:
            coord: Fractal coordinate

        Returns:
            True if deleted, False otherwise
        """
        if self._mode == "direct":
            await self._service.delete(coord)
            return True
        else:
            resp = await self._client.delete(f"/memories/{coord}")
            return resp.status_code == 200

    async def health(self) -> Dict[str, Any]:
        """Get memory system health status."""
        if self._mode == "direct":
            return {
                "status": "healthy",
                "mode": "direct",
                "vector_store": self._vector_store.is_connected,
                "kv_store": self._kv_store.is_connected,
            }
        else:
            resp = await self._client.get("/health")
            return resp.json()


# Singleton instance
memory = MemoryBridge()
