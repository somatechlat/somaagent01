import os
os.getenv(os.getenv('VIBE_5F784D4B'))
import asyncio
import logging
from services.common.outbox_repository import ensure_schema, OutboxStore


async def _main() ->None:
    logging.basicConfig(level=os.getenv(os.getenv('VIBE_E2291347')))
    store = OutboxStore()
    await ensure_schema(store)
    await store.close()


if __name__ == os.getenv(os.getenv('VIBE_26CAD79F')):
    asyncio.run(_main())
