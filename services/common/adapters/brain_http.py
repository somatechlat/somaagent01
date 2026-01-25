"""
HTTP Brain Adapter - Network Access to SomaBrain.

Used in distributed mode where Agent, Brain, and Memory run
as SEPARATE containers/services communicating over HTTP.

VIBE Compliance:
- Rule 2: Real implementation, no mocks
- Rule 5: Uses real HTTP endpoints, verified from docs
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from services.common.protocols import BrainServiceProtocol

logger = logging.getLogger(__name__)


class HTTPBrainAdapter:
    """
    HTTP-based brain adapter for distributed mode.

    Communicates with SomaBrain via HTTP REST API.
    Latency: ~5-50ms per call depending on network.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 30.0):
        """Initialize HTTP client for SomaBrain."""
        logger.info("🌐 HTTPBrainAdapter: Initializing HTTP mode (distributed)")

        self._base_url = base_url or os.environ.get(
            "SOMABRAIN_URL",
            os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696"),
        )
        self._timeout = timeout
        self._client = httpx.Client(base_url=self._base_url, timeout=timeout)
        self._async_client: httpx.AsyncClient | None = None

        logger.info(f"✅ HTTPBrainAdapter initialized: {self._base_url}")

    def _get_async_client(self) -> httpx.AsyncClient:
        """Lazy initialize async client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout
            )
        return self._async_client

    def encode(self, text: str) -> list[float]:
        """Encode text to vector using quantum layer via HTTP."""
        try:
            response = self._client.post(
                "/api/v1/encode",
                json={"text": text},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("vector", data.get("embedding", []))
        except httpx.HTTPError as e:
            logger.error(f"Brain encode failed: {e}")
            raise RuntimeError(f"SomaBrain encode failed: {e}") from e

    def remember(
        self,
        content: str,
        *,
        tenant: str = "default",
        session_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Store a memory in the cognitive core via HTTP."""
        try:
            response = self._client.post(
                "/api/v1/memory/store",
                json={
                    "content": content,
                    "tenant": tenant,
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "metadata": metadata or {},
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Brain remember failed: {e}")
            raise RuntimeError(f"SomaBrain remember failed: {e}") from e

    def recall(
        self,
        query: str,
        *,
        top_k: int = 10,
        tenant: str = "default",
        filters: dict | None = None,
    ) -> list[dict]:
        """Recall memories matching the query via HTTP."""
        try:
            response = self._client.post(
                "/api/v1/memory/recall",
                json={
                    "query": query,
                    "top_k": top_k,
                    "tenant": tenant,
                    "filters": filters or {},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", data.get("memories", []))
        except httpx.HTTPError as e:
            logger.error(f"Brain recall failed: {e}")
            raise RuntimeError(f"SomaBrain recall failed: {e}") from e

    def apply_feedback(
        self,
        session_id: str,
        signal: str,
        value: float,
    ) -> dict:
        """Apply reinforcement signal to learning system via HTTP."""
        try:
            response = self._client.post(
                "/api/v1/feedback",
                json={
                    "session_id": session_id,
                    "signal": signal,
                    "value": value,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.warning(f"Brain feedback failed: {e}")
            return {"status": "failed", "error": str(e)}

    async def encode_async(self, text: str) -> list[float]:
        """Async encode text to vector."""
        client = self._get_async_client()
        try:
            response = await client.post("/api/v1/encode", json={"text": text})
            response.raise_for_status()
            data = response.json()
            return data.get("vector", data.get("embedding", []))
        except httpx.HTTPError as e:
            logger.error(f"Brain encode (async) failed: {e}")
            raise RuntimeError(f"SomaBrain encode failed: {e}") from e

    async def recall_async(
        self,
        query: str,
        *,
        top_k: int = 10,
        tenant: str = "default",
        filters: dict | None = None,
    ) -> list[dict]:
        """Async recall memories."""
        client = self._get_async_client()
        try:
            response = await client.post(
                "/api/v1/memory/recall",
                json={
                    "query": query,
                    "top_k": top_k,
                    "tenant": tenant,
                    "filters": filters or {},
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", data.get("memories", []))
        except httpx.HTTPError as e:
            logger.error(f"Brain recall (async) failed: {e}")
            raise RuntimeError(f"SomaBrain recall failed: {e}") from e

    def health(self) -> dict:
        """Health check for SomaBrain service."""
        try:
            response = self._client.get("/health")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"status": "unhealthy", "error": str(e)}

    def close(self) -> None:
        """Close HTTP clients."""
        self._client.close()
        if self._async_client:
            # Note: async client should be closed in async context
            pass


# Singleton instance
_http_brain_adapter: HTTPBrainAdapter | None = None


def get_http_brain_adapter(
    base_url: str | None = None, timeout: float = 30.0
) -> HTTPBrainAdapter:
    """Get or create the singleton HTTPBrainAdapter."""
    global _http_brain_adapter
    if _http_brain_adapter is None:
        _http_brain_adapter = HTTPBrainAdapter(base_url=base_url, timeout=timeout)
    return _http_brain_adapter
