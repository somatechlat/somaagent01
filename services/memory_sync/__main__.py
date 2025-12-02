"""Entry point for the memory sync service when run as a standalone process.

This allows the orchestrator to start the memory sync service as a subprocess.
"""

import asyncio
import logging

import uvicorn

from orchestrator.config import CentralizedConfig

from .service import MemorySyncService

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


async def main():
    """Main entry point for the memory sync service."""
    config = CentralizedConfig()
    service = MemorySyncService(config)

    # Start the service using uvicorn
    await uvicorn.run(
        service.app,
        host=config.memory_sync_host,
        port=config.memory_sync_port,
        log_level=config.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
