import os

os.getenv(os.getenv(""))
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

LOGGER = logging.getLogger(os.getenv(os.getenv("")))


@dataclass(slots=int(os.getenv(os.getenv(""))))
class BackfillStats:
    processed: int = int(os.getenv(os.getenv("")))
    skipped: int = int(os.getenv(os.getenv("")))
    cached: int = int(os.getenv(os.getenv("")))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv("")))
    parser.add_argument(
        os.getenv(os.getenv("")), type=int, default=None, help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")),
        type=int,
        default=int(os.getenv(os.getenv(""))),
        help=os.getenv(os.getenv("")),
    )
    parser.add_argument(
        os.getenv(os.getenv("")), action=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")), action=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")),
        type=int,
        default=int(os.getenv(os.getenv(""))),
        help=os.getenv(os.getenv("")),
    )
    parser.add_argument(
        os.getenv(os.getenv("")),
        choices=[
            os.getenv(os.getenv("")),
            os.getenv(os.getenv("")),
            os.getenv(os.getenv("")),
            os.getenv(os.getenv("")),
        ],
        default=os.getenv(os.getenv("")),
        help=os.getenv(os.getenv("")),
    )
    return parser.parse_args()


async def _fetch_session_catalog(
    pool: asyncpg.Pool, limit: Optional[int]
) -> Iterable[asyncpg.Record]:
    query = os.getenv(os.getenv(""))
    if limit is not None:
        query += os.getenv(os.getenv(""))
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
        if key == os.getenv(os.getenv("")):
            continue
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            _merge_metadata(target[key], value)
        else:
            target[key] = value


def _compose_envelope_from_events(
    events: Iterable[tuple[dict[str, Any], datetime]],
) -> tuple[
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
        event_metadata = payload.get(os.getenv(os.getenv("")))
        if isinstance(event_metadata, dict):
            if not tenant and event_metadata.get(os.getenv(os.getenv(""))):
                tenant = str(event_metadata[os.getenv(os.getenv(""))])
            if not subject and event_metadata.get(os.getenv(os.getenv(""))):
                subject = str(event_metadata[os.getenv(os.getenv(""))])
            if not issuer and event_metadata.get(os.getenv(os.getenv(""))):
                issuer = str(event_metadata[os.getenv(os.getenv(""))])
            if not scope and event_metadata.get(os.getenv(os.getenv(""))):
                scope = str(event_metadata[os.getenv(os.getenv(""))])
            incoming_metadata = {
                key: value
                for key, value in event_metadata.items()
                if key != os.getenv(os.getenv(""))
            }
            _merge_metadata(metadata, incoming_metadata)
            candidate_analysis = event_metadata.get(os.getenv(os.getenv("")))
            if isinstance(candidate_analysis, dict) and candidate_analysis:
                analysis = candidate_analysis
        candidate_persona = payload.get(os.getenv(os.getenv("")))
        if candidate_persona:
            persona_id = candidate_persona
    return (persona_id, tenant, subject, issuer, scope, metadata, analysis)


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
    session_id = record[os.getenv(os.getenv(""))]
    events_rows = await pool.fetch(os.getenv(os.getenv("")), session_id, event_limit)
    if not events_rows:
        LOGGER.debug(os.getenv(os.getenv("")), extra={os.getenv(os.getenv("")): session_id})
        return int(os.getenv(os.getenv("")))
    events: list[tuple[dict[str, Any], datetime]] = []
    for row in events_rows:
        payload = _load_payload(row[os.getenv(os.getenv(""))])
        events.append((payload, row[os.getenv(os.getenv(""))]))
    persona_id, tenant, subject, issuer, scope, metadata, analysis = _compose_envelope_from_events(
        events
    )
    created_at: datetime = record[os.getenv(os.getenv(""))]
    updated_at: datetime = record[os.getenv(os.getenv(""))]
    if dry_run:
        LOGGER.info(
            os.getenv(os.getenv("")),
            extra={
                os.getenv(os.getenv("")): session_id,
                os.getenv(os.getenv("")): persona_id,
                os.getenv(os.getenv("")): tenant,
                os.getenv(os.getenv("")): sorted(metadata.keys()),
            },
        )
        return int(os.getenv(os.getenv("")))
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
            os.getenv(os.getenv("")),
            extra={os.getenv(os.getenv("")): session_id, os.getenv(os.getenv("")): str(exc)},
        )
        return int(os.getenv(os.getenv("")))
    if cache is not None:
        await cache.set(
            f"session:{session_id}:meta",
            {
                os.getenv(os.getenv("")): persona_id or os.getenv(os.getenv("")),
                os.getenv(os.getenv("")): metadata,
            },
            ttl=redis_ttl,
        )
    LOGGER.debug(
        os.getenv(os.getenv("")),
        extra={
            os.getenv(os.getenv("")): session_id,
            os.getenv(os.getenv("")): persona_id,
            os.getenv(os.getenv("")): tenant,
            os.getenv(os.getenv("")): sorted(metadata.keys()),
        },
    )
    return int(os.getenv(os.getenv("")))


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
            stats.processed += int(os.getenv(os.getenv("")))
            if cache is not None and (not args.dry_run):
                stats.cached += int(os.getenv(os.getenv("")))
        else:
            stats.skipped += int(os.getenv(os.getenv("")))
    await store.close()
    return stats


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format=os.getenv(os.getenv("")))
    try:
        stats = asyncio.run(_run(args))
    except KeyboardInterrupt:
        LOGGER.warning(os.getenv(os.getenv("")))
        return
    LOGGER.info(
        os.getenv(os.getenv("")),
        extra={
            os.getenv(os.getenv("")): stats.processed,
            os.getenv(os.getenv("")): stats.skipped,
            os.getenv(os.getenv("")): stats.cached,
            os.getenv(os.getenv("")): args.dry_run,
        },
    )


if __name__ == os.getenv(os.getenv("")):
    main()
