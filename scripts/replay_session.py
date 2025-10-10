"""Replay a SomaAgent session from Postgres.

Usage:
    python scripts/replay_session.py SESSION_ID [--limit N] [--follow]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from services.common.session_repository import PostgresSessionStore


async def replay(session_id: str, limit: int | None, follow: bool) -> None:
    store = PostgresSessionStore()
    seen = 0
    try:
        while True:
            events = await store.list_events(session_id, limit=limit or 200)
            events = list(reversed(events))
            if seen < len(events):
                for event in events[seen:]:
                    print(json.dumps(event, ensure_ascii=False, indent=2))
                seen = len(events)
            if not follow:
                break
            await asyncio.sleep(2.0)
    finally:
        await store.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay session events from Postgres")
    parser.add_argument("session_id", help="Session identifier")
    parser.add_argument(
        "--limit", type=int, default=None, help="Maximum number of events to retrieve"
    )
    parser.add_argument("--follow", action="store_true", help="Stream new events as they arrive")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        asyncio.run(replay(args.session_id, args.limit, args.follow))
    except KeyboardInterrupt:
        return 0
    except Exception as exc:  # pragma: no cover - CLI path
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
