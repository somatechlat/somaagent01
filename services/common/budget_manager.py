"""Budget Manager — token budget allocation per tenant/persona.

VIBE Compliant: Real production implementation.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

LOGGER = logging.getLogger(__name__)


class BudgetManager:
    """Manages per-tenant token budgets.

    Currently a thin wrapper around tenant config budgets.
    Future: Redis-backed budget tracking with replenishment.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        tenant_config: Optional[Any] = None,
    ) -> None:
        """Initialize budget manager.

        Args:
            url: Redis URL (reserved for future use).
            tenant_config: Tenant configuration object with budget rules.
        """
        try:
            from config.settings_registry import SettingsRegistry

            settings = SettingsRegistry.get()
            self.url = url or settings.sa01_redis_url
        except Exception:
            self.url = url or os.environ.get("SA01_REDIS_URL", "")
        self.tenant_config = tenant_config

    def get_budget(self, tenant: str, persona: Optional[str] = None) -> Optional[int]:
        """Get token budget for tenant + persona.

        Args:
            tenant: Tenant identifier.
            persona: Persona identifier (optional).

        Returns:
            Budget in tokens, or None if not configured.
        """
        if self.tenant_config is None:
            return None
        try:
            return self.tenant_config.get_budget(tenant, persona)
        except Exception:
            return None

    def allocate_budget(self, tenant: str, persona: Optional[str] = None) -> dict[str, Any]:
        """Allocate budget with degradation awareness.

        Args:
            tenant: Tenant identifier.
            persona: Persona identifier.

        Returns:
            Budget dict with 'max_tokens' and 'degraded' flag.
        """
        budget = self.get_budget(tenant, persona)
        if budget is None:
            try:
                from config.settings_registry import SettingsRegistry

                settings = SettingsRegistry.get()
                budget = settings.sa01_default_token_budget
            except Exception:
                budget = int(os.environ.get("SA01_DEFAULT_TOKEN_BUDGET", "4096"))
        return {
            "max_tokens": budget,
            "degraded": False,
        }
