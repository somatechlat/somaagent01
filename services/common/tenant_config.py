"""Tenant configuration loader for budgets and governance settings."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Optional

import yaml


@dataclass
class TenantSettings:
    """Tenantsettings class implementation."""

    fail_open: bool = True
    budgets: Dict[str, int] = field(default_factory=dict)
    routing_allow: list[str] = field(default_factory=list)
    routing_deny: list[str] = field(default_factory=list)


class TenantConfig:
    """Loads tenant configuration from YAML with simple caching."""

    def __init__(self, path: Optional[str] = None) -> None:
        """Initialize the instance."""

        self.path = path or os.environ.get("TENANT_CONFIG_PATH", "conf/tenants.yaml")
        self._cache: dict[str, TenantSettings] | None = None
        self._mtime: float | None = None

    def get_settings(self, tenant: str) -> TenantSettings:
        """Retrieve settings.

            Args:
                tenant: The tenant.
            """

        data = self._load()
        return data.get(tenant, data.get("default", TenantSettings()))

    def get_fail_open(self, tenant: str) -> bool:
        """Retrieve fail open.

            Args:
                tenant: The tenant.
            """

        return self.get_settings(tenant).fail_open

    def get_budget_limit(self, tenant: str, persona_id: Optional[str]) -> Optional[int]:
        """Retrieve budget limit.

            Args:
                tenant: The tenant.
                persona_id: The persona_id.
            """

        settings = self.get_settings(tenant)
        budgets = settings.budgets
        if not budgets:
            return None
        persona_key = (persona_id or "default").lower()
        if persona_key in budgets and budgets[persona_key] > 0:
            return budgets[persona_key]
        default = budgets.get("default", 0)
        return default or None

    def get_routing_policy(self, tenant: str) -> tuple[list[str], list[str]]:
        """Retrieve routing policy.

            Args:
                tenant: The tenant.
            """

        settings = self.get_settings(tenant)
        return settings.routing_allow, settings.routing_deny

    def _load(self) -> dict[str, TenantSettings]:
        """Execute load.
            """

        if not os.path.exists(self.path):
            return {"default": TenantSettings()}
        mtime = os.path.getmtime(self.path)
        if self._cache is not None and self._mtime == mtime:
            return self._cache
        with open(self.path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        parsed: dict[str, TenantSettings] = {}
        for tenant, values in raw.items():
            if not isinstance(values, dict):
                continue
            settings = TenantSettings()
            settings.fail_open = bool(values.get("fail_open", True))
            budgets = values.get("budgets", {})
            if isinstance(budgets, dict):
                settings.budgets = {
                    str(key).lower(): int(value)
                    for key, value in budgets.items()
                    if isinstance(value, (int, float))
                }
            routing = values.get("routing", {})
            if isinstance(routing, dict):
                allow = routing.get("allow", [])
                deny = routing.get("deny", [])
                if isinstance(allow, list):
                    settings.routing_allow = [str(item) for item in allow]
                if isinstance(deny, list):
                    settings.routing_deny = [str(item) for item in deny]
            parsed[str(tenant)] = settings
        if "default" not in parsed:
            parsed["default"] = TenantSettings()
        self._cache = parsed
        self._mtime = mtime
        return parsed