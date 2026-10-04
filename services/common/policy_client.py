"""Policy enforcement via OPA/OpenFGA."""

from __future__ import annotations

import logging
import os
from collections import OrderedDict
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from services.common.http_timeouts import httpx_timeout
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


def _policy_setting(name: str, default):
    """Resolve one policy knob through the real settings chain.

    Capsule -> AgentSetting -> SettingsModel -> schema default. Not
    os.environ: an operator-managed value must be CRUD-able, and a literal in
    the code is a value nobody can see or change.
    """
    from admin.core.helpers.settings import get_settings

    model = get_settings()
    value = getattr(model, name.lower(), None)
    return default if value in (None, "") else value



class PolicyClient:
    """Policyclient class implementation."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        tenant_config: Optional[TenantConfig] = None,
    ) -> None:
        """Initialize the instance."""

        default_base_url = (
            base_url or os.environ.get("SA01_POLICY_URL") or os.environ.get("SA01_OPA_URL")
        )
        if not default_base_url:
            # No policy engine attached. This is the normal Standalone case and
            # it must NOT grant anything: authorization is resolved by
            # role-based access control (admin.core.authz) and a policy engine,
            # when one is attached, may only narrow that. See evaluate().
            self.base_url = None
            self.data_path = "/v1/data/soma/allow"
            self._client = None
            self.cache_ttl = float(_policy_setting("POLICY_CACHE_TTL_S", 2.0))
            self.fail_open_default = False
            self._cache: OrderedDict = OrderedDict()
            self._cache_max = int(_policy_setting("POLICY_CACHE_MAX", 4096))
            self.tenant_config = tenant_config or TenantConfig()
            self._disabled = True
            return
        self._disabled = False
        # Robust URL handling: strip trailing /v1/data/soma or /v1/data/soma/allow
        # so we don't double-append the data path when env var includes it.
        _base = default_base_url.rstrip("/")
        if _base.endswith("/v1/data/soma/allow"):
            _base = _base[: -len("/v1/data/soma/allow")]
        elif _base.endswith("/v1/data/soma"):
            _base = _base[: -len("/v1/data/soma")]
        self.base_url = _base
        self.data_path = _policy_setting("POLICY_DATA_PATH", "/v1/data/soma/allow")
        self._client = httpx.AsyncClient(timeout=httpx_timeout())
        self.cache_ttl = float(_policy_setting("POLICY_CACHE_TTL_S", 2.0))
        # Fail-closed by default; POLICY_FAIL_OPEN is no longer honored
        self.fail_open_default = False
        self._cache: OrderedDict = OrderedDict()
        self._cache_max = int(_policy_setting("POLICY_CACHE_MAX", 4096))
        self.tenant_config = tenant_config or TenantConfig()

    @property
    def is_configured(self) -> bool:
        """True when a policy engine is attached and may express an opinion.

        When False, callers must decide authorization from role-based access
        control alone. They must not treat the absence of an engine as consent.
        """
        return not getattr(self, "_disabled", False)

    async def evaluate(self, request: PolicyRequest) -> bool:
        """Execute evaluate.

        Args:
            request: The request.

        Returns:
            bool: True only when the policy engine affirmatively allows.

        Note:
            FAIL-CLOSED. With no engine attached there is no affirmative
            decision to be had, so this denies. Previously it returned True
            here — that was an authentication bypass in every deployment
            without OPA, which is every Standalone install.
        """
        if getattr(self, "_disabled", False):
            LOGGER.error(
                "PolicyClient has no policy engine; denying (fail-closed). "
                "Role-based access control is the authority in this mode."
            )
            return False

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
            self._cache.move_to_end(cache_key)
            return cached[0]

        client = self._client
        if client is None or self.base_url is None:
            # Reachable only if construction left us without a transport while
            # not in standalone mode. Deny instead of inventing a client.
            LOGGER.error("PolicyClient is not initialised; denying (fail-closed)")
            return False
        url = f"{self.base_url.rstrip('/')}{self.data_path}"
        try:
            response = await client.post(url, json=payload)
            if response.status_code != 200:
                LOGGER.error(
                    "OPA request failed",
                    extra={"status": response.status_code, "body": response.text},
                )
                response.raise_for_status()
            data: dict[str, Any] = response.json()
            decision = bool(data.get("result"))
            self._cache[cache_key] = (decision, now)
            self._cache.move_to_end(cache_key)
            while len(self._cache) > self._cache_max:
                self._cache.popitem(last=False)
            return decision
        except Exception as exc:
            LOGGER.exception("Policy evaluation failed", extra={"error": str(exc)})
            # Fail-closed: deny when policy engine is unavailable or errors
            return False

    async def close(self) -> None:
        """Execute close."""

        # Standalone mode never opens a transport; there is nothing to close.
        if self._client is not None:
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
