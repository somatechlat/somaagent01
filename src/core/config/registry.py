"""Configuration Registry for SomaAgent01.

VIBE CODING RULES COMPLIANT:
- NO SHIMS: Real configuration registry only
- NO FALLBACKS: Single source of truth only
- NO FAKE ANYTHING: Production-ready registry
- NO LEGACY: Modern registry patterns
- NO BACKUPS: No duplicate registry logic
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, TypeVar

from .loader import ConfigLoader, get_config_loader
from .models import Config

T = TypeVar("T")


@dataclass
class ConfigSubscription:
    """Configuration subscription details."""

    callback: Callable[[Config], None]
    name: str
    owner: str


class ConfigRegistry:
    """Single configuration registry for SomaAgent01.

    VIBE CODING RULES COMPLIANT:
    - NO SHIMS: Real configuration registry
    - NO FALLBACKS: Single source of truth
    - NO FAKE ANYTHING: Production-ready implementation
    - NO LEGACY: Modern registry patterns
    - NO BACKUPS: No duplicate registry logic
    """

    def __init__(self, config_loader: Optional[ConfigLoader] = None):
        """Initialize configuration registry.

        Args:
            config_loader: Configuration loader instance
        """
        self._config_loader = config_loader or get_config_loader()
        self._current_config: Optional[Config] = None
        self._subscriptions: Dict[str, ConfigSubscription] = {}
        self._lock = threading.RLock()
        self._initialized = False

    def initialize(self) -> None:
        """Initialize configuration registry.

        Loads initial configuration and sets up registry.
        """
        with self._lock:
            if self._initialized:
                return

            # Load initial configuration
            self._current_config = self._config_loader.load_config()
            self._initialized = True

    def get_config(self) -> Config:
        """Get current configuration.

        Returns:
            Config: Current configuration

        Raises:
            RuntimeError: If registry not initialized
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
            return self._current_config

    def refresh_config(self) -> None:
        """Refresh configuration from loader.

        Reloads configuration and notifies subscribers of changes.
        """
        with self._lock:
            if not self._initialized:
                self.initialize()
                return

            # Get previous configuration
            old_config = self._current_config

            # Load new configuration
            new_config = self._config_loader.load_config(force_reload=True)

            # Update current configuration
            self._current_config = new_config

            # Notify subscribers if configuration changed
            if old_config != new_config:
                self._notify_subscribers(new_config)

    def subscribe(self, callback: Callable[[Config], None], name: str, owner: str) -> None:
        """Subscribe to configuration changes.

        Args:
            callback: Callback function to call on configuration changes
            name: Subscription name
            owner: Subscription owner (service/module name)
        """
        with self._lock:
            subscription = ConfigSubscription(
                callback=callback,
                name=name,
                owner=owner,
            )

            key = f"{owner}.{name}"
            self._subscriptions[key] = subscription

    def unsubscribe(self, name: str, owner: str) -> None:
        """Unsubscribe from configuration changes.

        Args:
            name: Subscription name
            owner: Subscription owner (service/module name)
        """
        with self._lock:
            key = f"{owner}.{name}"
            self._subscriptions.pop(key, None)

    def _notify_subscribers(self, new_config: Config) -> None:
        """Notify subscribers of configuration changes.

        Args:
            new_config: New configuration
        """
        # Create copy of subscriptions to avoid modification during iteration
        subscriptions = list(self._subscriptions.values())

        for subscription in subscriptions:
            try:
                subscription.callback(new_config)
            except Exception as e:
                # Log error but continue with other subscribers
                print(
                    f"Error in config subscription {subscription.name} from {subscription.owner}: {e}"
                )

    def get_service_config(self) -> Config.ServiceConfig:
        """Get service configuration.

        Returns:
            Config.ServiceConfig: Service configuration
        """
        config = self.get_config()
        return config.service

    def get_database_config(self) -> Config.DatabaseConfig:
        """Get database configuration.

        Returns:
            Config.DatabaseConfig: Database configuration
        """
        config = self.get_config()
        return config.database

    def get_kafka_config(self) -> Config.KafkaConfig:
        """Get Kafka configuration.

        Returns:
            Config.KafkaConfig: Kafka configuration
        """
        config = self.get_config()
        return config.kafka

    def get_redis_config(self) -> Config.RedisConfig:
        """Get Redis configuration.

        Returns:
            Config.RedisConfig: Redis configuration
        """
        config = self.get_config()
        return config.redis

    def get_external_config(self) -> Config.ExternalServiceConfig:
        """Get external service configuration.

        Returns:
            Config.ExternalServiceConfig: External service configuration
        """
        config = self.get_config()
        return config.external

    def get_auth_config(self) -> Config.AuthConfig:
        """Get authentication configuration.

        Returns:
            Config.AuthConfig: Authentication configuration
        """
        config = self.get_config()
        return config.auth

    def get_feature_flag(self, flag_name: str, default: bool = False) -> bool:
        """Get feature flag value.

        Args:
            flag_name: Feature flag name
            default: Default value if flag not found

        Returns:
            bool: Feature flag value
        """
        config = self.get_config()
        return config.feature_flags.get(flag_name, default)

    def get_extra_config(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """Get extra configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Optional[Any]: Configuration value
        """
        config = self.get_config()
        return config.extra.get(key, default)

    @contextmanager
    def config_context(self, override_config: Optional[Config] = None) -> Config:
        """Context manager for configuration access.

        Args:
            override_config: Optional configuration to override current config

        Yields:
            Config: Configuration object
        """
        with self._lock:
            original_config = self._current_config

            if override_config is not None:
                self._current_config = override_config

            try:
                yield self._current_config
            finally:
                if override_config is not None:
                    self._current_config = original_config

    def validate_config(self) -> bool:
        """Validate current configuration.

        Returns:
            bool: True if configuration is valid
        """
        try:
            config = self.get_config()
            # Pydantic validation happens during model creation
            # Additional validation can be added here if needed
            return True
        except Exception:
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary (sanitized).

        Returns:
            Dict[str, Any]: Sanitized configuration summary
        """
        config = self.get_config()

        return {
            "service": {
                "name": config.service.name,
                "environment": config.service.environment,
                "deployment_mode": config.service.deployment_mode,
                "host": config.service.host,
                "port": config.service.port,
                "metrics_port": config.service.metrics_port,
                "log_level": config.service.log_level,
            },
            "database": {
                "pool_size": config.database.pool_size,
                "max_overflow": config.database.max_overflow,
                "pool_timeout": config.database.pool_timeout,
                "dsn": "[REDACTED]",
            },
            "kafka": {
                "bootstrap_servers": config.kafka.bootstrap_servers,
                "security_protocol": config.kafka.security_protocol,
                "sasl_mechanism": config.kafka.sasl_mechanism,
                "sasl_username": config.kafka.sasl_username,
                "sasl_password": "[REDACTED]",
            },
            "redis": {
                "max_connections": config.redis.max_connections,
                "retry_on_timeout": config.redis.retry_on_timeout,
                "socket_timeout": config.redis.socket_timeout,
                "url": "[REDACTED]",
            },
            "external": {
                "somabrain_base_url": config.external.somabrain_base_url,
                "opa_url": config.external.opa_url,
                "otlp_endpoint": config.external.otlp_endpoint,
            },
            "auth": {
                "auth_required": config.auth.auth_required,
                "jwt_algorithms": config.auth.jwt_algorithms,
                "jwt_audience": config.auth.jwt_audience,
                "jwt_issuer": config.auth.jwt_issuer,
                "jwt_leeway": config.auth.jwt_leeway,
                "jwt_secret": "[REDACTED]",
                "jwt_public_key": "[REDACTED]",
                "jwt_jwks_url": config.auth.jwt_jwks_url,
                "internal_token": "[REDACTED]",
            },
            "feature_flags": config.feature_flags,
            "extra_keys": list(config.extra.keys()),
        }


# Global configuration registry instance
_config_registry: Optional[ConfigRegistry] = None


def get_config_registry(config_loader: Optional[ConfigLoader] = None) -> ConfigRegistry:
    """Get global configuration registry instance.

    Args:
        config_loader: Configuration loader instance

    Returns:
        ConfigRegistry: Global configuration registry instance
    """
    global _config_registry
    if _config_registry is None:
        _config_registry = ConfigRegistry(config_loader)
    return _config_registry


def initialize_config(config_file_path: Optional[str] = None) -> None:
    """Initialize global configuration system.

    Args:
        config_file_path: Path to configuration file
    """
    config_loader = get_config_loader(config_file_path)
    config_registry = get_config_registry(config_loader)
    config_registry.initialize()


def get_config() -> Config:
    """Get global configuration.

    Returns:
        Config: Global configuration
    """
    registry = get_config_registry()
    return registry.get_config()


def refresh_config() -> None:
    """Refresh global configuration."""
    registry = get_config_registry()
    registry.refresh_config()


def subscribe_to_config(callback: Callable[[Config], None], name: str, owner: str) -> None:
    """Subscribe to global configuration changes.

    Args:
        callback: Callback function to call on configuration changes
        name: Subscription name
        owner: Subscription owner (service/module name)
    """
    registry = get_config_registry()
    registry.subscribe(callback, name, owner)


def unsubscribe_from_config(name: str, owner: str) -> None:
    """Unsubscribe from global configuration changes.

    Args:
        name: Subscription name
        owner: Subscription owner (service/module name)
    """
    registry = get_config_registry()
    registry.unsubscribe(name, owner)


def get_service_config() -> Config.ServiceConfig:
    """Get global service configuration.

    Returns:
        Config.ServiceConfig: Service configuration
    """
    registry = get_config_registry()
    return registry.get_service_config()


def get_database_config() -> Config.DatabaseConfig:
    """Get global database configuration.

    Returns:
        Config.DatabaseConfig: Database configuration
    """
    registry = get_config_registry()
    return registry.get_database_config()


def get_kafka_config() -> Config.KafkaConfig:
    """Get global Kafka configuration.

    Returns:
        Config.KafkaConfig: Kafka configuration
    """
    registry = get_config_registry()
    return registry.get_kafka_config()


def get_redis_config() -> Config.RedisConfig:
    """Get global Redis configuration.

    Returns:
        Config.RedisConfig: Redis configuration
    """
    registry = get_config_registry()
    return registry.get_redis_config()


def get_external_config() -> Config.ExternalServiceConfig:
    """Get global external service configuration.

    Returns:
        Config.ExternalServiceConfig: External service configuration
    """
    registry = get_config_registry()
    return registry.get_external_config()


def get_auth_config() -> Config.AuthConfig:
    """Get global authentication configuration.

    Returns:
        Config.AuthConfig: Authentication configuration
    """
    registry = get_config_registry()
    return registry.get_auth_config()


def get_feature_flag(flag_name: str, default: bool = False) -> bool:
    """Get global feature flag value.

    Args:
        flag_name: Feature flag name
        default: Default value if flag not found

    Returns:
        bool: Feature flag value
    """
    registry = get_config_registry()
    return registry.get_feature_flag(flag_name, default)


def get_extra_config(key: str, default: Optional[Any] = None) -> Optional[Any]:
    """Get global extra configuration value.

    Args:
        key: Configuration key
        default: Default value if key not found

    Returns:
        Optional[Any]: Configuration value
    """
    registry = get_config_registry()
    return registry.get_extra_config(key, default)


@contextmanager
def config_context(override_config: Optional[Config] = None) -> Config:
    """Context manager for global configuration access.

    Args:
        override_config: Optional configuration to override current config

    Yields:
        Config: Configuration object
    """
    registry = get_config_registry()
    with registry.config_context(override_config) as config:
        yield config


def validate_config() -> bool:
    """Validate global configuration.

    Returns:
        bool: True if configuration is valid
    """
    registry = get_config_registry()
    return registry.validate_config()


def get_config_summary() -> Dict[str, Any]:
    """Get global configuration summary (sanitized).

    Returns:
        Dict[str, Any]: Sanitized configuration summary
    """
    registry = get_config_registry()
    return registry.get_config_summary()
