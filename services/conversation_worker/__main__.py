"""Entry point for the conversation worker service when run as a standalone process.

This allows the orchestrator to start the conversation worker service as a subprocess.

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

from .service import ConversationWorkerService

# Use Django-configured logger (no basicConfig override)
LOGGER = logging.getLogger(__name__)


async def main():
    """Main entry point for the conversation worker service."""
    config = CentralizedConfig()
    service = ConversationWorkerService(config)

    # Start the service using uvicorn
    await uvicorn.run(
        service.app,
        host=config.conversation_worker_host,
        port=config.conversation_worker_port,
        log_level=config.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
