"""
HTTP Memory Adapter - Network Access to SomaFractalMemory.

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

from services.common.protocols import MemoryServiceProtocol

logger = logging.getLogger(__name__)


class HTTPMemoryAdapter:
    """
    HTTP-based memory adapter for distributed mode.

    Communicates with SomaFractalMemory via HTTP REST API.
    Latency: ~5-50ms per call depending on network.
    """

    def __init__(
        self,
        namespace: str = "default",
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize HTTP client for SomaFractalMemory."""
        logger.info("🌐 HTTPMemoryAdapter: Initializing HTTP mode (distributed)")

        self._namespace = namespace
        self._base_url = base_url or os.environ.get(
            "SOMAFRACTALMEMORY_URL",
            os.environ.get("SOMA_MEMORY_URL", "http://localhost:10101"),
        )
        self._timeout = timeout
        self._api_token = os.environ.get("SOMA_API_TOKEN", "")

        # Configure client with auth header
        headers = {}
        if self._api_token:
            headers["Authorization"] = f"Bearer {self._api_token}"

        self._client = httpx.Client(
            base_url=self._base_url, timeout=timeout, headers=headers
        )
        self._async_client: httpx.AsyncClient | None = None

        logger.info(f"✅ HTTPMemoryAdapter initialized: {self._base_url}")

    def _get_async_client(self) -> httpx.AsyncClient:
        """Lazy initialize async client."""
        if self._async_client is None:
            headers = {}
            if self._api_token:
                headers["Authorization"] = f"Bearer {self._api_token}"
            self._async_client = httpx.AsyncClient(
                base_url=self._base_url, timeout=self._timeout, headers=headers
            )
        return self._async_client

    def store(
        self,
        coordinate: tuple[float, ...],
        payload: dict,
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> dict:
        """Store data at a coordinate via HTTP."""
        ns = namespace or self._namespace
        try:
            response = self._client.post(
                "/api/v1/store",
                json={
                    "coordinate": list(coordinate),
                    "payload": payload,
                    "tenant": tenant,
                    "namespace": ns,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Memory store failed: {e}")
            raise RuntimeError(f"SomaFractalMemory store failed: {e}") from e

    def search(
        self,
        query: str | list[float],
        *,
        top_k: int = 10,
        tenant: str = "default",
        namespace: str | None = None,
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors via HTTP."""
        ns = namespace or self._namespace
        try:
            # Handle both text and vector queries
            if isinstance(query, str):
                body = {"query": query, "top_k": top_k, "tenant": tenant, "namespace": ns}
            else:
                body = {"vector": query, "top_k": top_k, "tenant": tenant, "namespace": ns}

            if filters:
                body["filters"] = filters

            response = self._client.post("/api/v1/search", json=body)
            response.raise_for_status()
            data = response.json()
            return data.get("results", data.get("matches", []))
        except httpx.HTTPError as e:
            logger.error(f"Memory search failed: {e}")
            raise RuntimeError(f"SomaFractalMemory search failed: {e}") from e

    def get(
        self,
        coordinate: tuple[float, ...],
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> dict | None:
        """Get data at a specific coordinate via HTTP."""
        ns = namespace or self._namespace
        try:
            response = self._client.post(
                "/api/v1/get",
                json={
                    "coordinate": list(coordinate),
                    "tenant": tenant,
                    "namespace": ns,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("result")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            logger.error(f"Memory get failed: {e}")
            raise RuntimeError(f"SomaFractalMemory get failed: {e}") from e
        except httpx.HTTPError as e:
            logger.error(f"Memory get failed: {e}")
            raise RuntimeError(f"SomaFractalMemory get failed: {e}") from e

    def delete(
        self,
        coordinate: tuple[float, ...],
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> bool:
        """Delete data at a coordinate via HTTP."""
        ns = namespace or self._namespace
        try:
            response = self._client.post(
                "/api/v1/delete",
                json={
                    "coordinate": list(coordinate),
                    "tenant": tenant,
                    "namespace": ns,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data.get("deleted", False)
        except httpx.HTTPError as e:
            logger.error(f"Memory delete failed: {e}")
            return False

    def health(self) -> dict:
        """Health check for SomaFractalMemory service."""
        try:
            response = self._client.get("/healthz")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {"status": "unhealthy", "error": str(e)}

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
        ns = namespace or self._namespace
        client = self._get_async_client()
        try:
            if isinstance(query, str):
                body = {"query": query, "top_k": top_k, "tenant": tenant, "namespace": ns}
            else:
                body = {"vector": query, "top_k": top_k, "tenant": tenant, "namespace": ns}

            if filters:
                body["filters"] = filters

            response = await client.post("/api/v1/search", json=body)
            response.raise_for_status()
            data = response.json()
            return data.get("results", data.get("matches", []))
        except httpx.HTTPError as e:
            logger.error(f"Memory search (async) failed: {e}")
            raise RuntimeError(f"SomaFractalMemory search failed: {e}") from e

    async def store_async(
        self,
        coordinate: tuple[float, ...],
        payload: dict,
        *,
        tenant: str = "default",
        namespace: str | None = None,
    ) -> dict:
        """Async store data at a coordinate."""
        ns = namespace or self._namespace
        client = self._get_async_client()
        try:
            response = await client.post(
                "/api/v1/store",
                json={
                    "coordinate": list(coordinate),
                    "payload": payload,
                    "tenant": tenant,
                    "namespace": ns,
                },
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Memory store (async) failed: {e}")
            raise RuntimeError(f"SomaFractalMemory store failed: {e}") from e

    def close(self) -> None:
        """Close HTTP clients."""
        self._client.close()
        if self._async_client:
            pass


# Singleton instance
_http_memory_adapter: HTTPMemoryAdapter | None = None


def get_http_memory_adapter(
    namespace: str = "default",
    base_url: str | None = None,
    timeout: float = 30.0,
) -> HTTPMemoryAdapter:
    """Get or create the singleton HTTPMemoryAdapter."""
    global _http_memory_adapter
    if _http_memory_adapter is None:
        _http_memory_adapter = HTTPMemoryAdapter(
            namespace=namespace, base_url=base_url, timeout=timeout
        )
    return _http_memory_adapter
