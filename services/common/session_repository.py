"""Session repository abstractions for SomaAgent01."""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from time import perf_counter
from typing import Any, Optional
from uuid import UUID
import uuid
from services.common import masking as _masking
from services.common import error_classifier as _errclass

import os
import asyncpg
import redis.asyncio as redis
from prometheus_client import Counter, Histogram

LOGGER = logging.getLogger(__name__)


SESSION_ENVELOPE_VALIDATION_FAILURES = Counter(
    "session_envelope_validation_failures_total",
    "Count of validation failures when constructing session envelopes",
    labelnames=("reason",),
)

SESSION_ENVELOPE_WRITE_TOTAL = Counter(
    "session_envelope_write_total",
    "Count of session envelope write operations",
    labelnames=("operation", "status"),
)

SESSION_ENVELOPE_WRITE_SECONDS = Histogram(
    "session_envelope_write_seconds",
    "Duration of session envelope write operations",
    labelnames=("operation",),
)

SESSION_ENVELOPE_REFRESH_TOTAL = Counter(
    "session_envelope_refresh_total",
    "Count of session envelope refreshes sourced from Postgres",
    labelnames=("result",),
)

SESSION_ENVELOPE_REFRESH_SECONDS = Histogram(
    "session_envelope_refresh_seconds",
    "Duration of session envelope refresh queries",
    labelnames=("result",),
)

SESSION_CACHE_EVENTS = Counter(
    "session_envelope_cache_events_total",
    "Session envelope cache interactions against Redis",
    labelnames=("operation", "result"),
)

SESSION_CACHE_KEY_TEMPLATE = "session:{session_id}:meta"


def session_cache_key(session_id: str) -> str:
    return SESSION_CACHE_KEY_TEMPLATE.format(session_id=session_id)


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
    def __init__(self, url: Optional[str] = None, *, default_ttl: Optional[int] = None) -> None:
        raw_url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.url = os.path.expandvars(raw_url)
        self._client: redis.Redis = redis.from_url(self.url, decode_responses=True)
        ttl = default_ttl
        if ttl is None:
            try:
                ttl = int(os.getenv("SESSION_CACHE_TTL_SECONDS", "900"))
            except ValueError:
                ttl = 900
        self.default_ttl = ttl if ttl and ttl > 0 else 0

    async def get(self, key: str) -> Optional[dict[str, Any]]:
        try:
            raw = await self._client.get(key)
        except Exception:
            SESSION_CACHE_EVENTS.labels("get", "error").inc()
            raise
        if raw is None:
            SESSION_CACHE_EVENTS.labels("get", "miss").inc()
            return None
        SESSION_CACHE_EVENTS.labels("get", "hit").inc()
        return json.loads(raw)

    async def set(self, key: str, value: dict[str, Any], ttl: int = 0) -> None:
        data = json.dumps(value, ensure_ascii=False)
        effective_ttl = ttl if ttl and ttl > 0 else self.default_ttl
        try:
            if effective_ttl > 0:
                await self._client.setex(key, effective_ttl, data)
            else:
                await self._client.set(key, data)
        except Exception:
            SESSION_CACHE_EVENTS.labels("set", "error").inc()
            raise
        else:
            SESSION_CACHE_EVENTS.labels("set", "success").inc()

    async def delete(self, key: str) -> None:
        try:
            removed = await self._client.delete(key)
        except Exception:
            SESSION_CACHE_EVENTS.labels("delete", "error").inc()
            raise
        result = "deleted" if removed else "noop"
        SESSION_CACHE_EVENTS.labels("delete", result).inc()

    async def ping(self) -> None:
        await self._client.ping()

    def format_key(self, session_id: str) -> str:
        return session_cache_key(session_id)

    async def write_context(
        self,
        session_id: str,
        persona_id: Optional[str],
        metadata: dict[str, Any] | None,
        *,
        ttl: int = 0,
    ) -> None:
        payload = {
            "persona_id": persona_id or "",
            "metadata": dict(metadata or {}),
        }
        await self.set(self.format_key(session_id), payload, ttl=ttl)


class SessionStore(ABC):
    @abstractmethod
    async def append_event(self, session_id: str, event: dict[str, Any]) -> None: ...

    @abstractmethod
    async def list_events(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]: ...

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
        raw_dsn = dsn or os.getenv(
            "POSTGRES_DSN", "postgresql://soma:soma@localhost:5432/somaagent01"
        )
        self.dsn = os.path.expandvars(raw_dsn)
        self._pool: Optional[asyncpg.Pool] = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            min_size = int(os.getenv("PG_POOL_MIN_SIZE", "1"))
            max_size = int(os.getenv("PG_POOL_MAX_SIZE", "2"))
            self._pool = await asyncpg.create_pool(self.dsn, min_size=max(0, min_size), max_size=max(1, max_size))
        return self._pool

    @staticmethod
    def _parse_session_id(session_id: str) -> UUID:
        try:
            return UUID(session_id)
        except ValueError as exc:
            SESSION_ENVELOPE_VALIDATION_FAILURES.labels("invalid_session_id").inc()
            LOGGER.warning("Invalid session_id for envelope", extra={"session_id": session_id})
            raise exc

    @staticmethod
    def _split_metadata(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        raw_metadata = event.get("metadata") or {}
        if isinstance(raw_metadata, dict):
            metadata = dict(raw_metadata)
        else:
            LOGGER.warning(
                "Unexpected metadata payload when composing envelope",
                extra={"metadata": raw_metadata},
            )
            SESSION_ENVELOPE_VALIDATION_FAILURES.labels("invalid_metadata_type").inc()
            metadata = {}

        analysis = metadata.pop("analysis", None)
        if isinstance(analysis, dict):
            analysis_payload = analysis
        else:
            if analysis is not None:
                SESSION_ENVELOPE_VALIDATION_FAILURES.labels("invalid_analysis_type").inc()
            analysis_payload = {}
        return metadata, analysis_payload

    def _compose_envelope_payload(self, event: dict[str, Any]) -> Optional[dict[str, Any]]:
        session_id = event.get("session_id")
        if not session_id:
            SESSION_ENVELOPE_VALIDATION_FAILURES.labels("missing_session_id").inc()
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
            # Normalize error events before persistence
            try:
                if isinstance(event, dict) and event.get("type") == "error":
                    # Promote to assistant.error unless role provided
                    role = event.get("role") or "assistant"
                    # Move details -> metadata.error and provide user-friendly message
                    details = event.get("details") or event.get("message") or "Unexpected error"
                    event = {
                        "event_id": event.get("event_id") or str(uuid.uuid4()),
                        "session_id": session_id,
                        "persona_id": event.get("persona_id"),
                        "role": role,
                        "message": "An internal error occurred while processing your request.",
                        "metadata": {"source": event.get("metadata", {}).get("source", "system"), "error": str(details)[:400]},
                        "type": f"{role}.error" if role in {"assistant", "tool", "system"} else "assistant.error",
                        "version": event.get("version", "sa01-v1"),
                    }
                    # Error classification (flag-driven)
                    if os.getenv("SA01_ENABLE_ERROR_CLASSIFIER", "false").lower() in {"true","1","yes","on"}:
                        meta = event.get("metadata") or {}
                        em = _errclass.classify(message=str(details))
                        meta.update({
                            "error_code": em.error_code,
                            "retriable": em.retriable,
                        })
                        if em.retry_after is not None:
                            meta["retry_after"] = em.retry_after
                        event["metadata"] = meta
            except Exception:
                pass

            # Optional masking (only for assistant/tool/system roles and user-visible message)
            if os.getenv("SA01_ENABLE_CONTENT_MASKING", "false").lower() in {"true","1","yes","on"}:
                try:
                    masked_event, hits = _masking.mask_event_payload(event)
                    if hits:
                        meta = dict(masked_event.get("metadata") or {})
                        meta.setdefault("mask_rules", hits)
                        masked_event["metadata"] = meta
                        event = masked_event
                except Exception:
                    pass
            envelope_payload = self._compose_envelope_payload(event)
            # Insert the event.  Because the `uq_session_events_session_event`
            # index enforces uniqueness of `(session_id, event_id)` we may hit a
            # `UniqueViolationError` if the same event is retried (e.g. after a
            # worker restart).  In that case we simply ignore the duplicate –
            # the event is already persisted and downstream consumers have
            # processed it.
            async with conn.transaction():
                try:
                    await conn.execute(
                        """
                        INSERT INTO session_events (session_id, payload)
                        VALUES ($1, $2)
                        """,
                        session_id,
                        json.dumps(event, ensure_ascii=False),
                    )
                except Exception as exc:
                    # asyncpg raises a subclass of `UniqueViolationError` for
                    # duplicate inserts.  We deliberately catch the generic
                    # `Exception` to avoid importing asyncpg directly – the
                    # runtime will provide the concrete type.  If the error
                    # is *not* a duplicate we re‑raise so genuine issues are
                    # not silently swallowed.
                    if getattr(exc, "__class__", None).__name__ != "UniqueViolationError":
                        raise
                    # Duplicate – safe to ignore.
                    LOGGER.debug(
                        "Duplicate session event ignored",
                        extra={"session_id": session_id, "event_id": event.get("event_id")},
                    )
                if envelope_payload:
                    await self._upsert_envelope(
                        conn,
                        envelope_payload,
                        operation="append",
                    )

    async def backfill_error_events(self) -> dict[str, int]:
        """Convert legacy raw error rows to enriched '*.error' format and fill missing fields.

        Returns a dict of counts for each update applied.
        """
        pool = await self._ensure_pool()
        raw_to_enriched = 0
        fill_missing_msg = 0
        fill_missing_role = 0
        async with pool.acquire() as conn:
            async with conn.transaction():
                # 1) Transform legacy payloads where type == 'error' into canonical '<role>.error'
                res1 = await conn.execute(
                    """
                    UPDATE session_events
                    SET payload = (
                        payload
                        || jsonb_build_object(
                            'role', COALESCE(NULLIF(payload->>'role',''), 'assistant')
                        )
                        || jsonb_build_object(
                            'type', CASE
                                WHEN COALESCE(NULLIF(payload->>'role',''), 'assistant') IN ('assistant','tool','system')
                                    THEN (COALESCE(NULLIF(payload->>'role',''), 'assistant') || '.error')
                                ELSE 'assistant.error'
                            END
                        )
                        || jsonb_build_object(
                            'message', CASE
                                WHEN COALESCE(payload->>'message','') = ''
                                    THEN 'An internal error occurred while processing your request.'
                                ELSE payload->>'message'
                            END
                        )
                        || jsonb_build_object(
                            'metadata', COALESCE(payload->'metadata', '{}'::jsonb)
                                || jsonb_build_object('source', COALESCE(payload->'metadata'->>'source','system'))
                                || jsonb_build_object('error', SUBSTRING(COALESCE(payload->>'details', payload->>'message', 'Unexpected error') FROM 1 FOR 400))
                        )
                    )
                    WHERE payload->>'type' = 'error'
                    """
                )
                try:
                    raw_to_enriched = int(str(res1).split(" ")[-1])
                except Exception:
                    raw_to_enriched = 0

                # 2) Ensure any '*.error' rows have a non-empty 'message'
                res2 = await conn.execute(
                    """
                    UPDATE session_events
                    SET payload = payload || jsonb_build_object('message', 'An internal error occurred while processing your request.')
                    WHERE payload->>'type' LIKE '%.error'
                      AND (NOT (payload ? 'message') OR COALESCE(payload->>'message','') = '')
                    """
                )
                try:
                    fill_missing_msg = int(str(res2).split(" ")[-1])
                except Exception:
                    fill_missing_msg = 0

                # 3) Fill missing 'role' when type already encodes it as '<role>.error'
                res3 = await conn.execute(
                    """
                    UPDATE session_events
                    SET payload = payload || jsonb_build_object('role', split_part(payload->>'type', '.', 1))
                    WHERE payload->>'type' LIKE '%.error'
                      AND NOT (payload ? 'role')
                    """
                )
                try:
                    fill_missing_role = int(str(res3).split(" ")[-1])
                except Exception:
                    fill_missing_role = 0

        return {
            "raw_to_enriched": raw_to_enriched,
            "fill_missing_msg": fill_missing_msg,
            "fill_missing_role": fill_missing_role,
        }

    async def list_events(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
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

    async def list_events_after(
        self,
        session_id: str,
        *,
        after_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            if after_id is None:
                rows = await conn.fetch(
                    """
                    SELECT id, occurred_at, payload
                    FROM session_events
                    WHERE session_id = $1
                    ORDER BY id ASC
                    LIMIT $2
                    """,
                    session_id,
                    limit,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, occurred_at, payload
                    FROM session_events
                    WHERE session_id = $1
                      AND id > $2
                    ORDER BY id ASC
                    LIMIT $3
                    """,
                    session_id,
                    after_id,
                    limit,
                )
        events: list[dict[str, Any]] = []
        for row in rows:
            payload = row["payload"]
            if isinstance(payload, str):
                payload = json.loads(payload)
            events.append(
                {
                    "id": row["id"],
                    "occurred_at": row["occurred_at"],
                    "payload": payload,
                }
            )
        return events

    async def event_exists(self, session_id: str, event_id: Optional[str]) -> bool:
        if not event_id:
            return False
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 1 FROM session_events
                WHERE session_id = $1
                  AND payload->>'event_id' = $2
                LIMIT 1
                """,
                session_id,
                event_id,
            )
        return row is not None

    async def delete_session(self, session_id: str) -> dict[str, int]:
        """Delete all timeline events and the session envelope for a session.

        Returns a dict with counts for rows deleted.
        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                events_deleted = await conn.execute(
                    """
                    DELETE FROM session_events
                    WHERE session_id = $1
                    """,
                    session_id,
                )
                # asyncpg returns e.g. 'DELETE 5' → extract the number
                try:
                    ev_count = int(str(events_deleted).split(" ")[-1])
                except Exception:
                    ev_count = 0
                env_deleted = await conn.execute(
                    """
                    DELETE FROM session_envelopes
                    WHERE session_id = $1::uuid
                    """,
                    session_id,
                )
                try:
                    env_count = int(str(env_deleted).split(" ")[-1])
                except Exception:
                    env_count = 0
        return {"events": ev_count, "envelopes": env_count}

    async def reset_session(self, session_id: str) -> dict[str, int]:
        """Clear timeline events for a session and keep the envelope.

        The envelope's analysis is cleared; metadata is preserved.
        Returns a dict with counts for rows affected.
        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                events_deleted = await conn.execute(
                    """
                    DELETE FROM session_events
                    WHERE session_id = $1
                    """,
                    session_id,
                )
                try:
                    ev_count = int(str(events_deleted).split(" ")[-1])
                except Exception:
                    ev_count = 0
                # Clear analysis JSON and touch updated_at if envelope exists
                await conn.execute(
                    """
                    UPDATE session_envelopes
                    SET analysis = '{}'::jsonb,
                        updated_at = NOW()
                    WHERE session_id = $1::uuid
                    """,
                    session_id,
                )
        return {"events": ev_count}

    async def list_sessions(
        self,
        *,
        limit: int = 50,
        tenant: Optional[str] = None,
    ) -> list[SessionEnvelope]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            if tenant:
                rows = await conn.fetch(
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
                    WHERE tenant = $1
                    ORDER BY updated_at DESC
                    LIMIT $2
                    """,
                    tenant,
                    limit,
                )
            else:
                rows = await conn.fetch(
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
                    ORDER BY updated_at DESC
                    LIMIT $1
                    """,
                    limit,
                )

        envelopes: list[SessionEnvelope] = []
        for row in rows:
            envelopes.append(
                SessionEnvelope(
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
            )
        return envelopes

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    async def _upsert_envelope(
        self,
        conn: asyncpg.Connection,
        payload: dict[str, Any],
        *,
        operation: str,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        metadata_json = json.dumps(payload.get("metadata", {}), ensure_ascii=False)
        analysis_json = json.dumps(payload.get("analysis", {}), ensure_ascii=False)
        start = perf_counter()
        try:
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
        except Exception:
            SESSION_ENVELOPE_WRITE_TOTAL.labels(operation, "error").inc()
            raise
        else:
            duration = perf_counter() - start
            SESSION_ENVELOPE_WRITE_TOTAL.labels(operation, "success").inc()
            SESSION_ENVELOPE_WRITE_SECONDS.labels(operation).observe(duration)

    async def get_envelope(self, session_id: str) -> Optional[SessionEnvelope]:
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            start = perf_counter()
            try:
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
            except Exception:
                SESSION_ENVELOPE_REFRESH_TOTAL.labels("error").inc()
                SESSION_ENVELOPE_REFRESH_SECONDS.labels("error").observe(perf_counter() - start)
                raise
            duration = perf_counter() - start
        if not row:
            SESSION_ENVELOPE_REFRESH_TOTAL.labels("missing").inc()
            SESSION_ENVELOPE_REFRESH_SECONDS.labels("missing").observe(duration)
            return None

        SESSION_ENVELOPE_REFRESH_TOTAL.labels("found").inc()
        SESSION_ENVELOPE_REFRESH_SECONDS.labels("found").observe(duration)
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
                operation="backfill",
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

-- Uniqueness index to prevent duplicate event_ids per session (if present in payload)
CREATE INDEX IF NOT EXISTS idx_session_events_event_id ON session_events ((payload->>'event_id'));
CREATE UNIQUE INDEX IF NOT EXISTS uq_session_events_session_event ON session_events (session_id, (payload->>'event_id')) WHERE (payload ? 'event_id');

-- Prevent future raw error events (payload->>'type' = 'error') by adding a CHECK constraint.
-- Add it only if missing and mark NOT VALID initially to avoid blocking on legacy rows.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_session_events_no_raw_error'
    ) THEN
        ALTER TABLE session_events
            ADD CONSTRAINT chk_session_events_no_raw_error
            CHECK (COALESCE(payload->>'type','') <> 'error') NOT VALID;
    END IF;
END$$;
"""


async def ensure_schema(store: PostgresSessionStore) -> None:
    """Create tables / indexes if they do not exist.

    The original migration script unconditionally executes ``MIGRATION_SQL``.
    When the unique index ``uq_session_events_session_event`` already
    exists *and* there are duplicate ``event_id`` rows, PostgreSQL raises a
    ``UniqueViolationError`` which crashes the conversation‑worker during
    startup.  To make the migration idempotent we now catch any exception
    raised by ``conn.execute`` and log a warning – the schema is already in
    place, so we can safely continue.
    """
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(MIGRATION_SQL)
        except Exception as exc:
            # ``UniqueViolationError`` (or any other error) during schema
            # creation means the objects already exist or the data violates
            # the new constraint.  We log the issue and proceed because the
            # worker can still operate with the existing tables.
            LOGGER.warning(
                "Schema migration failed – assuming objects already exist",
                extra={"error": str(exc)},
            )
        else:
            LOGGER.info("Ensured session_events and session_envelopes tables exist")

async def ensure_constraints(store: PostgresSessionStore) -> None:
    """Ensure optional runtime constraints that can't be safely added pre-backfill.

    - chk_session_events_no_raw_error: Disallow raw payload type 'error' rows.
    """
    pool = await store._ensure_pool()
    async with pool.acquire() as conn:
        # Add CHECK constraint if not exists (guarded via catalog lookup)
        await conn.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'chk_session_events_no_raw_error'
                ) THEN
                    ALTER TABLE session_events
                    ADD CONSTRAINT chk_session_events_no_raw_error
                    CHECK (NOT ((payload ? 'type') AND (payload->>'type' = 'error')));
                END IF;
            END$$;
            """
        )
        LOGGER.info("Ensured runtime constraints for session_events")
