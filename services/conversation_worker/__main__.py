"""Entry point for the conversation worker service when run as a standalone process.

This allows the orchestrator to start the conversation worker service as a subprocess.
"""

import asyncio
import logging

import uvicorn

from orchestrator.config import CentralizedConfig

from .service import ConversationWorkerService

# Configure logging
logging.basicConfig(level=logging.INFO)
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
