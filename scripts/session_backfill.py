"""Backfill the session_envelopes table and warm Redis cache.

Usage examples:
    python scripts/session_backfill.py --limit 100
    python scripts/session_backfill.py --skip-redis --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Optional

import asyncpg

from services.common.session_repository import (
    ensure_schema,
    PostgresSessionStore,
    RedisSessionCache,
)

LOGGER = logging.getLogger("session_backfill")


@dataclass(slots=True)
class BackfillStats:
    processed: int = 0
    skipped: int = 0
    cached: int = 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate session_envelopes from session_events and warm Redis cache.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of sessions to backfill (default: all).",
    )
    parser.add_argument(
        "--event-limit",
        type=int,
        default=500,
        help="Maximum number of events to inspect per session (default: 500).",
    )
    parser.add_argument(
        "--skip-redis",
        action="store_true",
        help="Skip warming Redis cache entries after writing envelopes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not write to Postgres or Redis; only log what would change.",
    )
    parser.add_argument(
        "--redis-ttl",
        type=int,
        default=900,
        help="TTL (seconds) for warmed Redis cache entries (default: 900).",
    )
    parser.add_argument(
        "--log-level",
        choices=["INFO", "DEBUG", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO).",
    )
    return parser.parse_args()


async def _fetch_session_catalog(
    pool: asyncpg.Pool, limit: Optional[int]
) -> Iterable[asyncpg.Record]:
    query = """
        SELECT session_id,
               MIN(occurred_at) AS created_at,
               MAX(occurred_at) AS updated_at
        FROM session_events
        GROUP BY session_id
        ORDER BY MAX(occurred_at) DESC
    """
    if limit is not None:
        query += " LIMIT $1"
        return await pool.fetch(query, limit)
    return await pool.fetch(query)


def _load_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        return json.loads(payload)
    raise TypeError(f"Unsupported payload type: {type(payload)!r}")


def _merge_metadata(target: dict[str, Any], incoming: dict[str, Any]) -> None:
    for key, value in incoming.items():
        if key == "analysis":
            continue
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _merge_metadata(target[key], value)
        else:
            target[key] = value


def _compose_envelope_from_events(events: Iterable[tuple[dict[str, Any], datetime]]) -> tuple[
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    dict[str, Any],
    dict[str, Any],
]:
    metadata: dict[str, Any] = {}
    analysis: dict[str, Any] = {}
    persona_id: Optional[str] = None
    tenant: Optional[str] = None
    subject: Optional[str] = None
    issuer: Optional[str] = None
    scope: Optional[str] = None

    for payload, _ in events:
        event_metadata = payload.get("metadata")
        if isinstance(event_metadata, dict):
            if not tenant and event_metadata.get("tenant"):
                tenant = str(event_metadata["tenant"])
            if not subject and event_metadata.get("subject"):
                subject = str(event_metadata["subject"])
            if not issuer and event_metadata.get("issuer"):
                issuer = str(event_metadata["issuer"])
            if not scope and event_metadata.get("scope"):
                scope = str(event_metadata["scope"])

            incoming_metadata = {
                key: value for key, value in event_metadata.items() if key != "analysis"
            }
            _merge_metadata(metadata, incoming_metadata)

            candidate_analysis = event_metadata.get("analysis")
            if isinstance(candidate_analysis, dict) and candidate_analysis:
                analysis = candidate_analysis

        candidate_persona = payload.get("persona_id")
        if candidate_persona:
            persona_id = candidate_persona

    return persona_id, tenant, subject, issuer, scope, metadata, analysis


async def _process_session(
    pool: asyncpg.Pool,
    store: PostgresSessionStore,
    cache: Optional[RedisSessionCache],
    record: asyncpg.Record,
    *,
    event_limit: int,
    dry_run: bool,
    redis_ttl: int,
) -> bool:
    session_id = record["session_id"]
    events_rows = await pool.fetch(
        """
        SELECT payload, occurred_at
        FROM session_events
        WHERE session_id = $1
        ORDER BY occurred_at ASC
        LIMIT $2
        """,
        session_id,
        event_limit,
    )
    if not events_rows:
        LOGGER.debug("Skipping session with no events", extra={"session_id": session_id})
        return False

    events: list[tuple[dict[str, Any], datetime]] = []
    for row in events_rows:
        payload = _load_payload(row["payload"])
        events.append((payload, row["occurred_at"]))

    (
        persona_id,
        tenant,
        subject,
        issuer,
        scope,
        metadata,
        analysis,
    ) = _compose_envelope_from_events(events)

    created_at: datetime = record["created_at"]
    updated_at: datetime = record["updated_at"]

    if dry_run:
        LOGGER.info(
            "[dry-run] Would backfill session",
            extra={
                "session_id": session_id,
                "persona_id": persona_id,
                "tenant": tenant,
                "metadata_keys": sorted(metadata.keys()),
            },
        )
        return True

    try:
        await store.backfill_envelope(
            session_id=session_id,
            persona_id=persona_id,
            tenant=tenant,
            subject=subject,
            issuer=issuer,
            scope=scope,
            metadata=metadata,
            analysis=analysis,
            created_at=created_at,
            updated_at=updated_at,
        )
    except ValueError as exc:
        LOGGER.warning(
            "Skipping session due to invalid UUID",
            extra={"session_id": session_id, "error": str(exc)},
        )
        return False

    if cache is not None:
        await cache.set(
            f"session:{session_id}:meta",
            {
                "persona_id": persona_id or "",
                "metadata": metadata,
            },
            ttl=redis_ttl,
        )

    LOGGER.debug(
        "Backfilled session envelope",
        extra={
            "session_id": session_id,
            "persona_id": persona_id,
            "tenant": tenant,
            "metadata_keys": sorted(metadata.keys()),
        },
    )
    return True


async def _run(args: argparse.Namespace) -> BackfillStats:
    store = PostgresSessionStore()
    await ensure_schema(store)
    cache = None if args.skip_redis else RedisSessionCache()
    pool = await store._ensure_pool()

    stats = BackfillStats()
    session_catalog = await _fetch_session_catalog(pool, args.limit)

    for record in session_catalog:
        processed = await _process_session(
            pool,
            store,
            cache,
            record,
            event_limit=args.event_limit,
            dry_run=args.dry_run,
            redis_ttl=args.redis_ttl,
        )
        if processed:
            stats.processed += 1
            if cache is not None and not args.dry_run:
                stats.cached += 1
        else:
            stats.skipped += 1

    await store.close()

    return stats


def main() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    try:
        stats = asyncio.run(_run(args))
    except KeyboardInterrupt:  # pragma: no cover - manual interruption
        LOGGER.warning("Backfill interrupted by user")
        return

    LOGGER.info(
        "Backfill completed",
        extra={
            "processed": stats.processed,
            "skipped": stats.skipped,
            "cached": stats.cached,
            "dry_run": args.dry_run,
        },
    )


if __name__ == "__main__":
    main()
