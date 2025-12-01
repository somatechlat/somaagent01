"""PostgreSQL store for agent settings with Vault-based secret management.

Single source of truth:
- Non-sensitive settings → PostgreSQL (agent_settings table)
- Secrets/API keys → Vault via UnifiedSecretManager

No Redis secrets, no .env files, no fallbacks.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional

import asyncpg

from services.common.admin_settings import ADMIN_SETTINGS
from services.common.unified_secret_manager import get_secret_manager
from src.core.config import cfg

LOGGER = logging.getLogger(__name__)


class AgentSettingsStore:
    """PostgreSQL store for agent settings with Vault secrets."""

    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = dsn or ADMIN_SETTINGS.postgres_dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None
        self._secrets = get_secret_manager()

    async def _ensure_pool(self) -> asyncpg.Pool:
        """Create or retrieve asyncpg connection pool."""
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            try:
                self._pool = await asyncpg.create_pool(
                    self.dsn,
                    min_size=max(0, min_size),
                    max_size=max(1, max_size),
                )
            except OSError:
                import re
                fallback_dsn = re.sub(r"@[^:/]+", "@127.0.0.1", self.dsn)
                self._pool = await asyncpg.create_pool(
                    fallback_dsn,
                    min_size=max(0, min_size),
                    max_size=max(1, max_size),
                )
        return self._pool

    async def ensure_schema(self) -> None:
        """Create agent_settings table if not exists."""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_settings (
                    id SERIAL PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_agent_settings_key ON agent_settings(key);
            """)

    async def get_settings(self) -> Dict[str, Any]:
        """Get all agent settings (PostgreSQL + Vault secrets)."""
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT value FROM agent_settings WHERE key = 'global'"
            )
            settings = dict(row["value"]) if row and isinstance(row["value"], dict) else {}

        # Load API keys from Vault
        api_keys = {}
        for provider in self._secrets.list_providers():
            key = self._secrets.get_provider_key(provider)
            if key:
                api_keys[provider] = key
        if api_keys:
            settings["api_keys"] = api_keys

        # Load credentials from Vault
        for cred in ["auth_login", "auth_password", "rfc_password", "root_password"]:
            value = self._secrets.get_credential(cred)
            if value:
                settings[cred] = value

        return settings

    async def set_settings(self, settings: Dict[str, Any]) -> None:
        """Save agent settings (PostgreSQL + Vault secrets)."""
        settings_copy = settings.copy()

        # Extract and save secrets to Vault
        self._save_secrets(settings_copy)

        # Remove sensitive fields before PostgreSQL storage
        self._remove_sensitive_fields(settings_copy)

        # Save to PostgreSQL
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO agent_settings (key, value, updated_at)
                VALUES ('global', $1::jsonb, NOW())
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
            """, json.dumps(settings_copy, ensure_ascii=False))

        LOGGER.info("Agent settings saved", extra={"keys": list(settings_copy.keys())})

    async def get_field(self, key: str) -> Any:
        """Get single settings field."""
        settings = await self.get_settings()
        return settings.get(key)

    async def set_field(self, key: str, value: Any) -> None:
        """Set single settings field."""
        settings = await self.get_settings()
        settings[key] = value
        await self.set_settings(settings)

    def _save_secrets(self, settings: Dict[str, Any]) -> None:
        """Save secrets to Vault."""
        # API keys
        api_keys = settings.get("api_keys", {})
        for key, value in api_keys.items():
            if not isinstance(value, str) or not value.strip():
                continue
            if value in {"", "None", "************"}:
                continue
            provider = key.replace("api_key_", "") if key.startswith("api_key_") else key
            self._secrets.set_provider_key(provider, value.strip())

        # Credentials
        for cred in ["auth_login", "auth_password", "rfc_password", "root_password"]:
            value = settings.get(cred)
            if isinstance(value, str) and value.strip() and value not in {"************"}:
                self._secrets.set_credential(cred, value.strip())

    def _remove_sensitive_fields(self, settings: Dict[str, Any]) -> None:
        """Remove sensitive fields before PostgreSQL storage."""
        for field in ["api_keys", "auth_login", "auth_password", "rfc_password", "root_password", "secrets"]:
            settings.pop(field, None)


# Singleton
_store: Optional[AgentSettingsStore] = None


def get_agent_settings_store() -> AgentSettingsStore:
    """Get singleton AgentSettingsStore instance."""
    global _store
    if _store is None:
        _store = AgentSettingsStore()
    return _store
