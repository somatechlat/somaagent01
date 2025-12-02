"""Service Registry for SomaAgent01 Orchestrator.

The ServiceRegistry maintains a declarative list of all services that the
orchestrator manages, including their startup order, dependencies, and
critical flags. This enables deterministic service startup and shutdown.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .config import CentralizedConfig

LOGGER = logging.getLogger(__name__)


@dataclass
class ServiceDefinition:
    """Definition of a single service managed by the orchestrator."""

    name: str
    module_path: str  # Python import path to service module
    startup_order: int = 0  # Lower numbers start first
    dependencies: Set[str] = field(default_factory=set)  # Service names this depends on
    critical: bool = True  # If True, orchestrator fails if this service fails
    health_check_path: str = "/health"
    port: Optional[int] = None  # Port for HTTP services

    def __post_init__(self) -> None:
        """Validate service definition."""
        if not self.name:
            raise ValueError("Service name cannot be empty")
        if not self.module_path:
            raise ValueError(f"Service {self.name} must have module_path")


class ServiceRegistry:
    """Registry of all services managed by the orchestrator."""

    def __init__(self, config: CentralizedConfig) -> None:
        self.config = config
        self.services: Dict[str, ServiceDefinition] = {}
        self._load_services()

    def _load_services(self) -> None:
        """Load all service definitions."""
        # Core infrastructure services - start first
        self.register(
            ServiceDefinition(
                name="gateway",
                module_path="services.gateway.__main__",
                startup_order=10,
                critical=True,
                health_check_path="/v1/health",
                port=8010,
            )
        )

        # Memory services - have dependencies
        self.register(
            ServiceDefinition(
                name="memory-replicator",
                module_path="services.memory_replicator.__main__",
                startup_order=20,
                dependencies={"gateway"},
                critical=True,
                port=9412,
            )
        )

        self.register(
            ServiceDefinition(
                name="memory-sync",
                module_path="services.memory_sync.__main__",
                startup_order=30,
                dependencies={"gateway", "memory-replicator"},
                critical=True,
                port=9413,
            )
        )

        self.register(
            ServiceDefinition(
                name="outbox-sync",
                module_path="services.outbox_sync.__main__",
                startup_order=40,
                dependencies={"gateway"},
                critical=True,
                port=9469,
            )
        )

        # Processing services
        self.register(
            ServiceDefinition(
                name="conversation-worker",
                module_path="services.conversation_worker.__main__",
                startup_order=50,
                dependencies={"gateway"},
                critical=True,
                port=9410,
            )
        )

        self.register(
            ServiceDefinition(
                name="tool-executor",
                module_path="services.tool_executor.__main__",
                startup_order=60,
                dependencies={"gateway"},
                critical=True,
                port=9411,
            )
        )

        # Additional services
        self.register(
            ServiceDefinition(
                name="fasta2a-gateway",
                module_path="python.api.router",
                startup_order=70,
                dependencies={"gateway"},
                critical=False,  # Non-critical for basic functionality
                port=8011,
            )
        )

        LOGGER.info(f"Loaded {len(self.services)} services into registry")

    def register(self, service: ServiceDefinition) -> None:
        """Register a service definition."""
        if service.name in self.services:
            raise ValueError(f"Service {service.name} already registered")

        # Validate dependencies exist
        for dep in service.dependencies:
            if dep not in self.services and dep != service.name:
                # Allow self-dependency for validation purposes
                raise ValueError(f"Service {service.name} depends on unknown service: {dep}")

        self.services[service.name] = service
        LOGGER.debug(f"Registered service: {service.name}")

    def get_service(self, name: str) -> Optional[ServiceDefinition]:
        """Get a service definition by name."""
        return self.services.get(name)

    def get_services_by_startup_order(self) -> List[ServiceDefinition]:
        """Get all services sorted by startup order."""
        return sorted(self.services.values(), key=lambda s: s.startup_order)

    def get_startup_sequence(self) -> List[List[ServiceDefinition]]:
        """Get services grouped by startup order for parallel startup."""
        services_by_order: Dict[int, List[ServiceDefinition]] = {}

        for service in self.get_services_by_startup_order():
            if service.startup_order not in services_by_order:
                services_by_order[service.startup_order] = []
            services_by_order[service.startup_order].append(service)

        # Convert to list in order
        max_order = max(services_by_order.keys()) if services_by_order else 0
        return [services_by_order.get(i, []) for i in range(max_order + 1)]

    def get_shutdown_sequence(self) -> List[ServiceDefinition]:
        """Get services in reverse startup order for shutdown."""
        return list(reversed(self.get_services_by_startup_order()))

    def validate_dependencies(self) -> None:
        """Validate that all service dependencies can be satisfied."""
        for service in self.services.values():
            for dep in service.dependencies:
                if dep not in self.services:
                    raise ValueError(f"Service {service.name} depends on missing service: {dep}")

    def get_critical_services(self) -> List[ServiceDefinition]:
        """Get all critical services."""
        return [s for s in self.services.values() if s.critical]

    def get_service_dependencies(self, service_name: str) -> Set[str]:
        """Get all dependencies for a service (transitive)."""
        service = self.get_service(service_name)
        if not service:
            return set()

        all_deps = set(service.dependencies)
        for dep in service.dependencies:
            all_deps.update(self.get_service_dependencies(dep))

        return all_deps

    def can_start_service(self, service_name: str, running_services: Set[str]) -> bool:
        """Check if a service can start based on its dependencies."""
        service = self.get_service(service_name)
        if not service:
            return False

        return service.dependencies.issubset(running_services)
