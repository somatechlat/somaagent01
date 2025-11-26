"""Profile repository for SomaAgent01."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Any, Optional, List
from uuid import UUID

import asyncpg
from prometheus_client import Counter, Histogram

from src.core.config import cfg

LOGGER = logging.getLogger(__name__)

PROFILE_WRITE_TOTAL = Counter(
    "profile_write_total",
    "Count of profile write operations",
    labelnames=("operation", "status"),
)

PROFILE_WRITE_SECONDS = Histogram(
    "profile_write_seconds",
    "Duration of profile write operations",
    labelnames=("operation",),
)

PROFILE_READ_TOTAL = Counter(
    "profile_read_total",
    "Count of profile read operations",
    labelnames=("result",),
)

PROFILE_READ_SECONDS = Histogram(
    "profile_read_seconds",
    "Duration of profile read operations",
    labelnames=("result",),
)

@dataclass(slots=True)
class PersonaProfile:
    id: UUID
    name: str
    description: Optional[str]
    activation_triggers: dict[str, Any]
    cognitive_params: dict[str, Any]
    tool_weights: dict[str, Any]
    system_prompt_modifier: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS persona_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    activation_triggers JSONB NOT NULL DEFAULT '{}'::jsonb,
    cognitive_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    tool_weights JSONB NOT NULL DEFAULT '{}'::jsonb,
    system_prompt_modifier TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION persona_profiles_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS persona_profiles_set_updated_at ON persona_profiles;
CREATE TRIGGER persona_profiles_set_updated_at
BEFORE UPDATE ON persona_profiles
FOR EACH ROW
EXECUTE FUNCTION persona_profiles_touch_updated_at();
"""

class ProfileStore:
    def __init__(self, dsn: Optional[str] = None) -> None:
        raw_dsn = dsn or cfg.settings().database.dsn
        self.dsn = raw_dsn
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(cfg.env("PG_POOL_MIN_SIZE", 1))
            max_size = int(cfg.env("PG_POOL_MAX_SIZE", 10))
            self._pool = await asyncpg.create_pool(self.dsn, min_size=max(0, min_size), max_size=max(1, max_size))
        return self._pool

    async def ensure_schema(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute(MIGRATION_SQL)
            LOGGER.info("Ensured persona_profiles table exists")
            
            # Seed default profiles if empty
            count = await conn.fetchval("SELECT COUNT(*) FROM persona_profiles")
            if count == 0:
                LOGGER.info("Seeding default profiles")
                await self._seed_defaults(conn)

    async def _seed_defaults(self, conn: asyncpg.Connection) -> None:
        defaults = [
            {
                "name": "work_mode",
                "description": "Focused, professional mode for high-productivity tasks.",
                "activation_triggers": {"keywords": ["work", "code", "deploy", "fix"]},
                "cognitive_params": {"urgency": 0.8, "creativity": 0.3},
                "tool_weights": {"code_execute": 1.5, "browser": 1.2},
                "system_prompt_modifier": "You are in WORK MODE. Be concise, professional, and focused on execution.",
            },
            {
                "name": "teaching_mode",
                "description": "Patient, explanatory mode for learning and exploration.",
                "activation_triggers": {"keywords": ["explain", "teach", "how to", "learn"]},
                "cognitive_params": {"urgency": 0.2, "creativity": 0.7},
                "tool_weights": {"knowledge_search": 1.5},
                "system_prompt_modifier": "You are in TEACHING MODE. Be patient, explain concepts clearly, and encourage questions.",
            },
            {
                "name": "emergency_mode",
                "description": "High-urgency mode for critical issues.",
                "activation_triggers": {"keywords": ["critical", "emergency", "down", "crash"]},
                "cognitive_params": {"urgency": 1.0, "creativity": 0.1},
                "tool_weights": {"pagerduty": 2.0, "logs": 1.5},
                "system_prompt_modifier": "You are in EMERGENCY MODE. Act immediately. Prioritize stability and recovery.",
            }
        ]
        
        for p in defaults:
            await conn.execute(
                """
                INSERT INTO persona_profiles (name, description, activation_triggers, cognitive_params, tool_weights, system_prompt_modifier)
                VALUES ($1, $2, $3::jsonb, $4::jsonb, $5::jsonb, $6)
                """,
                p["name"], p["description"], json.dumps(p["activation_triggers"]), 
                json.dumps(p["cognitive_params"]), json.dumps(p["tool_weights"]), 
                p["system_prompt_modifier"]
            )

    async def get_profile_by_name(self, name: str) -> Optional[PersonaProfile]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            start = perf_counter()
            try:
                row = await conn.fetchrow(
                    """
                    SELECT id, name, description, activation_triggers, cognitive_params, 
                           tool_weights, system_prompt_modifier, is_active, created_at, updated_at
                    FROM persona_profiles
                    WHERE name = $1
                    """,
                    name,
                )
            except Exception:
                PROFILE_READ_TOTAL.labels("error").inc()
                PROFILE_READ_SECONDS.labels("error").observe(perf_counter() - start)
                raise
            duration = perf_counter() - start
            
        if not row:
            PROFILE_READ_TOTAL.labels("missing").inc()
            PROFILE_READ_SECONDS.labels("missing").observe(duration)
            return None

        PROFILE_READ_TOTAL.labels("found").inc()
        PROFILE_READ_SECONDS.labels("found").observe(duration)
        return self._row_to_profile(row)

    async def list_active_profiles(self) -> List[PersonaProfile]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, description, activation_triggers, cognitive_params, 
                       tool_weights, system_prompt_modifier, is_active, created_at, updated_at
                FROM persona_profiles
                WHERE is_active = TRUE
                ORDER BY name ASC
                """
            )
        return [self._row_to_profile(row) for row in rows]

    def _row_to_profile(self, row: Any) -> PersonaProfile:
        return PersonaProfile(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            activation_triggers=json.loads(row["activation_triggers"]) if isinstance(row["activation_triggers"], str) else row["activation_triggers"],
            cognitive_params=json.loads(row["cognitive_params"]) if isinstance(row["cognitive_params"], str) else row["cognitive_params"],
            tool_weights=json.loads(row["tool_weights"]) if isinstance(row["tool_weights"], str) else row["tool_weights"],
            system_prompt_modifier=row["system_prompt_modifier"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
