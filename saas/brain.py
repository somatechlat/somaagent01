"""
SomaBrain Direct Access Bridge
==============================

Provides in-process access to SomaBrain cognitive core,
eliminating HTTP overhead for brain operations.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Detect saas mode
SAAS_MODE = os.getenv("SOMA_SAAS_MODE", "false").lower() == "true"


class BrainBridge:
    """
    Direct in-process bridge to SomaBrain.

    In SAAS mode: Uses direct Python imports
    In DISTRIBUTED mode: Falls back to HTTP client
    """

    _instance: Optional["BrainBridge"] = None
    _initialized: bool = False

    def __new__(cls) -> "BrainBridge":
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
        """Initialize direct in-process access to SomaBrain."""
        logger.info("🧠 BrainBridge: Initializing DIRECT mode (in-process)")
        try:
            # Import SomaBrain directly
            from somabrain.agent_memory import encode_memory, recall_memory
            from somabrain.math import cosine_similarity, normalize_vector
            from somabrain.quantum import HRRConfig, QuantumLayer

            # Check Rust core
            try:
                import somabrain_rs

                self._rust_available = True
                logger.info("🦀 Rust core loaded: %s", dir(somabrain_rs))
            except ImportError:
                self._rust_available = False
                logger.warning("⚠️ Rust core not available, using Python fallback")

            # Initialize quantum layer
            self._quantum = QuantumLayer(HRRConfig())
            self._encode = encode_memory
            self._recall = recall_memory
            self._cosine = cosine_similarity
            self._normalize = normalize_vector

            self._mode = "direct"
            logger.info("✅ BrainBridge: Direct mode initialized")

        except ImportError as e:
            logger.error("❌ Failed to import SomaBrain: %s", e)
            raise RuntimeError(f"SomaBrain not available in saas: {e}")

    def _init_http(self) -> None:
        """Initialize HTTP client for distributed mode."""
        logger.info("🌐 BrainBridge: Initializing HTTP mode (distributed)")

        import httpx

        # VIBE Rule 100: Use centralized config instead of os.getenv
        try:
            from config import get_settings
            _settings = get_settings()
            # Use somabrain internal host/port from centralized config
            self._base_url = f"http://{getattr(_settings, 'somabrain_host', 'somastack_saas')}:9696"
            logger.info("📦 Using centralized config for SomaBrain URL")
        except ImportError:
            # Fallback for non-SaaS environments
            self._base_url = os.getenv("SOMABRAIN_URL", "http://somastack_saas:9696")
            logger.warning("⚠️ Centralized config not available, using environment")
        
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)
        self._mode = "http"
        logger.info("✅ BrainBridge: HTTP mode initialized -> %s", self._base_url)

    @property
    def mode(self) -> str:
        """Return current mode: 'direct' or 'http'."""
        return self._mode

    @property
    def rust_available(self) -> bool:
        """Check if Rust core is available."""
        return getattr(self, "_rust_available", False)

    # =========================================================================
    # COGNITIVE OPERATIONS
    # =========================================================================

    async def encode_text(self, text: str) -> list[float]:
        """Encode text to HRR vector."""
        if self._mode == "direct":
            vec = self._quantum.encode_text(text)
            return vec.tolist()
        else:
            resp = await self._client.post("/api/encode", json={"text": text})
            return resp.json()["vector"]

    async def cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if self._mode == "direct":
            import numpy as np

            return float(self._cosine(np.array(a), np.array(b)))
        else:
            resp = await self._client.post("/api/similarity", json={"a": a, "b": b})
            return resp.json()["similarity"]

    async def recall(self, query_vector: list[float], top_k: int = 5) -> list[dict]:
        """Recall memories similar to query vector."""
        if self._mode == "direct":
            memories = self._recall(query_vector, top_k=top_k)
            return [m.dict() for m in memories]
        else:
            resp = await self._client.post(
                "/api/recall", json={"vector": query_vector, "top_k": top_k}
            )
            return resp.json()["results"]

    async def health(self) -> Dict[str, Any]:
        """Get brain health status."""
        if self._mode == "direct":
            return {
                "status": "healthy",
                "mode": "direct",
                "rust_available": self.rust_available,
            }
        else:
            resp = await self._client.get("/health")
            return resp.json()


# Singleton instance
brain = BrainBridge()
