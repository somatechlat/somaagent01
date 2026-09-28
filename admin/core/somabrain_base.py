"""SomaBrain Client - Base HTTP client

Production-grade HTTP client for SomaBrain memory service.
100% Django patterns - No FastAPI, No SQLAlchemy.


- Rule 1: NO BULLSHIT - Real implementation, no mocks
- Rule 4: REAL IMPLEMENTATIONS ONLY
- Rule 8: Django/Ninja ONLY
- Rule 13: CENTRALIZED SETTINGS
- Rule 32: HYBRID CONFIGURATION STANDARD
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, cast, Dict, List, Optional

import httpx
from django.conf import settings

from services.common.circuit_breaker import CircuitBreakerError, get_circuit_breaker


LOGGER = logging.getLogger(__name__)


class SomaClientError(Exception):
    """Exception raised for SomaBrain client errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize the instance."""

        super().__init__(message)
        self.status_code = status_code


class SomaMemoryRecord:
    """Lightweight record for SomaBrain memory retrieval results."""

    def __init__(
        self,
        identifier: str,
        payload: Dict[str, Any],
        score: Optional[float] = None,
        coordinate: Optional[List[float]] = None,
        retriever: Optional[str] = None,
    ) -> None:
        """Initialize the instance."""

        self.identifier = identifier
        self.payload = payload
        self.score = score
        self.coordinate = coordinate
        self.retriever = retriever


class _SomaBrainBaseClient:
    """Production SomaBrain HTTP client.

    Thread-safe singleton pattern for connection pooling.
    Uses Django settings for configuration.
    """

    _instance: Optional[_SomaBrainBaseClient] = None
    _lock: asyncio.Lock = asyncio.Lock()

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize SomaBrain client.

        Args:
            base_url: SomaBrain API base URL (defaults to settings)
            timeout: Request timeout in seconds
        """
        self._base_url = base_url or self._get_base_url()
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @staticmethod
    def _get_base_url() -> Optional[str]:
        """Get SomaBrain URL from Django settings or environment.

        Implements
        Prioritizes Django settings, falls back to environment.
        Returns None when disabled (standalone mode).
        """

        # Try Django settings first
        if hasattr(settings, "SOMABRAIN_URL"):
            url = str(settings.SOMABRAIN_URL)
            if url:
                return url

        # Fallback to environment variable
        env_url = os.environ.get("SOMABRAIN_URL")
        if env_url:
            return env_url

        # Disabled in standalone mode
        return None

    @classmethod
    def get(cls) -> Optional[SomaBrainClient]:
        """Get or create singleton instance.

        Returns None when SomaBrain is not configured (standalone mode).
        Callers must check the return value before use.
        """
        if cls._get_base_url() is None:
            return None
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    async def get_async(cls) -> Optional[SomaBrainClient]:
        """Get or create singleton instance (async version).

        Returns None when SomaBrain is not configured (standalone mode).
        Callers must check the return value before use.
        """
        if cls._get_base_url() is None:
            return None
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @property
    def is_enabled(self) -> bool:
        """Return True when the client has a configured base URL."""
        return bool(self._base_url)

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if not self._base_url:
            raise SomaClientError("SomaBrain is not configured", status_code=503)
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={"Content-Type": "application/json"},
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to SomaBrain.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., "/v1/memory/recall")
            json: JSON body for POST/PUT
            params: Query parameters
            headers: Additional HTTP headers

        Returns:
            Response JSON as dict

        Raises:
            SomaClientError: On HTTP or connection errors
            CircuitBreakerError: If circuit breaker is OPEN
        """
        if not self._base_url:
            raise SomaClientError("SomaBrain is not configured", status_code=503)

        breaker = get_circuit_breaker("somabrain_http", failure_threshold=5, reset_timeout=30)

        async def _do_request() -> Dict[str, Any]:
            client = await self._ensure_client()
            request_headers = headers or {}
            response = await client.request(method, path, json=json, params=params, headers=request_headers)
            response.raise_for_status()
            return response.json()

        try:
            return cast(Dict[str, Any], await breaker.call(_do_request))
        except CircuitBreakerError as e:
            LOGGER.error("SomaBrain circuit breaker OPEN", extra={"path": path, "error": str(e)})
            raise SomaClientError(
                f"SomaBrain unavailable (circuit open): {e}", status_code=503
            ) from e
        except httpx.HTTPStatusError as e:
            LOGGER.error(
                "SomaBrain HTTP error",
                extra={"path": path, "status": e.response.status_code},
            )
            raise SomaClientError(
                f"HTTP {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            LOGGER.error("SomaBrain connection error", extra={"path": path, "error": str(e)})
            raise SomaClientError(f"Connection error: {e}") from e
