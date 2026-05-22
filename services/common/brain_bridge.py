"""BrainBridge - Direct In-Process Access to SomaBrain (AAAS Mode).

This module provides the "Direct Interface" pattern for Agent-to-Brain communication
when running in the secure AAAS (Agent As A Service) "God Process".

Deployment Modes:
- AAAS: DIRECT calls to `somabrain.services` (In-Memory, <0.1ms latency)
- STANDALONE: This module will raise ImportError or be disabled.

Strict Isolation:
- This module MUST ONLY be imported if `SOMA_DEPLOY_MODE=AAAS`.
- It relies on `somabrain` being installed in the same python environment.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# 1. Detect Mode
DEPLOY_MODE = os.environ.get("SOMA_DEPLOY_MODE", "dev").upper()
IS_AAAS = DEPLOY_MODE == "AAAS" or os.environ.get("AAAS_ENABLED", "false").lower() == "true"


class BrainBridgeError(Exception):
    """Bridge specific errors."""

    pass


class _BrainBridge:
    """Singleton bridge to SomaBrain services."""

    _instance = None
    _memory_service: Any = None
    _mode = "direct"  # Used by SomaBrainClient to detect direct bridge

    def __init__(self):
        if not IS_AAAS:
            raise BrainBridgeError("BrainBridge initialized in non-AAAS mode.")

        try:
            # LAZY IMPORT - Critical for Standalone isolation
            from somabrain.core.container import container  # type: ignore  # type: ignore[import]
            from somabrain.services.memory_service import (  # type: ignore[import]
                MemoryService,  # noqa: F401
            )

            # For robustness, we check container first
            if container.has("memory_service"):
                self._memory_service = container.get("memory_service")
                logger.info("BrainBridge: MemoryService resolved from container.")
            else:
                raise BrainBridgeError(
                    "SomaBrain container has no 'memory_service'. "
                    "AAAS bootstrap failed — ensure SomaBrain initializes before Agent code."
                )

        except ImportError as e:
            logger.error(f"BrainBridge failed to import somabrain: {e}")
            raise BrainBridgeError(f"Cannot import somabrain modules: {e}") from e
            raise BrainBridgeError(f"AAAS Mode requires 'somabrain' package: {e}")

    @property
    def mode(self) -> str:
        return "direct" if IS_AAAS else "http"

    async def remember(
        self, content: str, tenant: str, namespace: str, metadata: dict
    ) -> Dict[str, Any]:
        """Direct memory store."""
        if not self._memory_service:
            # Retry fetch from container (lifecycle timing)
            self._resolve_services()

        # MemoryService.remember is synchronous usually, but we expose async for compatibility
        # If the underlying service is sync, we run it directly (it's fast) or thread it.
        # somabrain.services.memory_service.MemoryService.remember IS synchronous wrapping .client().remember

        try:
            # Construct payload expectation
            payload = {
                "content": content,
                "metadata": metadata,
                # Flatten metadata for searchability if needed, or keep nested
                **metadata,
            }

            # The MemoryService.remember expects (key, payload, universe)
            # We need to generate a key if not provided?
            # Actually MemoryService facade is a bit different than SomaBrainClient.
            # Let's look at MemoryService signature: remember(self, key, payload, universe)

            import hashlib

            key = metadata.get("key") or f"mem_{hashlib.md5(content.encode()).hexdigest()}"

            # CALL DIRECTLY
            res = self._memory_service.remember(key=key, payload=payload)

            # Normalise response to match Client expected output
            return {
                "coordinate": res if isinstance(res, (list, tuple)) else [],
                "id": key,
                "status": "success",
            }
        except Exception as e:
            logger.error(f"BrainBridge Direct Remember Error: {e}")
            raise

    async def recall(
        self, query_vector: Any = None, *, query: str | None = None, top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """Direct recall — delegates to recall_text since MemoryService handles embedding internally.

        Args:
            query_vector: DEPRECATED — kept for backward compat with callers that pass encode_text result.
            query: The text query to recall memories for.
            top_k: Number of results to return.
        """
        # Callers should pass `query=`; if they pass query_vector (legacy), try to use it as text
        text = query
        if text is None and isinstance(query_vector, str):
            text = query_vector
        if text is None:
            raise BrainBridgeError(
                "recall() requires `query` parameter (string). "
                "Pass query='your search text' instead of query_vector."
            )
        return await self.recall_text(query=text, top_k=top_k)

    async def recall_text(
        self, query: str, top_k: int = 10, tenant: str = "default"
    ) -> List[Dict[str, Any]]:
        if not self._memory_service:
            self._resolve_services()

        try:
            hits = self._memory_service.recall(query=query, top_k=top_k)
            # hits is List[RecallHit]
            results = []
            for h in hits:
                results.append({"payload": h.payload, "score": h.score, "coordinate": h.coordinate})
            return results
        except Exception as e:
            logger.error(f"BrainBridge Direct Recall Error: {e}")
            raise

    async def encode_text(self, text: str) -> List[float]:
        # If we need embedding, we might need an embedding service.
        # But for 'recall_text', MemoryService handles it.
        return []

    def _resolve_services(self):
        from somabrain.core.container import container  # type: ignore

        if container.has("memory_service"):
            self._memory_service = container.get("memory_service")
        else:
            raise BrainBridgeError(
                "SomaBrain container has no 'memory_service'. AAAS Bootstrap failed?"
            )


# Global Singleton
brain = _BrainBridge() if IS_AAAS else None
