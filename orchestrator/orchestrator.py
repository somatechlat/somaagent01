"""Real SomaAgent01 Orchestrator implementation.

The SomaOrchestrator is responsible for starting, monitoring, and stopping
all services in the correct order with proper dependency management and
graceful shutdown handling.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Any, Dict, Optional, Set

from .config import CentralizedConfig
from .service_registry import ServiceRegistry, ServiceDefinition
from .health_monitor import UnifiedHealthMonitor

LOGGER = logging.getLogger(__name__)


class ServiceProcess:
    """Represents a running service process."""
    
    def __init__(self, definition: ServiceDefinition, process: asyncio.subprocess.Process):
        self.definition = definition
        self.process = process
        self.start_time = asyncio.get_event_loop().time()
        self.healthy = False
        self.last_health_check = 0.0


class SomaOrchestrator:
    """Main orchestrator that manages all services."""
    
    def __init__(self, config: CentralizedConfig) -> None:
        self.config = config
        self.registry = ServiceRegistry(config)
        self.health_monitor = UnifiedHealthMonitor(config)
        
        self.running_services: Dict[str, ServiceProcess] = {}
        self.shutdown_event = asyncio.Event()
        self.startup_complete = asyncio.Event()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        try:
            # Only available in Unix
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
        except (AttributeError, ValueError):
            # Windows or other platforms
            pass
    
    def _handle_signal(self, signum: int, frame: Any) -> None:
        """Handle shutdown signals."""
        LOGGER.info(f"Received signal {signum}, initiating graceful shutdown")
        if not self.shutdown_event.is_set():
            self.shutdown_event.set()
    
    async def start(self) -> None:
        """Start all services in dependency order."""
        LOGGER.info("Starting SomaAgent01 orchestrator")
        
        try:
            # Validate service dependencies
            self.registry.validate_dependencies()
            
            # Get startup sequence
            startup_sequence = self.registry.get_startup_sequence()
            
            LOGGER.info(f"Starting {len(self.registry.services)} services in {len(startup_sequence)} phases")
            
            # Start services in phases based on startup order
            for phase_num, phase_services in enumerate(startup_sequence, 1):
                if not phase_services:
                    continue
                
                LOGGER.info(f"Starting phase {phase_num} with {len(phase_services)} services")
                
                # Start all services in this phase in parallel
                startup_tasks = []
                for service_def in phase_services:
                    task = asyncio.create_task(self._start_service(service_def))
                    startup_tasks.append(task)
                
                # Wait for all services in this phase to start
                results = await asyncio.gather(*startup_tasks, return_exceptions=True)
                
                # Check for failures
                failed_services = []
                for service_def, result in zip(phase_services, results):
                    if isinstance(result, Exception):
                        LOGGER.error(f"Failed to start service {service_def.name}: {result}")
                        failed_services.append(service_def.name)
                        
                        # If critical service failed, shutdown everything
                        if service_def.critical:
                            LOGGER.critical(f"Critical service {service_def.name} failed, shutting down")
                            await self.shutdown()
                            raise RuntimeError(f"Critical service {service_def.name} failed to start")
                
                if failed_services:
                    LOGGER.warning(f"Phase {phase_num} completed with {len(failed_services)} failed services")
                else:
                    LOGGER.info(f"Phase {phase_num} completed successfully")
            
            # Start health monitoring
            await self.health_monitor.start()
            
            # Mark startup as complete
            self.startup_complete.set()
            LOGGER.info("All services started successfully")
            
        except Exception as e:
            LOGGER.error(f"Failed to start orchestrator: {e}")
            await self.shutdown()
            raise
    
    async def _start_service(self, service_def: ServiceDefinition) -> None:
        """Start a single service."""
        LOGGER.info(f"Starting service: {service_def.name}")
        
        try:
            # Import and start the service
            if service_def.port:
                # HTTP service - start with uvicorn
                cmd = [
                    sys.executable, "-m", "uvicorn",
                    f"{service_def.module_path}:app",
                    "--host", "0.0.0.0",
                    "--port", str(service_def.port)
                ]
                if self.config.environment == "DEV":
                    cmd.append("--reload")
            else:
                # Worker service - start directly
                cmd = [sys.executable, "-m", service_def.module_path]
            
            # Start the subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict(self.config.dict()), "PYTHONPATH": "/git/agent-zero"}
            )
            
            # Track the service
            service_process = ServiceProcess(service_def, process)
            self.running_services[service_def.name] = service_process
            
            LOGGER.info(f"Started service {service_def.name} with PID {process.pid}")
            
            # Wait a bit for the service to initialize
            await asyncio.sleep(2)
            
            # Perform initial health check
            await self._check_service_health(service_process)
            
        except Exception as e:
            LOGGER.error(f"Failed to start service {service_def.name}: {e}")
            raise
    
    async def _check_service_health(self, service_process: ServiceProcess) -> None:
        """Check the health of a running service."""
        # Check if the process is still running
        if service_process.process.returncode is not None:
            raise RuntimeError(f"Service {service_process.definition.name} process exited with code {service_process.process.returncode}")
        
        # If service has a health check path, perform HTTP health check
        if service_process.definition.health_check_path and service_process.definition.port:
            await self._check_http_health(service_process)
        
        service_process.healthy = True
        service_process.last_health_check = asyncio.get_event_loop().time()
        LOGGER.debug(f"Service {service_process.definition.name} is healthy")
    
    async def _check_http_health(self, service_process: ServiceProcess) -> None:
        """Perform HTTP health check for a service."""
        import httpx
        
        url = f"http://localhost:{service_process.definition.port}{service_process.definition.health_check_path}"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                
            if response.status_code != 200:
                raise RuntimeError(f"Health check failed for {service_process.definition.name}: HTTP {response.status_code}")
                
            # Try to parse JSON response if available
            try:
                health_data = response.json()
                if isinstance(health_data, dict) and health_data.get("status") != "ok":
                    raise RuntimeError(f"Health check failed for {service_process.definition.name}: {health_data.get('status', 'unknown')}")
            except (ValueError, KeyError):
                # If response is not JSON or doesn't have status field, 200 is sufficient
                pass
                
        except Exception as e:
            raise RuntimeError(f"HTTP health check failed for {service_process.definition.name}: {e}")
    
    async def shutdown(self) -> None:
        """Shutdown all services gracefully."""
        if self.shutdown_event.is_set():
            LOGGER.info("Shutdown already in progress")
            return
        
        self.shutdown_event.set()
        LOGGER.info("Starting graceful shutdown")
        
        try:
            # Stop health monitoring
            await self.health_monitor.stop()
            
            # Get shutdown sequence (reverse of startup order)
            shutdown_sequence = self.registry.get_shutdown_sequence()
            
            LOGGER.info(f"Shutting down {len(self.running_services)} services")
            
            # Shutdown services in reverse order
            for service_def in shutdown_sequence:
                if service_def.name in self.running_services:
                    await self._stop_service(service_def.name)
            
            LOGGER.info("All services stopped")
            
        except Exception as e:
            LOGGER.error(f"Error during shutdown: {e}")
            raise
        finally:
            self.running_services.clear()
    
    async def _stop_service(self, service_name: str) -> None:
        """Stop a single service."""
        service_process = self.running_services.get(service_name)
        if not service_process:
            LOGGER.warning(f"Service {service_name} not found in running services")
            return
        
        LOGGER.info(f"Stopping service: {service_name}")
        
        try:
            # Send SIGTERM first for graceful shutdown
            service_process.process.terminate()
            
            # Wait for graceful shutdown
            try:
                await asyncio.wait_for(
                    service_process.process.wait(), 
                    timeout=30.0
                )
                LOGGER.info(f"Service {service_name} stopped gracefully")
            except asyncio.TimeoutError:
                LOGGER.warning(f"Service {service_name} did not stop gracefully, killing")
                service_process.process.kill()
                await service_process.process.wait()
                LOGGER.info(f"Service {service_name} killed")
            
        except Exception as e:
            LOGGER.error(f"Error stopping service {service_name}: {e}")
            # Try to kill the process if terminate failed
            try:
                service_process.process.kill()
                await service_process.process.wait()
            except:
                pass
        finally:
            self.running_services.pop(service_name, None)
    
    async def monitor_services(self) -> None:
        """Continuously monitor running services."""
        LOGGER.info("Starting service monitoring")
        
        while not self.shutdown_event.is_set():
            try:
                # Check health of all running services
                for service_name, service_process in list(self.running_services.items()):
                    try:
                        await self._check_service_health(service_process)
                    except Exception as e:
                        LOGGER.error(f"Health check failed for service {service_name}: {e}")
                        
                        # If critical service failed, trigger shutdown
                        if service_process.definition.critical:
                            LOGGER.critical(f"Critical service {service_name} failed, shutting down")
                            asyncio.create_task(self.shutdown())
                            return
                
                # Wait before next check
                await asyncio.sleep(10)
                
            except Exception as e:
                LOGGER.error(f"Error in service monitoring: {e}")
                await asyncio.sleep(5)
    
    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        status = {
            "orchestrator": {
                "running": not self.shutdown_event.is_set(),
                "startup_complete": self.startup_complete.is_set(),
                "services_count": len(self.running_services)
            },
            "services": {}
        }
        
        for service_name, service_process in self.running_services.items():
            status["services"][service_name] = {
                "name": service_name,
                "pid": service_process.process.pid,
                "healthy": service_process.healthy,
                "start_time": service_process.start_time,
                "last_health_check": service_process.last_health_check,
                "critical": service_process.definition.critical
            }
        
        return status