"""Policy enforcement via OPA/OpenFGA."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from services.common.tenant_config import TenantConfig
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


@dataclass
class PolicyRequest:
    tenant: str
    persona_id: Optional[str]
    action: str
    resource: str
    context: dict[str, Any]


class PolicyClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        tenant_config: Optional[TenantConfig] = None,
    ) -> None:
        config = cfg.settings()
        default_base_url = getattr(getattr(config, "external", None), "opa_url", None) or cfg.env(
            "SA01_POLICY_URL"
        )
        if not base_url and not default_base_url:
            raise ValueError("SA01_POLICY_URL is required. No hardcoded defaults per VIBE rules.")
        self.base_url = base_url or default_base_url
        self.data_path = (
            cfg.env("SA01_POLICY_DATA_PATH", "/v1/data/soma/allow") or "/v1/data/soma/allow"
        )
        self._client = httpx.AsyncClient(timeout=10.0)
        self.cache_ttl = float(cfg.env("SA01_POLICY_CACHE_TTL", "2") or "2")
        # Fail-closed by default; POLICY_FAIL_OPEN is no longer honored
        self.fail_open_default = False
        self._cache: dict[tuple[Any, ...], tuple[bool, float]] = {}
        self.tenant_config = tenant_config or TenantConfig()

    async def evaluate(self, request: PolicyRequest) -> bool:
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
        await self._client.aclose()

    def _cache_key(self, request: PolicyRequest) -> tuple[Any, ...]:
        context_items = tuple(sorted((k, self._freeze(v)) for k, v in request.context.items()))
        return (
            request.tenant,
            request.persona_id,
            request.action,
            request.resource,
            context_items,
        )

    def _freeze(self, value: Any) -> Any:
        if isinstance(value, dict):
            return tuple(sorted((k, self._freeze(v)) for k, v in value.items()))
        if isinstance(value, list):
            return tuple(self._freeze(v) for v in value)
        return value
