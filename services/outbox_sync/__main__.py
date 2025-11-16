"""Entry point for the outbox sync service when run as a standalone process.

This allows the orchestrator to start the outbox sync service as a subprocess.
"""

import asyncio
import logging
import uvicorn

from orchestrator.config import CentralizedConfig
from .service import OutboxSyncService

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


async def main():
    """Main entry point for the outbox sync service."""
    config = CentralizedConfig()
    service = OutboxSyncService(config)
    
    # Start the service using uvicorn
    await uvicorn.run(
        service.app,
        host=config.outbox_sync_host,
        port=config.outbox_sync_port,
        log_level=config.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    asyncio.run(main())