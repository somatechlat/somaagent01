"""Centralized Configuration System for SomaAgent01.

VIBE CODING RULES COMPLIANT:
- NO SHIMS: Real configuration only
- NO FALLBACKS: Single source of truth
- NO FAKE ANYTHING: Production-ready implementation
- NO LEGACY: Modern patterns only
- NO BACKUPS: No duplicate configuration systems
"""

from .models import (
    Config,
    ServiceConfig,
    DatabaseConfig,
    KafkaConfig,
    RedisConfig,
    ExternalServiceConfig,
    AuthConfig,
)
from .loader import (
    ConfigLoader,
    EnvironmentMapping,
    get_config_loader,
    reload_config,
)
from .registry import (
    ConfigRegistry,
    ConfigSubscription,
    get_config_registry,
    initialize_config,
    get_config,
    refresh_config,
    subscribe_to_config,
    unsubscribe_from_config,
    get_service_config,
    get_database_config,
    get_kafka_config,
    get_redis_config,
    get_external_config,
    get_auth_config,
    get_feature_flag,
    get_extra_config,
    config_context,
    validate_config,
    get_config_summary,
)

__all__ = [
    # Models
    "Config",
    "ServiceConfig",
    "DatabaseConfig",
    "KafkaConfig",
    "RedisConfig",
    "ExternalServiceConfig",
    "AuthConfig",
    # Loader
    "ConfigLoader",
    "EnvironmentMapping",
    "get_config_loader",
    "reload_config",
    # Registry
    "ConfigRegistry",
    "ConfigSubscription",
    "get_config_registry",
    "initialize_config",
    "get_config",
    "refresh_config",
    "subscribe_to_config",
    "unsubscribe_from_config",
    "get_service_config",
    "get_database_config",
    "get_kafka_config",
    "get_redis_config",
    "get_external_config",
    "get_auth_config",
    "get_feature_flag",
    "get_extra_config",
    "config_context",
    "validate_config",
    "get_config_summary",
]

# Single source of truth for all configuration
# This eliminates 5 duplicate configuration systems:
# - services/common/settings_sa01.py
# - services/common/admin_settings.py  
# - services/common/runtime_config.py
# - services/common/registry.py
# - services/common/settings_registry.py