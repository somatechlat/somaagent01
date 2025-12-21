from __future__ import annotations

import asyncio

from services.common.outbox import OutboxPublisher
from src.core.config import cfg


async def flush(limit: int = 100) -> int:
    use_outbox = cfg.env("SA01_USE_OUTBOX", "false").lower() == "true"
    if not use_outbox:
        return 0
    outbox = OutboxPublisher()
    total = 0
    while True:
        published = await outbox.publish_pending(limit=limit)
        total += published
        if published < limit:
            break
    return total


if __name__ == "__main__":
    published = asyncio.run(flush())
    print(published)
