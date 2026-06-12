"""Policy enforcement via OPA/OpenFGA."""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from services.common.tenant_config import TenantConfig

LOGGER = logging.getLogger(__name__)


@dataclass
class PolicyRequest:
    """Data model for PolicyRequest."""

    tenant: str
    persona_id: Optional[str]
    action: str
    resource: str
    context: dict[str, Any]


class PolicyClient:
    """Policyclient class implementation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        tenant_config: Optional[TenantConfig] = None,
    ) -> None:
        """Initialize the instance."""

        default_base_url = (
            base_url
            or os.environ.get("SA01_POLICY_URL")
            or os.environ.get("SA01_OPA_URL")
        )
        if not default_base_url:
            raise ValueError(
                "SA01_POLICY_URL or SA01_OPA_URL is required. No hardcoded defaults per VIBE rules."
            )
        # Robust URL handling: strip trailing /v1/data/soma or /v1/data/soma/allow
        # so we don't double-append the data path when env var includes it.
        _base = default_base_url.rstrip("/")
        if _base.endswith("/v1/data/soma/allow"):
            _base = _base[: -len("/v1/data/soma/allow")]
        elif _base.endswith("/v1/data/soma"):
            _base = _base[: -len("/v1/data/soma")]
        self.base_url = _base
        self.data_path = (
            os.environ.get("SA01_POLICY_DATA_PATH", "/v1/data/soma/allow")
            or "/v1/data/soma/allow"
        )
        self._client = httpx.AsyncClient(timeout=10.0)
        self.cache_ttl = float(os.environ.get("SA01_POLICY_CACHE_TTL", "2") or "2")
        # Fail-closed by default; POLICY_FAIL_OPEN is no longer honored
        self.fail_open_default = False
        self._cache: dict[tuple[Any, ...], tuple[bool, float]] = {}
        self.tenant_config = tenant_config or TenantConfig()

    async def evaluate(self, request: PolicyRequest) -> bool:
        """Execute evaluate.

        Args:
            request: The request.
        """

        payload = {
            "input": {
                "tenant": request.tenant,
                "persona_id": request.persona_id,
                "action": request.action,
                "resource": request.resource,
                "context": request.context,
            }
        }

        cache_key = self._cache_key(request)
        now = time.time()
        cached = self._cache.get(cache_key)
        if cached and (now - cached[1]) < self.cache_ttl:
            return cached[0]

        assert self.base_url is not None
        url = f"{self.base_url.rstrip('/')}{self.data_path}"
        try:
            response = await self._client.post(url, json=payload)
            if response.status_code != 200:
                LOGGER.error(
                    "OPA request failed",
                    extra={"status": response.status_code, "body": response.text},
                )
                response.raise_for_status()
            data: dict[str, Any] = response.json()
            decision = bool(data.get("result"))
            self._cache[cache_key] = (decision, now)
            return decision
        except Exception as exc:
            LOGGER.exception("Policy evaluation failed", extra={"error": str(exc)})
            # Fail-closed: deny when policy engine is unavailable or errors
            return False

    async def close(self) -> None:
        """Execute close."""

        await self._client.aclose()

    def _cache_key(self, request: PolicyRequest) -> tuple[Any, ...]:
        """Execute cache key.

        Args:
            request: The request.
        """

        context_items = tuple(sorted((k, self._freeze(v)) for k, v in request.context.items()))
        return (
            request.tenant,
            request.persona_id,
            request.action,
            request.resource,
            context_items,
        )

    def _freeze(self, value: Any) -> Any:
        """Execute freeze.

        Args:
            value: The value.
        """

        if isinstance(value, dict):
            return tuple(sorted((k, self._freeze(v)) for k, v in value.items()))
        if isinstance(value, list):
            return tuple(self._freeze(v) for v in value)
        return value


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_policy_client_instance: Optional[PolicyClient] = None


def get_policy_client() -> PolicyClient:
    """Get or create the singleton PolicyClient.

    Usage:
        client = get_policy_client()
        allowed = await client.evaluate(PolicyRequest(...))
    """
    global _policy_client_instance
    if _policy_client_instance is None:
        _policy_client_instance = PolicyClient()
    return _policy_client_instance


__all__ = [
    "PolicyClient",
    "PolicyRequest",
    "get_policy_client",
]
