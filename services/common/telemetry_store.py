"""Postgres-backed telemetry store."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import asyncpg

from services.common.settings_base import BaseServiceSettings


class TelemetryStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    @classmethod
    def from_settings(cls, settings: BaseServiceSettings) -> "TelemetryStore":
        return cls(dsn=settings.postgres_dsn)

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(os.getenv("PG_POOL_MIN_SIZE", "1"))
            max_size = int(os.getenv("PG_POOL_MAX_SIZE", "2"))
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

                CREATE TABLE IF NOT EXISTS generic_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_name TEXT NOT NULL,
                    labels JSONB,
                    value DOUBLE PRECISION,
                    metadata JSONB,
                    occurred_at TIMESTAMPTZ DEFAULT NOW()
                );
                -- Helpful indexes for common queries and recent lookups
                DO $$
                BEGIN
                    -- Composite index for metric_name and recency
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relkind = 'i' AND c.relname = 'idx_generic_metrics_name_time'
                    ) THEN
                        CREATE INDEX idx_generic_metrics_name_time
                        ON generic_metrics (metric_name, occurred_at DESC);
                    END IF;

                    -- Standalone occurred_at index for time-based scans
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relkind = 'i' AND c.relname = 'idx_generic_metrics_occurred_at'
                    ) THEN
                        CREATE INDEX idx_generic_metrics_occurred_at
                        ON generic_metrics (occurred_at DESC);
                    END IF;

                    -- GIN index on labels JSONB for generic key/value filters
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_class c
                        JOIN pg_namespace n ON n.oid = c.relnamespace
                        WHERE c.relkind = 'i' AND c.relname = 'idx_generic_metrics_labels'
                    ) THEN
                        CREATE INDEX idx_generic_metrics_labels
                        ON generic_metrics USING GIN (labels jsonb_ops);
                    END IF;
                END$$;
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

    async def insert_generic_metric(
        self,
        *,
        metric_name: str,
        labels: dict[str, Any] | None,
        value: float | int | None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO generic_metrics (metric_name, labels, value, metadata)
                VALUES ($1,$2,$3,$4)
                """,
                metric_name,
                json.dumps(labels or {}, ensure_ascii=False),
                float(value) if value is not None else None,
                json.dumps(metadata or {}, ensure_ascii=False),
            )

    async def fetch_recent_generic(self, metric_name: str, limit: int = 25) -> list[dict[str, Any]]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT metric_name, labels, value, metadata, occurred_at
                FROM generic_metrics
                WHERE metric_name = $1
                ORDER BY occurred_at DESC
                LIMIT $2
                """,
                metric_name,
                limit,
            )
        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "metric_name": r["metric_name"],
                    "labels": r["labels"],
                    "value": r["value"],
                    "metadata": r["metadata"],
                    "occurred_at": r["occurred_at"].isoformat() if r["occurred_at"] else None,
                }
            )
        return out
