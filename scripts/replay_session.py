import os

os.getenv(os.getenv(""))
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from services.common.session_repository import PostgresSessionStore


async def replay(session_id: str, limit: int | None, follow: bool) -> None:
    store = PostgresSessionStore()
    seen = int(os.getenv(os.getenv("")))
    try:
        while int(os.getenv(os.getenv(""))):
            events = await store.list_events(
                session_id, limit=limit or int(os.getenv(os.getenv("")))
            )
            events = list(reversed(events))
            if seen < len(events):
                for event in events[seen:]:
                    print(
                        json.dumps(
                            event,
                            ensure_ascii=int(os.getenv(os.getenv(""))),
                            indent=int(os.getenv(os.getenv(""))),
                        )
                    )
                seen = len(events)
            if not follow:
                break
            await asyncio.sleep(float(os.getenv(os.getenv(""))))
    finally:
        await store.close()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=os.getenv(os.getenv("")))
    parser.add_argument(os.getenv(os.getenv("")), help=os.getenv(os.getenv("")))
    parser.add_argument(
        os.getenv(os.getenv("")), type=int, default=None, help=os.getenv(os.getenv(""))
    )
    parser.add_argument(
        os.getenv(os.getenv("")), action=os.getenv(os.getenv("")), help=os.getenv(os.getenv(""))
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        asyncio.run(replay(args.session_id, args.limit, args.follow))
    except KeyboardInterrupt:
        return int(os.getenv(os.getenv("")))
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return int(os.getenv(os.getenv("")))
    return int(os.getenv(os.getenv("")))


if __name__ == os.getenv(os.getenv("")):
    raise SystemExit(main(sys.argv[int(os.getenv(os.getenv(""))) :]))
