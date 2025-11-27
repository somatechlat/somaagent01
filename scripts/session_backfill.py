import os
os.getenv(os.getenv('VIBE_E8D920CC'))
from __future__ import annotations
import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Optional
import asyncpg
from services.common.session_repository import ensure_schema, PostgresSessionStore, RedisSessionCache
LOGGER = logging.getLogger(os.getenv(os.getenv('VIBE_36339433')))


@dataclass(slots=int(os.getenv(os.getenv('VIBE_DC4FB2C1'))))
class BackfillStats:
    processed: int = int(os.getenv(os.getenv('VIBE_0F354F3C')))
    skipped: int = int(os.getenv(os.getenv('VIBE_0F354F3C')))
    cached: int = int(os.getenv(os.getenv('VIBE_0F354F3C')))


def _parse_args() ->argparse.Namespace:
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv(
        'VIBE_167817AF')))
    parser.add_argument(os.getenv(os.getenv('VIBE_27F85ECC')), type=int,
        default=None, help=os.getenv(os.getenv('VIBE_65B08DE3')))
    parser.add_argument(os.getenv(os.getenv('VIBE_78385655')), type=int,
        default=int(os.getenv(os.getenv('VIBE_8148C1E3'))), help=os.getenv(
        os.getenv('VIBE_0178FA1A')))
    parser.add_argument(os.getenv(os.getenv('VIBE_81CDDDB1')), action=os.
        getenv(os.getenv('VIBE_7152FC54')), help=os.getenv(os.getenv(
        'VIBE_0C036011')))
    parser.add_argument(os.getenv(os.getenv('VIBE_08367EAF')), action=os.
        getenv(os.getenv('VIBE_7152FC54')), help=os.getenv(os.getenv(
        'VIBE_829F42FC')))
    parser.add_argument(os.getenv(os.getenv('VIBE_7BA3F9E0')), type=int,
        default=int(os.getenv(os.getenv('VIBE_21CABE60'))), help=os.getenv(
        os.getenv('VIBE_BBC2F05D')))
    parser.add_argument(os.getenv(os.getenv('VIBE_4120F611')), choices=[os.
        getenv(os.getenv('VIBE_1200DCF5')), os.getenv(os.getenv(
        'VIBE_7B52F24E')), os.getenv(os.getenv('VIBE_126D4FF1')), os.getenv
        (os.getenv('VIBE_E0B0EA56'))], default=os.getenv(os.getenv(
        'VIBE_1200DCF5')), help=os.getenv(os.getenv('VIBE_A46BD77E')))
    return parser.parse_args()


async def _fetch_session_catalog(pool: asyncpg.Pool, limit: Optional[int]
    ) ->Iterable[asyncpg.Record]:
    query = os.getenv(os.getenv('VIBE_C2DE2108'))
    if limit is not None:
        query += os.getenv(os.getenv('VIBE_E2148CD1'))
        return await pool.fetch(query, limit)
    return await pool.fetch(query)


def _load_payload(payload: Any) ->dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        return json.loads(payload)
    raise TypeError(f'Unsupported payload type: {type(payload)!r}')


def _merge_metadata(target: dict[str, Any], incoming: dict[str, Any]) ->None:
    for key, value in incoming.items():
        if key == os.getenv(os.getenv('VIBE_6BAA6ACF')):
            continue
        if key in target and isinstance(target[key], dict) and isinstance(value
            , dict):
            _merge_metadata(target[key], value)
        else:
            target[key] = value


def _compose_envelope_from_events(events: Iterable[tuple[dict[str, Any],
    datetime]]) ->tuple[Optional[str], Optional[str], Optional[str],
    Optional[str], Optional[str], dict[str, Any], dict[str, Any]]:
    metadata: dict[str, Any] = {}
    analysis: dict[str, Any] = {}
    persona_id: Optional[str] = None
    tenant: Optional[str] = None
    subject: Optional[str] = None
    issuer: Optional[str] = None
    scope: Optional[str] = None
    for payload, _ in events:
        event_metadata = payload.get(os.getenv(os.getenv('VIBE_D6151899')))
        if isinstance(event_metadata, dict):
            if not tenant and event_metadata.get(os.getenv(os.getenv(
                'VIBE_46FDA7DD'))):
                tenant = str(event_metadata[os.getenv(os.getenv(
                    'VIBE_46FDA7DD'))])
            if not subject and event_metadata.get(os.getenv(os.getenv(
                'VIBE_137A4DB5'))):
                subject = str(event_metadata[os.getenv(os.getenv(
                    'VIBE_137A4DB5'))])
            if not issuer and event_metadata.get(os.getenv(os.getenv(
                'VIBE_28D69C4F'))):
                issuer = str(event_metadata[os.getenv(os.getenv(
                    'VIBE_28D69C4F'))])
            if not scope and event_metadata.get(os.getenv(os.getenv(
                'VIBE_EB049B02'))):
                scope = str(event_metadata[os.getenv(os.getenv(
                    'VIBE_EB049B02'))])
            incoming_metadata = {key: value for key, value in
                event_metadata.items() if key != os.getenv(os.getenv(
                'VIBE_6BAA6ACF'))}
            _merge_metadata(metadata, incoming_metadata)
            candidate_analysis = event_metadata.get(os.getenv(os.getenv(
                'VIBE_6BAA6ACF')))
            if isinstance(candidate_analysis, dict) and candidate_analysis:
                analysis = candidate_analysis
        candidate_persona = payload.get(os.getenv(os.getenv('VIBE_2440CCE4')))
        if candidate_persona:
            persona_id = candidate_persona
    return persona_id, tenant, subject, issuer, scope, metadata, analysis


async def _process_session(pool: asyncpg.Pool, store: PostgresSessionStore,
    cache: Optional[RedisSessionCache], record: asyncpg.Record, *,
    event_limit: int, dry_run: bool, redis_ttl: int) ->bool:
    session_id = record[os.getenv(os.getenv('VIBE_0C99518A'))]
    events_rows = await pool.fetch(os.getenv(os.getenv('VIBE_BD70D668')),
        session_id, event_limit)
    if not events_rows:
        LOGGER.debug(os.getenv(os.getenv('VIBE_11D75383')), extra={os.
            getenv(os.getenv('VIBE_0C99518A')): session_id})
        return int(os.getenv(os.getenv('VIBE_AC847F30')))
    events: list[tuple[dict[str, Any], datetime]] = []
    for row in events_rows:
        payload = _load_payload(row[os.getenv(os.getenv('VIBE_224E72A6'))])
        events.append((payload, row[os.getenv(os.getenv('VIBE_BFC61433'))]))
    persona_id, tenant, subject, issuer, scope, metadata, analysis = (
        _compose_envelope_from_events(events))
    created_at: datetime = record[os.getenv(os.getenv('VIBE_5873C891'))]
    updated_at: datetime = record[os.getenv(os.getenv('VIBE_1687EAAD'))]
    if dry_run:
        LOGGER.info(os.getenv(os.getenv('VIBE_C1C8E2C8')), extra={os.getenv
            (os.getenv('VIBE_0C99518A')): session_id, os.getenv(os.getenv(
            'VIBE_2440CCE4')): persona_id, os.getenv(os.getenv(
            'VIBE_46FDA7DD')): tenant, os.getenv(os.getenv('VIBE_CD258F93')
            ): sorted(metadata.keys())})
        return int(os.getenv(os.getenv('VIBE_DC4FB2C1')))
    try:
        await store.backfill_envelope(session_id=session_id, persona_id=
            persona_id, tenant=tenant, subject=subject, issuer=issuer,
            scope=scope, metadata=metadata, analysis=analysis, created_at=
            created_at, updated_at=updated_at)
    except ValueError as exc:
        LOGGER.warning(os.getenv(os.getenv('VIBE_A7EFE82C')), extra={os.
            getenv(os.getenv('VIBE_0C99518A')): session_id, os.getenv(os.
            getenv('VIBE_CC2DD6CB')): str(exc)})
        return int(os.getenv(os.getenv('VIBE_AC847F30')))
    if cache is not None:
        await cache.set(f'session:{session_id}:meta', {os.getenv(os.getenv(
            'VIBE_2440CCE4')): persona_id or os.getenv(os.getenv(
            'VIBE_B729B245')), os.getenv(os.getenv('VIBE_D6151899')):
            metadata}, ttl=redis_ttl)
    LOGGER.debug(os.getenv(os.getenv('VIBE_B91609FE')), extra={os.getenv(os
        .getenv('VIBE_0C99518A')): session_id, os.getenv(os.getenv(
        'VIBE_2440CCE4')): persona_id, os.getenv(os.getenv('VIBE_46FDA7DD')
        ): tenant, os.getenv(os.getenv('VIBE_CD258F93')): sorted(metadata.
        keys())})
    return int(os.getenv(os.getenv('VIBE_DC4FB2C1')))


async def _run(args: argparse.Namespace) ->BackfillStats:
    store = PostgresSessionStore()
    await ensure_schema(store)
    cache = None if args.skip_redis else RedisSessionCache()
    pool = await store._ensure_pool()
    stats = BackfillStats()
    session_catalog = await _fetch_session_catalog(pool, args.limit)
    for record in session_catalog:
        processed = await _process_session(pool, store, cache, record,
            event_limit=args.event_limit, dry_run=args.dry_run, redis_ttl=
            args.redis_ttl)
        if processed:
            stats.processed += int(os.getenv(os.getenv('VIBE_516E0CD0')))
            if cache is not None and not args.dry_run:
                stats.cached += int(os.getenv(os.getenv('VIBE_516E0CD0')))
        else:
            stats.skipped += int(os.getenv(os.getenv('VIBE_516E0CD0')))
    await store.close()
    return stats


def main() ->None:
    args = _parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level), format=os.
        getenv(os.getenv('VIBE_0EB8329C')))
    try:
        stats = asyncio.run(_run(args))
    except KeyboardInterrupt:
        LOGGER.warning(os.getenv(os.getenv('VIBE_810F8966')))
        return
    LOGGER.info(os.getenv(os.getenv('VIBE_3852B5FA')), extra={os.getenv(os.
        getenv('VIBE_15E68E0D')): stats.processed, os.getenv(os.getenv(
        'VIBE_389B4EDD')): stats.skipped, os.getenv(os.getenv(
        'VIBE_E19BB6A3')): stats.cached, os.getenv(os.getenv(
        'VIBE_B302C48B')): args.dry_run})


if __name__ == os.getenv(os.getenv('VIBE_79A3A442')):
    main()
