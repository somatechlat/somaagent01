"""Budget manager for SomaAgent 01."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import redis.asyncio as redis

from services.common import env
from src.core.config import cfg
from services.common.tenant_config import TenantConfig


@dataclass
class BudgetResult:
    allowed: bool
    total_tokens: int
    limit_tokens: Optional[int]


class BudgetManager:
    def __init__(
        self, url: Optional[str] = None, tenant_config: Optional[TenantConfig] = None
    ) -> None:
        # Use centralized configuration for Redis URL, falling back to provided URL if given.
        raw_url = url or cfg.settings().redis.url
        self.url = env.expand(raw_url)
        self.prefix = env.get("BUDGET_PREFIX", "budget:tokens") or "budget:tokens"
        self.limit = env.get_int("BUDGET_LIMIT_TOKENS", 0)  # 0 = unlimited
        self.client = redis.from_url(self.url, decode_responses=True)
        self.tenant_config = tenant_config or TenantConfig()

    async def consume(self, tenant: str, persona_id: Optional[str], tokens: int) -> BudgetResult:
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
        key = self._key(tenant, persona_id)
        value = await self.client.get(key)
        return int(value or 0)

    def _key(self, tenant: str, persona_id: Optional[str]) -> str:
        persona = persona_id or "default"
        return f"{self.prefix}:{tenant}:{persona}:{self._current_window()}"

    def _current_window(self) -> str:
        # Simple daily window by default
        from datetime import datetime

        return datetime.utcnow().strftime("%Y%m%d")

    def _limit_for(self, tenant: str, persona_id: Optional[str]) -> Optional[int]:
        config_limit = self.tenant_config.get_budget_limit(tenant, persona_id)
        if config_limit is not None:
            return config_limit if config_limit > 0 else None

        env_key = f"BUDGET_LIMIT_{tenant.upper()}"
        persona_key = f"BUDGET_LIMIT_{tenant.upper()}_{(persona_id or 'DEFAULT').upper()}"
        persona_env = env.get(persona_key)
        if persona_env is not None:
            try:
                return int(persona_env) or None
            except ValueError:
                return None
        limit = env.get_int(env_key, 0)
        if limit == 0:
            limit = self.limit
        return limit or None
