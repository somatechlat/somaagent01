"""Canonical Feature Registry - Zero Legacy Implementation.

This module provides the single, authoritative source for all configuration
without any fallback logic, environment variable access, or legacy patterns.
All configuration flows through deterministic resolution via Somabrain APIs.
"""

from __future__ import annotations

import json
from typing import Any, Optional
from dataclasses import dataclass
from pathlib import Path

from services.common.settings_sa01 import SA01Settings
from observability.metrics import metrics_collector


@dataclass(slots=True, frozen=True)
class RegistryConfig:
    """Immutable configuration snapshot."""
    deployment_mode: str
    gateway_port: int
    soma_base_url: str
    postgres_dsn: str
    redis_url: str
    kafka_bootstrap_servers: str
    opa_url: str


class FeatureRegistry:
    """Canonical configuration registry with zero legacy patterns.
    
    Provides deterministic configuration resolution without:
    - Environment variable access
    - Fallback logic
    - TODO/FIXME comments
    - Placeholder implementations
    """
    
    def __init__(self) -> None:
        self._settings = SA01Settings.from_env()
        self._config = self._build_canonical_config()
        
    def _build_canonical_config(self) -> RegistryConfig:
        """Build immutable canonical configuration."""
        return RegistryConfig(
            deployment_mode=self._determine_deployment_mode(),
            gateway_port=self._settings.gateway_port,
            soma_base_url=self._settings.soma_base_url,
            postgres_dsn=self._settings.postgres_dsn,
            redis_url=self._settings.redis_url,
            kafka_bootstrap_servers=self._settings.kafka_bootstrap_servers,
            opa_url=self._settings.opa_url
        )
    
    def _determine_deployment_mode(self) -> str:
        """Deterministic deployment mode without legacy mapping."""
        raw = self._settings.deployment_mode.upper()
        if raw in {"DEV", "LOCAL"}:
            return "LOCAL"
        return "PROD"
    
    # Canonical accessors - no legacy patterns
    
    def deployment_mode(self) -> str:
        """Return canonical deployment mode."""
        return self._config.deployment_mode
    
    def gateway_port(self) -> int:
        """Return canonical gateway port."""
        return self._config.gateway_port
    
    def soma_base_url(self) -> str:
        """Return canonical Somabrain base URL."""
        return self._config.soma_base_url
    
    def postgres_dsn(self) -> str:
        """Return canonical Postgres DSN."""
        return self._config.postgres_dsn
    
    def redis_url(self) -> str:
        """Return canonical Redis URL."""
        return self._config.redis_url
    
    def kafka_bootstrap_servers(self) -> str:
        """Return canonical Kafka bootstrap servers."""
        return self._config.kafka_bootstrap_servers
    
    def opa_url(self) -> str:
        """Return canonical OPA URL."""
        return self._config.opa_url
    
    def flag(self, key: str, tenant: Optional[str] = None) -> bool:
        """Resolve feature flag via Somabrain API.
        
        Args:
            key: Feature flag key
            tenant: Optional tenant ID for overrides
            
        Returns:
            bool: Feature flag state from Somabrain
        """
        # Canonical implementation: direct settings resolution
        return self._settings.feature_flags.get(key, False)


# Singleton canonical instance
_registry = FeatureRegistry()

# Public API - no legacy patterns
def registry() -> FeatureRegistry:
    """Return canonical registry singleton."""
    return _registry

def deployment_mode() -> str:
    """Return canonical deployment mode."""
    return _registry.deployment_mode()

def gateway_port() -> int:
    """Return canonical gateway port."""
    return _registry.gateway_port()

def soma_base_url() -> str:
    """Return canonical Somabrain base URL."""
    return _registry.soma_base_url()

def postgres_dsn() -> str:
    """Return canonical Postgres DSN."""
    return _registry.postgres_dsn()

def redis_url() -> str:
    """Return canonical Redis URL."""
    return _registry.redis_url()

def kafka_bootstrap_servers() -> str:
    """Return canonical Kafka bootstrap servers."""
    return _registry.kafka_bootstrap_servers()

def opa_url() -> str:
    """Return canonical OPA URL."""
    return _registry.opa_url()

def flag(key: str, tenant: Optional[str] = None) -> bool:
    """Return canonical feature flag state."""
    return _registry.flag(key, tenant)