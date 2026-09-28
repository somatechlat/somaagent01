"""Entry point for the bridge worker service when run as a standalone process.

Run: ``python -m services.bridge_worker``
"""

from __future__ import annotations

import asyncio
import logging
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()  # noqa: E402

from services.bridge_worker.main import main as worker_main  # noqa: E402

logger = logging.getLogger(__name__)


async def main() -> None:
    """Run the bridge worker poll loop (no HTTP server required)."""
    logging.basicConfig(
        level=os.environ.get("SA01_BRIDGE_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    await worker_main()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Stopped")
