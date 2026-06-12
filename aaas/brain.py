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

# Detect aaas mode via canonical DeploymentMode
from services.common.deployment_mode import DeploymentMode

AAAS_MODE = DeploymentMode.is_aaas()


class BrainBridge:
    """
    Direct in-process bridge to SomaBrain.

    In AAAS mode: Uses direct Python imports
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

        if AAAS_MODE:
            self._init_direct()
        else:
            self._init_http()

    def _init_direct(self) -> None:
        """Initialize direct in-process access to SomaBrain."""
        logger.info('BrainBridge: Initializing DIRECT mode (in-process)')
        try:
            # Import SomaBrain directly
            from somabrain.agent_memory import encode_memory, recall_memory
            from somabrain.math import cosine_similarity, normalize_vector
            from somabrain.quantum import HRRConfig, QuantumLayer

            # Check Rust core
            try:
                import somabrain_rs

                self._rust_available = True
                logger.info('Rust core loaded: %s', dir(somabrain_rs))
            except ImportError:
                self._rust_available = False
                logger.warning('Rust core not available, using Python fallback')

            # Initialize quantum layer
            self._quantum = QuantumLayer(HRRConfig())
            self._encode = encode_memory
            self._recall = recall_memory
            self._cosine = cosine_similarity
            self._normalize = normalize_vector

            self._mode = "direct"
            logger.info('BrainBridge: Direct mode initialized')

        except ImportError as e:
            logger.error('Failed to import SomaBrain: %s', e)
            raise RuntimeError(f"SomaBrain not available in aaas: {e}")

    def _init_http(self) -> None:
        """Initialize HTTP client for distributed mode."""
        logger.info('BrainBridge: Initializing HTTP mode (distributed)')

        import httpx

        # VIBE Rule 100: Use centralized config
        from config import get_settings

        _settings = get_settings()
        self._base_url = f"http://{getattr(_settings, 'somabrain_host', 'somastack_aaas')}:9696"
        logger.info('Using centralized config for SomaBrain URL')

        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=30.0)
        self._mode = "http"
        logger.info('BrainBridge: HTTP mode initialized -> %s', self._base_url)

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

    async def recall(
        self,
        query: str | list[float],
        *,
        top_k: int = 5,
        tenant: str = "default",
        filters: dict | None = None,
    ) -> list[dict]:
        """Recall memories similar to query vector or text.

        Args:
            query: Text string or pre-encoded vector.
            top_k: Maximum results to return.
            tenant: Tenant filter.
            filters: Optional metadata filters.
        """
        if self._mode == "direct":
            # Encode text to vector if needed
            if isinstance(query, str):
                query_vector = self._quantum.encode_text(query).tolist()
            else:
                query_vector = query
            memories = self._recall(query_vector, top_k=top_k)
            return [m.dict() for m in memories]
        else:
            payload: dict[str, Any] = {"query": query, "top_k": top_k, "tenant": tenant}
            if filters:
                payload["filters"] = filters
            resp = await self._client.post("/api/recall", json=payload)
            return resp.json()["results"]

    async def recall_text(
        self,
        query: str,
        *,
        top_k: int = 5,
        tenant: str = "default",
        filters: dict | None = None,
    ) -> list[dict]:
        """Recall memories from a text query.

        Delegates to the underlying brain client's recall method.
        """
        return await self.recall(query, top_k=top_k, tenant=tenant, filters=filters)

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

    async def remember(self, content: str, **kwargs) -> Dict[str, Any]:
        """Store a memory (Episodic/Semantic).

        Args:
            content: The text content to remember
            **kwargs: Metadata (tags, importance, etc.)

        Returns:
            Dict containing memory_id and coordinate
        """
        if self._mode == "direct":
            try:
                # Import internally to avoid top-level dependency issues
                from somabrain.agent_memory import store_memory_item

                # In direct mode, we call the brain's internal store function
                result = await store_memory_item(content, **kwargs)
                return result
            except ImportError:
                logger.error('Failed to import somabrain.agent_memory.store_memory_item')
                raise
            except Exception as e:
                logger.error('Direct memory store failed: %s', e)
                raise
        else:
            # HTTP Fallback
            payload = {"content": content, "metadata": kwargs}
            resp = await self._client.post("/api/remember", json=payload)
            return resp.json()

    # =========================================================================
    # GMD LEARNING / RL FEEDBACK (Theorem 2)
    # =========================================================================

    def apply_feedback(self, tenant_id: str, utility: float, reward: float) -> bool:
        """Apply RL feedback signal - GMD Theorem 2.

        AAAS (direct): AdaptationEngine.apply_feedback()
        DISTRIBUTED (http): Falls back to HTTP
        """
        if self._mode == "direct":
            try:
                from somabrain.learning.adaptation import AdaptationEngine

                if not hasattr(self, "_engines"):
                    self._engines: Dict[str, Any] = {}
                if tenant_id not in self._engines:
                    self._engines[tenant_id] = AdaptationEngine(tenant_id=tenant_id)
                return self._engines[tenant_id].apply_feedback(utility=utility, reward=reward)
            except Exception as e:
                logger.error('[GMD] Direct feedback failed: %s', e)
                return False
        else:
            logger.warning("[GMD] apply_feedback() in HTTP mode - use async version")
            return False

    async def apply_feedback_async(
        self, session_id: str, signal: str, value: float, meta: Optional[Dict] = None
    ) -> bool:
        """Apply RL feedback - async version for HTTP mode."""
        if self._mode == "direct":
            return self.apply_feedback(session_id, utility=value, reward=value)
        else:
            try:
                resp = await self._client.post(
                    "/v1/learning/reward",
                    json={
                        "session_id": session_id,
                        "signal": signal,
                        "value": value,
                        "meta": meta or {},
                    },
                )
                return resp.json().get("ok", False)
            except Exception as e:
                logger.error('[GMD] HTTP feedback failed: %s', e)
                return False

    # =========================================================================
    # NEUROMODULATORS
    # =========================================================================

    def get_neuromodulators(self, tenant_id: str) -> Dict[str, float]:
        """Get neuromodulator state - GMD baseline.

        AAAS (direct): PerTenantNeuromodulators
        """
        if self._mode == "direct":
            try:
                from somabrain.neuromodulators import PerTenantNeuromodulators

                if not hasattr(self, "_neuromod"):
                    self._neuromod = PerTenantNeuromodulators()
                state = self._neuromod.get_state(tenant_id)
                return {
                    "dopamine": state.dopamine,
                    "serotonin": state.serotonin,
                    "noradrenaline": state.noradrenaline,
                    "acetylcholine": state.acetylcholine,
                }
            except Exception as e:
                logger.error('[GMD] Direct get_neuromodulators failed: %s', e)
        return {"dopamine": 0.5, "serotonin": 0.5, "noradrenaline": 0.5, "acetylcholine": 0.5}

    def set_neuromodulators(self, tenant_id: str, **levels) -> None:
        """Set neuromodulator state - GMD baseline.

        AAAS (direct): PerTenantNeuromodulators
        """
        if self._mode == "direct":
            try:
                from somabrain.neuromodulators import NeuromodState, PerTenantNeuromodulators

                if not hasattr(self, "_neuromod"):
                    self._neuromod = PerTenantNeuromodulators()
                state = NeuromodState(**levels)
                self._neuromod.set_state(tenant_id, state)
                logger.info('[GMD] Neuromodulators set for tenant %s', tenant_id[:8])
            except Exception as e:
                logger.error('[GMD] Direct set_neuromodulators failed: %s', e)

    async def set_neuromodulators_async(
        self, tenant_id: str, persona_id: str, neuromodulators: Dict[str, float]
    ) -> None:
        """Set neuromodulators - async for HTTP mode."""
        if self._mode == "direct":
            self.set_neuromodulators(tenant_id, **neuromodulators)
        else:
            try:
                await self._client.put(
                    "/v1/neuromodulators",
                    json={
                        "tenant": tenant_id,
                        "persona": persona_id,
                        "neuromodulators": neuromodulators,
                    },
                )
            except Exception as e:
                logger.error('[GMD] HTTP set_neuromodulators failed: %s', e)


# Lazy singleton — only instantiates on first attribute access
_brain_instance: BrainBridge | None = None


class _LazyBrainBridge:
    """Lazy proxy for BrainBridge — instantiates on first use."""

    def _get_instance(self) -> BrainBridge:
        global _brain_instance
        if _brain_instance is None:
            _brain_instance = BrainBridge()
        return _brain_instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_instance(), name)


brain = _LazyBrainBridge()
