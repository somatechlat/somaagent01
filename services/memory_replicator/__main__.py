"""Entry point for the memory replicator service when run as a standalone process.

This allows the orchestrator to start the memory replicator service as a subprocess.

"""

import asyncio
import logging
import os

# Django setup MUST happen before any Django-dependent imports
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "services.gateway.settings")
import django

django.setup()

import uvicorn

from orchestrator.config import CentralizedConfig

from .service import MemoryReplicatorService

# Use Django-configured logger (no basicConfig override)
LOGGER = logging.getLogger(__name__)


async def main():
    """Main entry point for the memory replicator service."""
    config = CentralizedConfig()
    service = MemoryReplicatorService(config)

    # Start the service using uvicorn
    await uvicorn.run(
        service.app,
        host=config.memory_replicator_host,
        port=config.memory_replicator_port,
        log_level=config.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    asyncio.run(main())