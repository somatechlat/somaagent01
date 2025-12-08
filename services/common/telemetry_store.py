"""Postgres-backed telemetry store."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import asyncpg

from src.core.config import cfg


def _int_from_env(name: str, default: int) -> int:
    raw = cfg.env(name, str(default))
    try:
        return int(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default


class TelemetryStore:
    def __init__(self, dsn: Optional[str] = None) -> None:

        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    @classmethod
    def from_settings(cls, settings: object | None = None) -> "TelemetryStore":
        database = getattr(settings, "database", None) if settings is not None else None
        dsn = getattr(database, "dsn", None) or getattr(settings, "postgres_dsn", None)
        return cls(dsn=dsn)

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = _int_from_env("PG_POOL_MIN_SIZE", 1)
            max_size = _int_from_env("PG_POOL_MAX_SIZE", 2)
            self._pool = await asyncpg.create_pool(
                self.dsn, min_size=max(0, min_size), max_size=max(1, max_size)
            )
            await self._ensure_schema()
        return self._pool

    async def _ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS slm_metrics (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    persona_id TEXT,
                    tenant TEXT,
                    model TEXT,
                    latency_seconds DOUBLE PRECISION,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    metadata JSONB,
                    occurred_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS tool_metrics (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    persona_id TEXT,
                    tenant TEXT,
                    tool_name TEXT,
                    status TEXT,
                    latency_seconds DOUBLE PRECISION,
                    metadata JSONB,
                    occurred_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS budget_events (
                    id SERIAL PRIMARY KEY,
                    tenant TEXT,
                    persona_id TEXT,
                    delta_tokens INTEGER,
                    total_tokens INTEGER,
                    limit_tokens INTEGER,
                    status TEXT,
                    metadata JSONB,
                    occurred_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS escalation_metrics (
                    id SERIAL PRIMARY KEY,
                    session_id TEXT,
                    persona_id TEXT,
                    tenant TEXT,
                    model TEXT,
                    latency_seconds DOUBLE PRECISION,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    decision_reason TEXT,
                    status TEXT,
                    metadata JSONB,
                    occurred_at TIMESTAMPTZ DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS model_scores (
                    id SERIAL PRIMARY KEY,
                    model TEXT NOT NULL,
                    deployment_mode TEXT NOT NULL,
                    window_start TIMESTAMPTZ NOT NULL,
                    window_end TIMESTAMPTZ NOT NULL,
                    avg_latency DOUBLE PRECISION,
                    avg_tokens DOUBLE PRECISION,
                    score DOUBLE PRECISION,
                    extra JSONB,
                    UNIQUE(model, deployment_mode, window_start, window_end)
                );
                """
            )

    async def insert_slm(self, event: dict[str, Any]) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO slm_metrics
                    (session_id, persona_id, tenant, model, latency_seconds, input_tokens, output_tokens, metadata)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                """,
                event.get("session_id"),
                event.get("persona_id"),
                event.get("tenant"),
                event.get("model"),
                event.get("latency_seconds"),
                event.get("input_tokens"),
                event.get("output_tokens"),
                json.dumps(event.get("metadata", {}), ensure_ascii=False),
            )

    async def insert_tool(self, event: dict[str, Any]) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tool_metrics
                    (session_id, persona_id, tenant, tool_name, status, latency_seconds, metadata)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                event.get("session_id"),
                event.get("persona_id"),
                event.get("tenant"),
                event.get("tool_name"),
                event.get("status"),
                event.get("latency_seconds"),
                json.dumps(event.get("metadata", {}), ensure_ascii=False),
            )

    async def insert_budget(self, event: dict[str, Any]) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO budget_events
                    (tenant, persona_id, delta_tokens, total_tokens, limit_tokens, status, metadata)
                VALUES ($1,$2,$3,$4,$5,$6,$7)
                """,
                event.get("tenant"),
                event.get("persona_id"),
                event.get("delta_tokens"),
                event.get("total_tokens"),
                event.get("limit_tokens"),
                event.get("status"),
                json.dumps(event.get("metadata", {}), ensure_ascii=False),
            )

    async def insert_escalation(self, event: dict[str, Any]) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO escalation_metrics
                    (session_id, persona_id, tenant, model, latency_seconds, input_tokens, output_tokens, decision_reason, status, metadata)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                """,
                event.get("session_id"),
                event.get("persona_id"),
                event.get("tenant"),
                event.get("model"),
                event.get("latency_seconds"),
                event.get("input_tokens"),
                event.get("output_tokens"),
                event.get("decision_reason"),
                event.get("status"),
                json.dumps(event.get("metadata", {}), ensure_ascii=False),
            )

    async def save_model_score(
        self,
        *,
        model: str,
        deployment_mode: str,
        window_start,
        window_end,
        avg_latency: float,
        avg_tokens: float,
        score: float,
        extra: dict[str, Any],
    ) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO model_scores
                    (model, deployment_mode, window_start, window_end, avg_latency, avg_tokens, score, extra)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                ON CONFLICT (model, deployment_mode, window_start, window_end)
                DO UPDATE SET avg_latency=EXCLUDED.avg_latency,
                              avg_tokens=EXCLUDED.avg_tokens,
                              score=EXCLUDED.score,
                              extra=EXCLUDED.extra
                """,
                model,
                deployment_mode,
                window_start,
                window_end,
                avg_latency,
                avg_tokens,
                score,
                json.dumps(extra, ensure_ascii=False),
            )
