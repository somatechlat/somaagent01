"""Async OpenFGA client wrapper with lightweight caching."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import httpx

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


class OpenFGAError(RuntimeError):
    """Raised when OpenFGA cannot process a request."""


@dataclass(frozen=True)
class AuthorizationKey:
    tenant: str
    subject: str
    relation: str
    action: str


class OpenFGAClient:
    """Minimal async wrapper around the OpenFGA HTTP API."""

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        store_id: Optional[str] = None,
        user_namespace: str = "user",
        tenant_namespace: str = "tenant",
        relation: str = "member",
        action: str = "access",
        timeout_seconds: float = 3.0,
        cache_ttl: float = 2.0,
        fail_open: bool = True,
    ) -> None:
        self.base_url = base_url or cfg.env("OPENFGA_API_URL", "http://openfga:8080") or "http://openfga:8080"
        self.store_id = store_id or cfg.env("OPENFGA_STORE_ID")
        if not self.store_id:
            raise ValueError("OPENFGA_STORE_ID must be configured for OpenFGAClient")
        self.user_namespace = user_namespace
        self.tenant_namespace = tenant_namespace
        self.relation = relation
        self.action = action
        self.fail_open = fail_open
        timeout = float(cfg.env("OPENFGA_TIMEOUT_SECONDS", str(timeout_seconds)) or timeout_seconds)
        self._client = httpx.AsyncClient(timeout=timeout)
        self._cache: Dict[AuthorizationKey, Tuple[bool, float]] = {}
        self._cache_lock = asyncio.Lock()
        self.cache_ttl = float(cfg.env("OPENFGA_CACHE_TTL", str(cache_ttl)) or cache_ttl)

    async def check_tenant_access(
        self,
        *,
        tenant: str,
        subject: str,
        relation: Optional[str] = None,
        action: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Return True if *subject* has relation/action on a tenant."""

        relation_name = relation or self.relation
        action_name = action or self.action
        cache_key = AuthorizationKey(tenant, subject, relation_name, action_name)

        async with self._cache_lock:
            cached = self._cache.get(cache_key)
            now = time.time()
            if cached and (now - cached[1]) < self.cache_ttl:
                return cached[0]

        tuple_key = {
            "user": f"{self.user_namespace}:{subject}",
            "relation": relation_name,
            "object": f"{self.tenant_namespace}:{tenant}",
        }

        url = f"{self.base_url.rstrip('/')}/stores/{self.store_id}/check"
        payload = {"tuple_key": tuple_key, "context": context or {}, "authorization_model_id": None}

        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
        except Exception as exc:
            LOGGER.error(
                "OpenFGA check failed",
                extra={
                    "tenant": tenant,
                    "subject": subject,
                    "relation": relation_name,
                    "action": action_name,
                    "error": str(exc),
                },
            )
            if self.fail_open:
                return True
            raise OpenFGAError("OpenFGA authorization failed") from exc

        data = response.json()
        allowed = bool(data.get("allowed"))

        async with self._cache_lock:
            self._cache[cache_key] = (allowed, time.time())
        return allowed

    async def close(self) -> None:
        await self._client.aclose()

    def clear_cache(self) -> None:
        self._cache.clear()

_FGA_CLIENT: OpenFGAClient | None = None

def _get_openfga_client() -> OpenFGAClient:
    """Return a singleton OpenFGA client."""
    global _FGA_CLIENT
    if _FGA_CLIENT is None:
        _FGA_CLIENT = OpenFGAClient()
    return _FGA_CLIENT
