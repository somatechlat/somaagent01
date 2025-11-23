"""Orchestrator package – entry point for the unified SomaAgent01 process.

The orchestrator starts all services (gateway, conversation worker, tool executor,
memory services, etc.) in a deterministic order, provides a single health
endpoint, and ensures graceful shutdown.  It replaces the previous ad‑hoc
service‑specific entry points.
"""
"""Orchestrator package for SomaAgent01.

Provides a single entry point that coordinates the lifecycle of all
services, centralises configuration, health monitoring and observability.

The package follows the VIBE CODING RULES – no placeholders, real
implementations only, and full type‑checked configuration.
"""

from .config import CentralizedConfig, load_config
from .health_monitor import UnifiedHealthMonitor
from .main import app, main, run_orchestrator
from .orchestrator import SomaOrchestrator
from .service_registry import ServiceDefinition, ServiceRegistry

__all__ = [
    "run_orchestrator",
    "main", 
    "app",
    "SomaOrchestrator",
    "ServiceRegistry", 
    "ServiceDefinition",
    "UnifiedHealthMonitor",
    "CentralizedConfig",
    "load_config"
]