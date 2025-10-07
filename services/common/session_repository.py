"""Session repository abstractions for SomaAgent01."""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import asyncpg
import redis.asyncio as redis

LOGGER = logging.getLogger(__name__)


class SessionCache(ABC):
    @abstractmethod
    async def get(self, key: str) -> Optional[dict[str, Any]]: ...

    @abstractmethod
    async def set(self, key: str, value: dict[str, Any], ttl: int = 0) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    async def ping(self) -> None:
        """Optional health check hook."""
        return None


class RedisSessionCache(SessionCache):
    def __init__(self, url: Optional[str] = None) -> None:
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client: redis.Redis = redis.from_url(self.url, decode_responses=True)

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        raw = await self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set(self, key: str, value: dict[str, Any], ttl: int = 0) -> None:
        data = json.dumps(value, ensure_ascii=False)
        if ttl > 0:
            await self._client.setex(key, ttl, data)
        else:
            await self._client.set(key, data)

    async def delete(self, key: str) -> None:
        await self._client.delete(key)

    async def ping(self) -> None:
        await self._client.ping()


class SessionStore(ABC):
    @abstractmethod
    async def append_event(self, session_id: str, event: dict[str, Any]) -> None: ...

    @abstractmethod
    async def list_events(
        self, session_id: str, limit: int = 100
    ) -> list[dict[str, Any]]: ...

    @abstractmethod
    async def get_envelope(self, session_id: str) -> Optional["SessionEnvelope"]: ...


@dataclass(slots=True)
class SessionEnvelope:
    session_id: UUID
    persona_id: Optional[str]
    tenant: Optional[str]
    subject: Optional[str]
    issuer: Optional[str]
    scope: Optional[str]
    metadata: dict[str, Any]
    analysis: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class PostgresSessionStore(SessionStore):
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.dsn, min_size=1, max_size=5)
        return self._pool

    @staticmethod
    def _parse_session_id(session_id: str) -> UUID:
        try:
            return UUID(session_id)
        except ValueError as exc:  # pragma: no cover - defensive guard
            LOGGER.warning("Invalid session_id for envelope", extra={"session_id": session_id})
            raise exc

    @staticmethod
    def _split_metadata(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        raw_metadata = event.get("metadata") or {}
        if isinstance(raw_metadata, dict):
            metadata = dict(raw_metadata)
        else:  # pragma: no cover - defensive guard
            LOGGER.warning(
                "Unexpected metadata payload when composing envelope",
                extra={"metadata": raw_metadata},
            )
            metadata = {}

        analysis = metadata.pop("analysis", None)
        if isinstance(analysis, dict):
            analysis_payload = analysis
        else:
            analysis_payload = {}
        return metadata, analysis_payload

    def _compose_envelope_payload(
        self, event: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        session_id = event.get("session_id")
        if not session_id:
            return None
        persona_id = event.get("persona_id")
        metadata, analysis = self._split_metadata(event)

        payload = {
            "session_id": self._parse_session_id(session_id),
            "persona_id": persona_id,
            "tenant": metadata.get("tenant"),
            "subject": metadata.get("subject"),
            "issuer": metadata.get("issuer"),
            "scope": metadata.get("scope"),
            "metadata": metadata,
            "analysis": analysis,
        }

        return payload

    async def ping(self) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")

    async def append_event(self, session_id: str, event: dict[str, Any]) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            envelope_payload = self._compose_envelope_payload(event)
            async with conn.transaction():
                await conn.execute(
                    """
                    INSERT INTO session_events (session_id, payload)
                    VALUES ($1, $2)
                    """,
                    session_id,
                    json.dumps(event, ensure_ascii=False),
                )
                if envelope_payload:
                    await self._upsert_envelope(conn, envelope_payload)

    async def list_events(
        self, session_id: str, limit: int = 100
    ) -> list[dict[str, Any]]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT payload
                FROM session_events
                WHERE session_id = $1
                ORDER BY id DESC
                LIMIT $2
                """,
                session_id,
                limit,
            )
        return [json.loads(r["payload"]) for r in rows]

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _upsert_envelope(
        self,
        conn: asyncpg.Connection,
        payload: dict[str, Any],
        *,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        metadata_json = json.dumps(payload.get("metadata", {}), ensure_ascii=False)
        analysis_json = json.dumps(payload.get("analysis", {}), ensure_ascii=False)
        await conn.execute(
            """
            INSERT INTO session_envelopes (
                session_id,
                persona_id,
                tenant,
                subject,
                issuer,
                scope,
                metadata,
                analysis,
                created_at,
                updated_at
            )
            VALUES (
                $1,
                $2,
                $3,
                $4,
                $5,
                $6,
                $7::jsonb,
                $8::jsonb,
                COALESCE($9, NOW()),
                COALESCE($10, NOW())
            )
            ON CONFLICT (session_id) DO UPDATE SET
                persona_id = COALESCE(EXCLUDED.persona_id, session_envelopes.persona_id),
                tenant = COALESCE(EXCLUDED.tenant, session_envelopes.tenant),
                subject = COALESCE(EXCLUDED.subject, session_envelopes.subject),
                issuer = COALESCE(EXCLUDED.issuer, session_envelopes.issuer),
                scope = COALESCE(EXCLUDED.scope, session_envelopes.scope),
                metadata = session_envelopes.metadata || EXCLUDED.metadata,
                analysis = CASE
                    WHEN EXCLUDED.analysis = '{}'::jsonb THEN session_envelopes.analysis
                    ELSE EXCLUDED.analysis
                END,
                updated_at = NOW()
            """,
            payload["session_id"],
            payload.get("persona_id"),
            payload.get("tenant"),
            payload.get("subject"),
            payload.get("issuer"),
            payload.get("scope"),
            metadata_json,
            analysis_json,
            created_at,
            updated_at,
        )

    async def get_envelope(self, session_id: str) -> Optional[SessionEnvelope]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT session_id,
                       persona_id,
                       tenant,
                       subject,
                       issuer,
                       scope,
                       metadata,
                       analysis,
                       created_at,
                       updated_at
                FROM session_envelopes
                WHERE session_id = $1::uuid
                """,
                session_id,
            )
        if not row:
            return None

        return SessionEnvelope(
            session_id=row["session_id"],
            persona_id=row["persona_id"],
            tenant=row["tenant"],
            subject=row["subject"],
            issuer=row["issuer"],
            scope=row["scope"],
            metadata=row["metadata"],
            analysis=row["analysis"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def backfill_envelope(
        self,
        session_id: str,
        *,
        persona_id: Optional[str],
        tenant: Optional[str],
        subject: Optional[str],
        issuer: Optional[str],
        scope: Optional[str],
        metadata: dict[str, Any],
        analysis: dict[str, Any],
        created_at: Optional[datetime],
        updated_at: Optional[datetime],
    ) -> None:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            await self._upsert_envelope(
                conn,
                {
                    "session_id": self._parse_session_id(session_id),
                    "persona_id": persona_id,
                    "tenant": tenant,
                    "subject": subject,
                    "issuer": issuer,
                    "scope": scope,
                    "metadata": metadata,
                    "analysis": analysis,
                },
                created_at=created_at,
                updated_at=updated_at,
            )


MIGRATION_SQL = """
CREATE TABLE IF NOT EXISTS session_events (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS session_envelopes (
    session_id UUID PRIMARY KEY,
    persona_id TEXT,
    tenant TEXT,
    subject TEXT,
    issuer TEXT,
    scope TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    analysis JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION session_envelopes_touch_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS session_envelopes_set_updated_at ON session_envelopes;
CREATE TRIGGER session_envelopes_set_updated_at
BEFORE UPDATE ON session_envelopes
FOR EACH ROW
EXECUTE FUNCTION session_envelopes_touch_updated_at();
"""


async def ensure_schema(store: PostgresSessionStore) -> None:
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        await conn.execute(MIGRATION_SQL)
        LOGGER.info("Ensured session_events and session_envelopes tables exist")
