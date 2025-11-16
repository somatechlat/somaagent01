"""Real entry point for the SomaAgent01 orchestrator.

The orchestrator is responsible for starting all service processes, managing
health checks, providing a unified FastAPI HTTP API, and handling graceful
shutdown. This is the single entry point for the entire SomaAgent01 system.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from .config import load_config, CentralizedConfig
from .orchestrator import SomaOrchestrator
from .health_monitor import UnifiedHealthMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)


# Create FastAPI app for orchestrator HTTP API
app = FastAPI(title="SomaAgent01 Orchestrator", version="1.0.0")

# Global orchestrator instance
_orchestrator: SomaOrchestrator | None = None


def get_orchestrator() -> SomaOrchestrator:
    """Get the global orchestrator instance."""
    if _orchestrator is None:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    return _orchestrator


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize the orchestrator on startup."""
    global _orchestrator
    
    try:
        config = load_config()
        _orchestrator = SomaOrchestrator(config)
        
        # Start the orchestrator
        await _orchestrator.start()
        
        # Start service monitoring
        monitoring_task = asyncio.create_task(_orchestrator.monitor_services())
        
        LOGGER.info("Orchestrator HTTP API started successfully")
        
    except Exception as e:
        LOGGER.error(f"Failed to start orchestrator: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Shutdown the orchestrator gracefully."""
    global _orchestrator
    
    if _orchestrator:
        try:
            await _orchestrator.shutdown()
            LOGGER.info("Orchestrator shutdown successfully")
        except Exception as e:
            LOGGER.error(f"Error during orchestrator shutdown: {e}")


@app.get("/v1/health")
async def health_check() -> Dict[str, Any]:
    """Unified health check endpoint for all services."""
    orchestrator = get_orchestrator()
    return orchestrator.get_service_status()


@app.get("/v1/status")
async def orchestrator_status() -> Dict[str, Any]:
    """Get detailed orchestrator status."""
    orchestrator = get_orchestrator()
    status = orchestrator.get_service_status()
    
    # Add health monitor status
    if hasattr(orchestrator, 'health_monitor'):
        health_status = orchestrator.health_monitor.get_overall_health()
        status["health_monitor"] = health_status
    
    return status


@app.post("/v1/shutdown")
async def shutdown_orchestrator() -> Dict[str, str]:
    """Initiate graceful shutdown of the orchestrator."""
    global _orchestrator
    
    if _orchestrator:
        asyncio.create_task(_orchestrator.shutdown())
        return {"status": "shutting_down", "message": "Graceful shutdown initiated"}
    
    return {"status": "not_running", "message": "Orchestrator is not running"}


def run_orchestrator() -> Dict[str, str]:
    """Legacy compatibility function - now starts real orchestrator.

    This function is kept for backward compatibility but now starts the
    actual orchestrator instead of just returning config.
    """
    cfg: CentralizedConfig = load_config()
    
    # Start the orchestrator HTTP server
    uvicorn.run(
        "orchestrator.main:app",
        host="0.0.0.0",
        port=8000,
        reload=cfg.environment == "DEV",
        log_level="info"
    )
    
    # This won't actually return due to uvicorn.run() blocking
    return {
        "service_name": cfg.service_name,
        "environment": cfg.environment,
        "status": "running"
    }


async def main_async() -> None:
    """Main async entry point for the orchestrator."""
    parser = argparse.ArgumentParser(description="SomaAgent01 Orchestrator")
    parser.add_argument("--port", type=int, default=8000, help="HTTP API port")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP API host")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config = load_config()
        
        # Create and start orchestrator
        orchestrator = SomaOrchestrator(config)
        
        # Start the orchestrator
        await orchestrator.start()
        
        # Start HTTP API server
        config = uvicorn.Config(
            app,
            host=args.host,
            port=args.port,
            reload=config.environment == "DEV",
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        # Run monitoring and HTTP server concurrently
        await asyncio.gather(
            orchestrator.monitor_services(),
            server.serve()
        )
        
    except KeyboardInterrupt:
        LOGGER.info("Received interrupt signal")
    except Exception as e:
        LOGGER.error(f"Orchestrator failed: {e}")
        sys.exit(1)
    finally:
        if 'orchestrator' in locals():
            await orchestrator.shutdown()


def main() -> None:
    """Main entry point for the orchestrator."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        LOGGER.info("Orchestrator stopped by user")
    except Exception as e:
        LOGGER.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
