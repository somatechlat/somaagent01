#!/usr/bin/env python3
"""Utility to create/upgrade the message_outbox table."""

import asyncio
import logging

from services.common.outbox_repository import ensure_schema, OutboxStore


async def _main() -> None:
    logging.basicConfig(level="INFO")
    store = OutboxStore()
    await ensure_schema(store)
    await store.close()


if __name__ == "__main__":
    asyncio.run(_main())
