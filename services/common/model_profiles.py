"""Model profile storage for SomaAgent 01."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

import asyncpg

from services.common.settings_base import BaseServiceSettings

LOGGER = logging.getLogger(__name__)


@dataclass
class ModelProfile:
    role: str
    deployment_mode: str
    model: str
    base_url: str
    api_path: str | None = None
    temperature: float = 0.2
    kwargs: dict[str, Any] | None = None


class ModelProfileStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        # Align DSN resolution with other stores: prefer POSTGRES_DSN env override
        # (set by docker-compose) over any baked settings. Fall back to provided
        # dsn or a localhost dev default.
        from services.common import runtime_config as cfg
        raw_dsn = cfg.env(
            "POSTGRES_DSN",
            dsn or "postgresql://soma:soma@localhost:5432/somaagent01",
        )
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    @classmethod
    def from_settings(cls, settings: BaseServiceSettings) -> "ModelProfileStore":
        # Respect the same POSTGRES_DSN env override here too to avoid mismatches
        # when SA01_POSTGRES_DSN is set in .env but docker provides POSTGRES_DSN.
        from services.common import runtime_config as cfg
        return cls(dsn=cfg.env("POSTGRES_DSN", settings.postgres_dsn))

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            from services.common import runtime_config as cfg
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", "1"))
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", "2"))
            self._pool = await asyncpg.create_pool(
                self.dsn, min_size=max(0, min_size), max_size=max(1, max_size)
            )
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS model_profiles (
                    id SERIAL PRIMARY KEY,
                    role TEXT NOT NULL,
                    deployment_mode TEXT NOT NULL,
                    model TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    api_path TEXT,
                    temperature DOUBLE PRECISION NOT NULL DEFAULT 0.2,
                    extra JSONB NOT NULL DEFAULT '{}'::jsonb,
                    UNIQUE(role, deployment_mode)
                );
                """
            )

    async def upsert(self, profile: ModelProfile) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO model_profiles (role, deployment_mode, model, base_url, api_path, temperature, extra)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (role, deployment_mode)
                DO UPDATE SET model = EXCLUDED.model,
                              base_url = EXCLUDED.base_url,
                              api_path = EXCLUDED.api_path,
                              temperature = EXCLUDED.temperature,
                              extra = EXCLUDED.extra;
                """,
                profile.role,
                profile.deployment_mode,
                profile.model,
                profile.base_url,
                profile.api_path,
                profile.temperature,
                json.dumps(profile.kwargs or {}, ensure_ascii=False),
            )

    # Backward-compat helpers to match Gateway endpoint names
    async def create_profile(self, profile: ModelProfile) -> None:
        """Create or replace a model profile.

        Gateway's /v1/model-profiles (POST) calls this method. We simply ensure the
        schema exists and delegate to upsert() so the operation is idempotent in dev.
        """
        await self.ensure_schema()
        await self.upsert(profile)

    async def update_profile(self, role: str, deployment_mode: str, profile: ModelProfile) -> None:
        """Update an existing model profile identified by (role, deployment_mode).

        The payload may include role/deployment_mode, but we trust the path
        parameters to avoid accidental mismatches.
        """
        await self.ensure_schema()
        effective = ModelProfile(
            role=role,
            deployment_mode=deployment_mode,
            model=profile.model,
            base_url=profile.base_url,
            temperature=profile.temperature,
            kwargs=profile.kwargs,
        )
        await self.upsert(effective)

    async def delete_profile(self, role: str, deployment_mode: str) -> None:
        await self.delete(role, deployment_mode)

    async def delete(self, role: str, deployment_mode: str) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM model_profiles WHERE role = $1 AND deployment_mode = $2",
                role,
                deployment_mode,
            )

    async def get(self, role: str, deployment_mode: str) -> Optional[ModelProfile]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT role, deployment_mode, model, base_url, api_path, temperature, extra
                FROM model_profiles
                WHERE role = $1 AND deployment_mode = $2
                """,
                role,
                deployment_mode,
            )
        if row is None:
            return None
        return ModelProfile(
            role=row["role"],
            deployment_mode=row["deployment_mode"],
            model=row["model"],
            base_url=row["base_url"],
            api_path=row["api_path"],
            temperature=row["temperature"],
            kwargs=row["extra"],
        )

    async def list(self, deployment_mode: Optional[str] = None) -> list[ModelProfile]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            if deployment_mode:
                rows = await conn.fetch(
                    "SELECT role, deployment_mode, model, base_url, api_path, temperature, extra FROM model_profiles WHERE deployment_mode = $1",
                    deployment_mode,
                )
            else:
                rows = await conn.fetch(
                    "SELECT role, deployment_mode, model, base_url, api_path, temperature, extra FROM model_profiles",
                )
        return [
            ModelProfile(
                role=row["role"],
                deployment_mode=row["deployment_mode"],
                model=row["model"],
                base_url=row["base_url"],
                api_path=row["api_path"],
                temperature=row["temperature"],
                kwargs=row["extra"],
            )
            for row in rows
        ]

    # Backward-compatible alias used by gateway endpoints
    async def list_profiles(self, deployment_mode: Optional[str] = None) -> list[ModelProfile]:
        """Alias for list(); maintained for gateway handler compatibility."""
        return await self.list(deployment_mode)

    async def sync_from_settings(self, settings: BaseServiceSettings) -> None:
        """Upsert profiles defined in the shared ``model_profiles.yaml`` file."""
        # Seed-only behavior: insert defaults for missing roles, but never overwrite
        # profiles already created/updated via the Web UI. This ensures the UI remains
        # the single source of truth in production while still allowing initial defaults.
        payload = settings.environment_profile()
        records = payload.get("profiles", []) if isinstance(payload, dict) else []
        for record in records:
            if not isinstance(record, dict):
                continue
            role = str(record.get("role", "default"))
            # Skip when an existing profile is present for this role+deployment
            existing = await self.get(role, settings.deployment_mode)
            if existing is not None:
                continue
            profile = ModelProfile(
                role=role,
                deployment_mode=settings.deployment_mode,
                model=str(record.get("model", "")),
                base_url=str(record.get("base_url", "")),
                temperature=float(record.get("temperature", 0.2)),
                kwargs=record.get("extra") if isinstance(record.get("extra"), dict) else None,
            )
            await self.upsert(profile)
