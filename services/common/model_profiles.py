"""Model Profiles — per-role deployment configuration store.

VIBE Compliant: Real PostgreSQL-backed implementation.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import asyncpg

LOGGER = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    """A model profile maps a role + deployment mode to an LLM config."""

    role: str
    deployment_mode: str
    config: Dict[str, Any]


class ModelProfileStore:
    """PostgreSQL-backed store for model profiles."""

    TABLE_NAME = "model_profiles"

    def __init__(self, dsn: Optional[str] = None) -> None:
        """Initialize the store.

        Args:
            dsn: PostgreSQL connection string.
        """
        self.dsn = dsn or os.environ.get("SA01_DB_DSN", "")

    @classmethod
    def from_env(cls) -> "ModelProfileStore":
        """Create a store from the environment."""
        return cls()

    async def _get_pool(self) -> Any:
        """Get or create a connection pool."""
        return await asyncpg.create_pool(self.dsn, min_size=1, max_size=2)

    async def ensure_schema(self) -> None:
        """Ensure the profiles table exists."""
        if not self.dsn:
            raise RuntimeError("ModelProfileStore: SA01_DB_DSN not configured")
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                        role TEXT NOT NULL,
                        deployment_mode TEXT NOT NULL,
                        config JSONB NOT NULL DEFAULT '{{}}',
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW(),
                        PRIMARY KEY (role, deployment_mode)
                    )
                    """
                )
            await pool.close()
        except Exception as exc:
            LOGGER.warning("ModelProfileStore.ensure_schema failed: %s", exc)

    async def list(self) -> List[ModelProfile]:
        """List all stored profiles."""
        if not self.dsn:
            raise RuntimeError("ModelProfileStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    f"SELECT role, deployment_mode, config FROM {self.TABLE_NAME}"
                )
                return [
                    ModelProfile(
                        role=r["role"],
                        deployment_mode=r["deployment_mode"],
                        config=(
                            json.loads(r["config"]) if isinstance(r["config"], str) else r["config"]
                        ),
                    )
                    for r in rows
                ]
        finally:
            await pool.close()

    async def upsert(self, profile: ModelProfile) -> None:
        """Insert or update a profile."""
        if not self.dsn:
            raise RuntimeError("ModelProfileStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.TABLE_NAME} (role, deployment_mode, config, updated_at)
                    VALUES ($1, $2, $3, NOW())
                    ON CONFLICT (role, deployment_mode)
                    DO UPDATE SET config = EXCLUDED.config, updated_at = NOW()
                    """,
                    profile.role,
                    profile.deployment_mode,
                    json.dumps(profile.config),
                )
        finally:
            await pool.close()

    async def delete(self, role: str, deployment_mode: str) -> bool:
        """Delete a profile. Returns True if a row was deleted."""
        if not self.dsn:
            raise RuntimeError("ModelProfileStore: SA01_DB_DSN not configured")
        pool = await self._get_pool()
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self.TABLE_NAME} WHERE role = $1 AND deployment_mode = $2",
                    role,
                    deployment_mode,
                )
                # asyncpg returns "DELETE N" where N is row count
                return result != "DELETE 0"
        finally:
            await pool.close()
