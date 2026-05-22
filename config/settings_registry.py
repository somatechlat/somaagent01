"""
SOMA Centralized Configuration System
======================================

VIBE Rule 100: Centralized Sovereignty - ALL settings in ONE place
VIBE Rule 91: Zero-Fallback Mandate - Fail-fast on missing config
VIBE Rule 164: Vault-Mandatory - ALL secrets from Vault

This module is the SINGLE SOURCE OF TRUTH for configuration dispatch
based on SA01_DEPLOYMENT_MODE (STANDALONE | AAAS | DEV | PROD).
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Type, TypeVar

LOGGER = logging.getLogger(__name__)

T = TypeVar("T", bound="BaseSettings")


# ═══════════════════════════════════════════════════════════════════════════════
# VIBE Rule 91: Zero-Fallback Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def get_required_env(
    var_name: str, *, allow_dev_default: bool = False, dev_default: str = ""
) -> str:
    """Get required environment variable with fail-fast in production.

    VIBE Rule 91: Zero-Fallback Mandate
    - PROD mode: Missing env var raises RuntimeError
    - DEV mode: Returns dev_default with warning (if allow_dev_default=True)
    """
    value = os.environ.get(var_name)
    if value:
        return value

    deployment_mode = os.environ.get("SA01_DEPLOYMENT_MODE", "DEV").upper()

    if deployment_mode in ("PROD", "PRODUCTION"):
        raise RuntimeError(
            f"VIBE Rule 91 VIOLATION: {var_name} is REQUIRED in production. "
            f"Set {var_name} in your environment or Vault."
        )

    if allow_dev_default:
        LOGGER.warning("⚠️ [DEV MODE] Using default for %s. Set this in production!", var_name)
        return dev_default

    raise RuntimeError(f"Environment variable {var_name} is required but not set.")


def get_optional_env(var_name: str, default: str = "") -> str:
    """Get optional environment variable with fallback allowed."""
    return os.environ.get(var_name, default)


# ═══════════════════════════════════════════════════════════════════════════════
# Base Settings Abstract Class
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class BaseSettings(ABC):
    """Abstract base for deployment-specific settings."""

    # Core identification
    deployment_mode: str = field(default="")
    deployment_target: str = field(default="LOCAL")  # LOCAL | EKS | GKE

    # Database
    postgres_host: str = field(default="")
    postgres_port: int = field(default=5432)
    postgres_db: str = field(default="")
    postgres_user: str = field(default="")

    # Redis
    redis_host: str = field(default="")
    redis_port: int = field(default=6379)
    redis_db: int = field(default=0)

    # SpiceDB
    spicedb_host: str = field(default="")
    spicedb_port: int = field(default=50051)
    spicedb_token: str = field(default="")
    spicedb_insecure: bool = field(default=False)

    # Vault
    vault_addr: str = field(default="")
    vault_mount: str = field(default="secret")
    vault_path_prefix: str = field(default="")

    # Application
    debug: bool = field(default=False)
    allowed_hosts: str = field(default="*")
    log_level: str = field(default="INFO")

    # Kafka
    kafka_bootstrap_servers: str = field(default="")
    kafka_security_protocol: str = field(default="PLAINTEXT")
    kafka_sasl_mechanism: str = field(default="")
    kafka_sasl_username: str = field(default="")
    kafka_sasl_password: str = field(default="")
    publish_kafka_timeout_seconds: float = field(default=2.0)

    # Requeue store
    sa01_redis_url: str = field(default="")
    policy_requeue_prefix: str = field(default="policy:requeue")

    # Auth / Account lockout
    auth_max_attempts: int = field(default=5)
    auth_lockout_duration: int = field(default=900)
    auth_attempt_window: int = field(default=900)

    # Authorization
    sa01_authz_fail_open: bool = field(default=False)

    # Features
    sa01_feature_profile: str = field(default="enhanced")

    # Idempotency
    sa01_tenant_id: str = field(default="default")
    sa01_memory_namespace: str = field(default="wm")

    # Budget
    sa01_default_token_budget: int = field(default=4096)

    @property
    def postgres_dsn(self) -> str:
        """PostgreSQL connection string (password from Vault)."""
        return f"postgresql://{self.postgres_user}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @classmethod
    @abstractmethod
    def load(cls: Type[T]) -> T:
        """Load settings from environment. Must be implemented by subclasses."""
        ...


# ═══════════════════════════════════════════════════════════════════════════════
# STANDALONE Settings
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class StandaloneSettings(BaseSettings):
    """Settings for Agent-only Standalone deployment (Port 20xxx)."""

    # Standalone-specific: NO Brain/Memory
    somabrain_enabled: bool = field(default=False)
    fractalmemory_enabled: bool = field(default=False)

    @classmethod
    def load(cls) -> "StandaloneSettings":
        """Load Standalone settings from environment."""
        LOGGER.info("📦 Loading STANDALONE configuration...")

        return cls(
            deployment_mode="STANDALONE",
            deployment_target=get_optional_env("SA01_DEPLOYMENT_TARGET", "LOCAL"),
            # Database - fail-fast in prod
            postgres_host=get_required_env(
                "POSTGRES_HOST", allow_dev_default=True, dev_default="somaagent_postgres"
            ),
            postgres_port=int(get_optional_env("POSTGRES_PORT", "5432")),
            postgres_db=get_optional_env("POSTGRES_DB", "somaagent"),
            postgres_user=get_optional_env("POSTGRES_USER", "somaagent"),
            # Redis
            redis_host=get_required_env(
                "REDIS_HOST", allow_dev_default=True, dev_default="somaagent_redis"
            ),
            redis_port=int(get_optional_env("REDIS_PORT", "6379")),
            redis_db=int(get_optional_env("REDIS_DB", "0")),
            # SpiceDB
            spicedb_host=get_optional_env("SPICEDB_HOST", "localhost"),
            spicedb_port=int(get_optional_env("SPICEDB_PORT", "50051")),
            spicedb_token=get_optional_env("SPICEDB_TOKEN", ""),
            spicedb_insecure=get_optional_env("SPICEDB_INSECURE", "false").lower() == "true",
            # Vault
            vault_addr=get_required_env(
                "VAULT_ADDR", allow_dev_default=True, dev_default="http://somaagent_vault:8200"
            ),
            vault_mount=get_optional_env("VAULT_MOUNT", "secret"),
            vault_path_prefix=get_optional_env("VAULT_PATH_PREFIX", "somaagent"),
            # Application
            debug=get_optional_env("DJANGO_DEBUG", "false").lower() == "true",
            allowed_hosts=get_optional_env("ALLOWED_HOSTS", "*"),
            log_level=get_optional_env("LOG_LEVEL", "INFO"),
            # Kafka
            kafka_bootstrap_servers=get_optional_env("KAFKA_BOOTSTRAP_SERVERS", ""),
            kafka_security_protocol=get_optional_env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            kafka_sasl_mechanism=get_optional_env("KAFKA_SASL_MECHANISM", ""),
            kafka_sasl_username=get_optional_env("KAFKA_SASL_USERNAME", ""),
            kafka_sasl_password=get_optional_env("KAFKA_SASL_PASSWORD", ""),
            publish_kafka_timeout_seconds=float(
                get_optional_env("PUBLISH_KAFKA_TIMEOUT_SECONDS", "2.0")
            ),
            # Requeue store
            sa01_redis_url=get_optional_env("SA01_REDIS_URL", ""),
            policy_requeue_prefix=get_optional_env("POLICY_REQUEUE_PREFIX", "policy:requeue"),
            # Auth / Account lockout
            auth_max_attempts=int(get_optional_env("AUTH_MAX_ATTEMPTS", "5")),
            auth_lockout_duration=int(get_optional_env("AUTH_LOCKOUT_DURATION", "900")),
            auth_attempt_window=int(get_optional_env("AUTH_ATTEMPT_WINDOW", "900")),
            # Authorization
            sa01_authz_fail_open=get_optional_env("SA01_AUTHZ_FAIL_OPEN", "false").lower()
            in {"1", "true", "yes", "on"},
            # Features
            sa01_feature_profile=get_optional_env("SA01_FEATURE_PROFILE", "enhanced"),
            # Idempotency
            sa01_tenant_id=get_optional_env("SA01_TENANT_ID", "default"),
            sa01_memory_namespace=get_optional_env("SA01_MEMORY_NAMESPACE", "wm"),
            # Budget
            sa01_default_token_budget=int(get_optional_env("SA01_DEFAULT_TOKEN_BUDGET", "4096")),
            # Standalone-specific
            somabrain_enabled=False,
            fractalmemory_enabled=False,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AAAS Settings
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class AAASSettings(BaseSettings):
    """Settings for Unified Monolith AAAS deployment (Port 63xxx)."""

    # AAAS-specific: Brain + Memory enabled
    soma_aaas_mode: bool = field(default=True)
    somabrain_enabled: bool = field(default=True)
    fractalmemory_enabled: bool = field(default=True)

    # AAAS direct-mode for sub-millisecond latency
    aaas_direct_mode: bool = field(default=False)

    # Milvus (Vector DB - AAAS only)
    milvus_host: str = field(default="")
    milvus_port: int = field(default=19530)

    @classmethod
    def load(cls) -> "AAASSettings":
        """Load AAAS settings from environment."""
        LOGGER.info("☁️ Loading AAAS configuration...")

        aaas_mode_raw = get_optional_env("SOMA_AAAS_MODE", "true").lower()

        return cls(
            deployment_mode="AAAS",
            deployment_target=get_optional_env("SA01_DEPLOYMENT_TARGET", "LOCAL"),
            # Database - AAAS namespace
            postgres_host=get_required_env(
                "POSTGRES_HOST", allow_dev_default=True, dev_default="somastack_postgres"
            ),
            postgres_port=int(get_optional_env("POSTGRES_PORT", "5432")),
            postgres_db=get_optional_env("POSTGRES_DB", "soma"),
            postgres_user=get_optional_env("POSTGRES_USER", "soma"),
            # Redis
            redis_host=get_required_env(
                "REDIS_HOST", allow_dev_default=True, dev_default="somastack_redis"
            ),
            redis_port=int(get_optional_env("REDIS_PORT", "6379")),
            redis_db=int(get_optional_env("REDIS_DB", "0")),
            # SpiceDB
            spicedb_host=get_optional_env("SPICEDB_HOST", "localhost"),
            spicedb_port=int(get_optional_env("SPICEDB_PORT", "50051")),
            spicedb_token=get_optional_env("SPICEDB_TOKEN", ""),
            spicedb_insecure=get_optional_env("SPICEDB_INSECURE", "false").lower() == "true",
            # Vault
            vault_addr=get_required_env(
                "VAULT_ADDR", allow_dev_default=True, dev_default="http://somastack_vault:8200"
            ),
            vault_mount=get_optional_env("VAULT_MOUNT", "secret"),
            vault_path_prefix=get_optional_env("VAULT_PATH_PREFIX", "soma"),
            # Application
            debug=get_optional_env("DJANGO_DEBUG", "false").lower() == "true",
            allowed_hosts=get_optional_env("ALLOWED_HOSTS", "*"),
            log_level=get_optional_env("LOG_LEVEL", "INFO"),
            # AAAS-specific
            soma_aaas_mode=aaas_mode_raw in ("true", "direct"),
            aaas_direct_mode=aaas_mode_raw == "direct",
            somabrain_enabled=True,
            fractalmemory_enabled=True,
            # Milvus
            milvus_host=get_required_env(
                "MILVUS_HOST", allow_dev_default=True, dev_default="somastack_milvus"
            ),
            milvus_port=int(get_optional_env("MILVUS_PORT", "19530")),
            # Kafka
            kafka_bootstrap_servers=get_optional_env(
                "KAFKA_BOOTSTRAP_SERVERS", "somastack_kafka:9092"
            ),
            kafka_security_protocol=get_optional_env("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
            kafka_sasl_mechanism=get_optional_env("KAFKA_SASL_MECHANISM", ""),
            kafka_sasl_username=get_optional_env("KAFKA_SASL_USERNAME", ""),
            kafka_sasl_password=get_optional_env("KAFKA_SASL_PASSWORD", ""),
            publish_kafka_timeout_seconds=float(
                get_optional_env("PUBLISH_KAFKA_TIMEOUT_SECONDS", "2.0")
            ),
            # Requeue store
            sa01_redis_url=get_optional_env("SA01_REDIS_URL", ""),
            policy_requeue_prefix=get_optional_env("POLICY_REQUEUE_PREFIX", "policy:requeue"),
            # Auth / Account lockout
            auth_max_attempts=int(get_optional_env("AUTH_MAX_ATTEMPTS", "5")),
            auth_lockout_duration=int(get_optional_env("AUTH_LOCKOUT_DURATION", "900")),
            auth_attempt_window=int(get_optional_env("AUTH_ATTEMPT_WINDOW", "900")),
            # Authorization
            sa01_authz_fail_open=get_optional_env("SA01_AUTHZ_FAIL_OPEN", "false").lower()
            in {"1", "true", "yes", "on"},
            # Features
            sa01_feature_profile=get_optional_env("SA01_FEATURE_PROFILE", "enhanced"),
            # Idempotency
            sa01_tenant_id=get_optional_env("SA01_TENANT_ID", "default"),
            sa01_memory_namespace=get_optional_env("SA01_MEMORY_NAMESPACE", "wm"),
            # Budget
            sa01_default_token_budget=int(get_optional_env("SA01_DEFAULT_TOKEN_BUDGET", "4096")),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Settings Registry - THE SINGLE SOURCE OF TRUTH
# ═══════════════════════════════════════════════════════════════════════════════


class SettingsRegistry:
    """
    Centralized settings dispatcher based on deployment mode.

    VIBE Rule 100: This is the ONLY entry point for configuration.

    Usage:
        from config.settings_registry import SettingsRegistry
        settings = SettingsRegistry.load()
        print(settings.postgres_host)
    """

    _instance: Optional[BaseSettings] = None

    @classmethod
    def load(cls, force_reload: bool = False) -> BaseSettings:
        """
        Load settings based on SA01_DEPLOYMENT_MODE.

        Returns cached instance unless force_reload=True.
        """
        if cls._instance is not None and not force_reload:
            return cls._instance

        mode = os.environ.get("SA01_DEPLOYMENT_MODE", "STANDALONE").upper()

        LOGGER.info("🔧 SettingsRegistry: Loading configuration for mode=%s", mode)

        if mode == "STANDALONE":
            cls._instance = StandaloneSettings.load()
        elif mode in ("AAAS", "AAASMODE"):
            cls._instance = AAASSettings.load()
        elif mode == "DEV":
            # DEV mode defaults to Standalone for simplicity
            LOGGER.info("📋 DEV mode detected, using Standalone config")
            cls._instance = StandaloneSettings.load()
        elif mode == "PROD":
            # PROD mode requires explicit AAAS or STANDALONE
            aaas_mode = os.environ.get("SOMA_AAAS_MODE", "false").lower() == "true"
            if aaas_mode:
                cls._instance = AAASSettings.load()
            else:
                cls._instance = StandaloneSettings.load()
        else:
            raise RuntimeError(
                f"VIBE Rule 91 VIOLATION: Unknown SA01_DEPLOYMENT_MODE={mode}. "
                "Valid values: STANDALONE, AAAS, DEV, PROD"
            )

        LOGGER.info("✅ SettingsRegistry: Configuration loaded successfully")
        return cls._instance

    @classmethod
    def get(cls) -> BaseSettings:
        """Get cached settings or load if not initialized."""
        if cls._instance is None:
            return cls.load()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset cached settings (for testing)."""
        cls._instance = None


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level convenience
# ═══════════════════════════════════════════════════════════════════════════════


def get_settings() -> BaseSettings:
    """Convenience function to get current settings."""
    return SettingsRegistry.get()
