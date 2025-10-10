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
    temperature: float = 0.2
    kwargs: dict[str, Any] | None = None


class ModelProfileStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self._pool: Optional[asyncpg.Pool] = None

    @classmethod
    def from_settings(cls, settings: BaseServiceSettings) -> "ModelProfileStore":
        return cls(dsn=settings.postgres_dsn)

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
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
                INSERT INTO model_profiles (role, deployment_mode, model, base_url, temperature, extra)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (role, deployment_mode)
                DO UPDATE SET model = EXCLUDED.model,
                              base_url = EXCLUDED.base_url,
                              temperature = EXCLUDED.temperature,
                              extra = EXCLUDED.extra;
                """,
                profile.role,
                profile.deployment_mode,
                profile.model,
                profile.base_url,
                profile.temperature,
                json.dumps(profile.kwargs or {}, ensure_ascii=False),
            )

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
                SELECT role, deployment_mode, model, base_url, temperature, extra
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
            temperature=row["temperature"],
            kwargs=row["extra"],
        )

    async def list(self, deployment_mode: Optional[str] = None) -> list[ModelProfile]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            if deployment_mode:
                rows = await conn.fetch(
                    "SELECT role, deployment_mode, model, base_url, temperature, extra FROM model_profiles WHERE deployment_mode = $1",
                    deployment_mode,
                )
            else:
                rows = await conn.fetch(
                    "SELECT role, deployment_mode, model, base_url, temperature, extra FROM model_profiles",
                )
        return [
            ModelProfile(
                role=row["role"],
                deployment_mode=row["deployment_mode"],
                model=row["model"],
                base_url=row["base_url"],
                temperature=row["temperature"],
                kwargs=row["extra"],
            )
            for row in rows
        ]

    async def sync_from_settings(self, settings: BaseServiceSettings) -> None:
        """Upsert profiles defined in the shared ``model_profiles.yaml`` file."""

        payload = settings.environment_profile()
        records = payload.get("profiles", []) if isinstance(payload, dict) else []
        for record in records:
            if not isinstance(record, dict):
                continue
            profile = ModelProfile(
                role=str(record.get("role", "default")),
                deployment_mode=settings.deployment_mode,
                model=str(record.get("model", "")),
                base_url=str(record.get("base_url", "")),
                temperature=float(record.get("temperature", 0.2)),
                kwargs=record.get("extra") if isinstance(record.get("extra"), dict) else None,
            )
            await self.upsert(profile)
