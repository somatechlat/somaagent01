"""Unified Health Monitor for SomaAgent01 Orchestrator.

The UnifiedHealthMonitor aggregates health status from all services and
provides a single health endpoint for monitoring systems.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import CentralizedConfig

LOGGER = logging.getLogger(__name__)


class ServiceHealthStatus:
    """Health status of a single service."""
    
    def __init__(self, service_name: str, healthy: bool = False, details: Optional[Dict[str, Any]] = None):
        self.service_name = service_name
        self.healthy = healthy
        self.details = details or {}
        self.last_check = 0.0
        self.consecutive_failures = 0


class UnifiedHealthMonitor:
    """Monitors health of all services and provides unified status."""
    
    def __init__(self, config: CentralizedConfig) -> None:
        self.config = config
        self.service_status: Dict[str, ServiceHealthStatus] = {}
        self.http_client: Optional[httpx.AsyncClient] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        
    async def start(self) -> None:
        """Start the health monitoring."""
        LOGGER.info("Starting unified health monitor")
        
        self.http_client = httpx.AsyncClient(timeout=5.0)
        self.shutdown_event.clear()
        
        # Start background monitoring task
        self.monitoring_task = asyncio.create_task(self._monitor_loop())
        
        LOGGER.info("Health monitor started")
    
    async def stop(self) -> None:
        """Stop the health monitoring."""
        LOGGER.info("Stopping unified health monitor")
        
        self.shutdown_event.set()
        
        if self.monitoring_task:
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.http_client:
            await self.http_client.aclose()
        
        LOGGER.info("Health monitor stopped")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self.shutdown_event.is_set():
            try:
                await self._check_all_services()
                await asyncio.sleep(10)  # Check every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                LOGGER.error(f"Error in health monitor loop: {e}")
                await asyncio.sleep(5)
    
    async def _check_all_services(self) -> None:
        """Check health of all registered services."""
        # This would integrate with the orchestrator's service registry
        # For now, we'll check the main orchestrator health
        await self._check_orchestrator_health()
    
    async def _check_orchestrator_health(self) -> None:
        """Check the health of the orchestrator itself."""
        try:
            # Check basic orchestrator functionality
            status = {
                "status": "healthy",
                "timestamp": asyncio.get_event_loop().time(),
                "services_monitored": len(self.service_status),
                "config_loaded": bool(self.config)
            }
            
            # Update orchestrator health status
            if "orchestrator" not in self.service_status:
                self.service_status["orchestrator"] = ServiceHealthStatus("orchestrator")
            
            service_status = self.service_status["orchestrator"]
            service_status.healthy = True
            service_status.details = status
            service_status.last_check = asyncio.get_event_loop().time()
            service_status.consecutive_failures = 0
            
        except Exception as e:
            LOGGER.error(f"Error checking orchestrator health: {e}")
            
            if "orchestrator" not in self.service_status:
                self.service_status["orchestrator"] = ServiceHealthStatus("orchestrator")
            
            service_status = self.service_status["orchestrator"]
            service_status.healthy = False
            service_status.details = {"error": str(e)}
            service_status.last_check = asyncio.get_event_loop().time()
            service_status.consecutive_failures += 1
    
    async def check_service_health(self, service_name: str, health_url: str) -> bool:
        """Check health of a specific service via HTTP."""
        try:
            if not self.http_client:
                return False
            
            response = await self.http_client.get(health_url)
            is_healthy = response.status_code == 200
            
            # Update service status
            if service_name not in self.service_status:
                self.service_status[service_name] = ServiceHealthStatus(service_name)
            
            service_status = self.service_status[service_name]
            service_status.healthy = is_healthy
            service_status.last_check = asyncio.get_event_loop().time()
            
            if is_healthy:
                service_status.consecutive_failures = 0
                service_status.details = {"status_code": response.status_code}
            else:
                service_status.consecutive_failures += 1
                service_status.details = {
                    "status_code": response.status_code,
                    "response": response.text[:200]  # Truncate long responses
                }
            
            return is_healthy
            
        except Exception as e:
            LOGGER.warning(f"Health check failed for service {service_name}: {e}")
            
            if service_name not in self.service_status:
                self.service_status[service_name] = ServiceHealthStatus(service_name)
            
            service_status = self.service_status[service_name]
            service_status.healthy = False
            service_status.details = {"error": str(e)}
            service_status.last_check = asyncio.get_event_loop().time()
            service_status.consecutive_failures += 1
            
            return False
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health status of all services."""
        total_services = len(self.service_status)
        healthy_services = sum(1 for status in self.service_status.values() if status.healthy)
        
        overall_healthy = total_services > 0 and healthy_services == total_services
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": asyncio.get_event_loop().time(),
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "services": {
                name: {
                    "healthy": status.healthy,
                    "last_check": status.last_check,
                    "consecutive_failures": status.consecutive_failures,
                    "details": status.details
                }
                for name, status in self.service_status.items()
            }
        }