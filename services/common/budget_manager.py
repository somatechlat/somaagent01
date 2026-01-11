"""Budget manager for SomaAgent 01."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis

from services.common.tenant_config import TenantConfig


def _int_from_env(name: str, default: int) -> int:
    """Execute int from env.

    Args:
        name: The name.
        default: The default.
    """

    raw = os.environ.get(name, str(default))
    try:
        return int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default


@dataclass
class BudgetResult:
    """Budgetresult class implementation."""

    allowed: bool
    total_tokens: int
    limit_tokens: Optional[int]


class BudgetManager:
    """Budgetmanager class implementation."""

    def __init__(
        self, url: Optional[str] = None, tenant_config: Optional[TenantConfig] = None
    ) -> None:
        # Use centralized configuration for Redis URL, falling back to provided URL if given.
        """Initialize the instance."""

        default_url = os.environ.get("SA01_REDIS_URL", "")
        raw_url = url or os.environ.get("REDIS_URL", default_url) or default_url
        self.url = os.path.expandvars(raw_url)
        self.prefix = os.environ.get("BUDGET_PREFIX", "budget:tokens") or "budget:tokens"
        self.limit = _int_from_env("BUDGET_LIMIT_TOKENS", 0)  # 0 = unlimited
        self.client = redis.from_url(self.url, decode_responses=True)
        self.tenant_config = tenant_config or TenantConfig()

    async def consume(self, tenant: str, persona_id: Optional[str], tokens: int) -> BudgetResult:
        """Execute consume.

        Args:
            tenant: The tenant.
            persona_id: The persona_id.
            tokens: The tokens.
        """

        if tokens <= 0:
            current = await self._get_total(tenant, persona_id)
            return BudgetResult(True, current, self._limit_for(tenant, persona_id))

        key = self._key(tenant, persona_id)
        total = await self.client.incrby(key, tokens)
        limit = self._limit_for(tenant, persona_id)
        if limit and total > limit:
            return BudgetResult(False, total, limit)
        return BudgetResult(True, total, limit)

    async def _get_total(self, tenant: str, persona_id: Optional[str]) -> int:
        """Execute get total.

        Args:
            tenant: The tenant.
            persona_id: The persona_id.
        """

        key = self._key(tenant, persona_id)
        value = await self.client.get(key)
        return int(value or 0)

    def _key(self, tenant: str, persona_id: Optional[str]) -> str:
        """Execute key.

        Args:
            tenant: The tenant.
            persona_id: The persona_id.
        """

        persona = persona_id or "default"
        return f"{self.prefix}:{tenant}:{persona}:{self._current_window()}"

    def _current_window(self) -> str:
        # Simple daily window by default
        """Execute current window."""

        from datetime import datetime, timezone

        return datetime.now(timezone.utc).strftime("%Y%m%d")

    def _limit_for(self, tenant: str, persona_id: Optional[str]) -> Optional[int]:
        """Execute limit for.

        Args:
            tenant: The tenant.
            persona_id: The persona_id.
        """

        config_limit = self.tenant_config.get_budget_limit(tenant, persona_id)
        if config_limit is not None:
            return config_limit if config_limit > 0 else None

        env_key = f"BUDGET_LIMIT_{tenant.upper()}"
        persona_key = f"BUDGET_LIMIT_{tenant.upper()}_{(persona_id or 'DEFAULT').upper()}"
        persona_env = os.environ.get(persona_key)
        if persona_env is not None:
            try:
                return int(persona_env) or None
            except ValueError:
                return None
        limit = _int_from_env(env_key, 0)
        if limit == 0:
            limit = self.limit
        return limit or None
