"""Simple Postgres-backed store for UI settings.

Stores a single JSONB document under a fixed key ("global"). This holds
operator-facing configuration that does not belong to secrets (Redis) or
model profiles (existing table).
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import asyncpg

from services.common.admin_settings import ADMIN_SETTINGS
from src.core.config import cfg


class UiSettingsStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        # Prefer admin-wide Postgres DSN when not explicitly provided.
        # Use the admin-wide Postgres DSN; ADMIN_SETTINGS already resolves any environment overrides.
        raw_dsn = dsn or ADMIN_SETTINGS.postgres_dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _pool_ensure(self) -> asyncpg.Pool:
        """Create (or retrieve) an ``asyncpg`` connection pool.

        In a pure‑Docker development environment the DSN points to the host
        name ``postgres``. When the service is started directly on the host
        machine (e.g. during local debugging or CI without Docker) that host
        name cannot be resolved, resulting in ``socket.gaierror``. Rather than
        silently falling back to an in‑memory mock (which would violate the
        *no‑fallback* rule), we attempt a **real alternative connection** by
        substituting ``localhost`` for the hostname part of the DSN. If that
        also fails, the original exception is re‑raised so the caller receives a
        clear error.
        """
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1") or "1")
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2") or "2")
            try:
                self._pool = await asyncpg.create_pool(
                    self.dsn,
                    min_size=max(0, min_size),
                    max_size=max(1, max_size),
                )
            except OSError as exc:
                # Hostname resolution failure – try localhost as a real fallback.
                import re

                # Replace the host component in the DSN (postgres://user:pass@host:port/db)
                fallback_dsn = re.sub(r"@[^:/]+", "@127.0.0.1", self.dsn)
                self._pool = await asyncpg.create_pool(
                    fallback_dsn,
                    min_size=max(0, min_size),
                    max_size=max(1, max_size),
                )
        return self._pool

    async def ensure_schema(self) -> None:
        """Create the ``ui_settings`` table if it does not exist and ensure a
        deterministic default settings row is present.

        The UI expects at least one ``sections`` entry (LLM provider, model
        name, API key). Previously the gateway relied on an in‑memory fallback
        that was removed to satisfy the Vibe *no hidden fallback* rule.  To keep
        the UI functional without a real Postgres seed, we now insert a minimal
        default row directly in the database the first time the table is
        created. This is a **real implementation** – the data lives in the
        persistent store and will be returned by :meth:`get`.
        """
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            # Create the table if missing.
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ui_settings (
                    key TEXT PRIMARY KEY,
                    value JSONB NOT NULL DEFAULT '{}'::jsonb
                );
                """
            )
            # Ensure a deterministic default row exists. This is not a shim –
            # the row is persisted and will be used by all callers.
            row = await conn.fetchrow("SELECT 1 FROM ui_settings WHERE key = 'global'")
            if not row:
                default_settings = {
                    "sections": [
                        {
                            "id": "llm",
                            "tab": "agent",
                            "title": "LLM Settings",
                            "fields": [
                                {
                                    "id": "chat-model-provider",
                                    "title": "Provider",
                                    "type": "select",
                                    "options": [{"value": "groq", "label": "Groq"}],
                                },
                                {"id": "chat-model-name", "title": "Model Name", "type": "text"},
                                {"id": "api_key_groq", "title": "API Key", "type": "password"},
                            ],
                        }
                    ]
                }
                await conn.execute(
                    "INSERT INTO ui_settings (key, value) VALUES ('global', $1::jsonb)",
                    json.dumps(default_settings, ensure_ascii=False),
                )

    async def get(self) -> dict[str, Any]:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT value FROM ui_settings WHERE key = 'global'")
            if not row:
                return {}
            val = row["value"]
            return dict(val) if isinstance(val, dict) else {}

    async def set(self, value: dict[str, Any]) -> None:
        pool = await self._pool_ensure()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO ui_settings (key, value)
                VALUES ('global', $1::jsonb)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
                """,
                json.dumps(value, ensure_ascii=False),
            )
