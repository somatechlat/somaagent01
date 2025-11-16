"""Entry point for the gateway service when run as a standalone process.

This allows the orchestrator to start the gateway service as a subprocess.
"""

import asyncio
import logging
import uvicorn

from orchestrator.config import CentralizedConfig
from .service import GatewayService

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


async def main():
    """Main entry point for the gateway service."""
    config = CentralizedConfig()
    service = GatewayService(config)
    
    # Start the service using uvicorn
    await uvicorn.run(
        service.app,
        host=config.gateway_host,
        port=config.gateway_port,
        log_level=config.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    asyncio.run(main())