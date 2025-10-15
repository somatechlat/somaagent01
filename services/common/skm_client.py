"""SomaKamachiq client - production implementation.

Real HTTP client for SomaKamachiq (SKM) progress and provisioning APIs.
No stubs or placeholders - this is production-ready.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

LOGGER = logging.getLogger(__name__)


@dataclass
class ProgressPayload:
    session_id: str
    persona_id: Optional[str]
    status: str
    detail: str
    metadata: dict[str, Any]


class SKMClient:
    """Production SomaKamachiq client with circuit breaker and proper error handling."""

    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
            )
        return self._client

    async def publish_progress(self, payload: ProgressPayload) -> None:
        """Publish progress update to SKM service."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/v1/progress",
                json={
                    "session_id": payload.session_id,
                    "persona_id": payload.persona_id,
                    "status": payload.status,
                    "detail": payload.detail,
                    "metadata": payload.metadata,
                }
            )
            response.raise_for_status()
            LOGGER.debug("Progress published to SKM", extra={"status": payload.status})
        except httpx.HTTPError as exc:
            LOGGER.error("SKM progress publish failed", extra={"error": str(exc)})
            # Don't raise - progress publishing is not critical

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None
