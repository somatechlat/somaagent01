"""Entry point for the FastA2A gateway service when run as a standalone process.

This allows the orchestrator to start the FastA2A gateway service as a subprocess.
"""

import asyncio
import logging

import uvicorn

from orchestrator.config import CentralizedConfig

from .service import FastA2AGatewayService

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


async def main():
    """Main entry point for the FastA2A gateway service."""
    config = CentralizedConfig()
    service = FastA2AGatewayService(config)
    
    # Start the service using uvicorn
    await uvicorn.run(
        service.app,
        host=config.fasta2a_gateway_host,
        port=config.fasta2a_gateway_port,
        log_level=config.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    asyncio.run(main())