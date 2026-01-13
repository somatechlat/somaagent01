"""
SOMA SaaS Configuration
============================

Unified configuration for the saas deployment.
All settings from SomaBrain, FractalMemory, and Agent01 in one place.

VIBE Rule 91: Zero-Fallback Mandate - Production must fail-fast, no localhost defaults.
VIBE Rule 164: Zero-Hardcode Mandate - No hardcoded passwords in source.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

LOGGER = logging.getLogger(__name__)


def _get_required_host(env_var: str, dev_default: str) -> str:
    """Get host from environment, allowing localhost only in DEV mode.
    
    VIBE Rule 91: Zero-Fallback Mandate
    """
    value = os.getenv(env_var)
    if value:
        return value
    
    deployment_mode = os.getenv("SA01_DEPLOYMENT_MODE", "DEV").upper()
    if deployment_mode == "PROD":
        raise RuntimeError(
            f"{env_var} is required in PROD mode. "
            f"Set {env_var} in your environment. "
            "VIBE Rule 91: No localhost fallbacks in production."
        )
    
    # DEV mode allows localhost fallback with warning
    LOGGER.warning(
        "⚠️ Using localhost for %s in DEV mode. Set %s for production.",
        env_var, env_var
    )
    return dev_default


def _get_secret(env_var: str, dev_default: Optional[str] = None) -> str:
    """Get secret from environment with fail-fast in production.
    
    VIBE Rule 164: Zero-Hardcode Mandate - Secrets from Vault only.
    """
    value = os.getenv(env_var)
    if value:
        return value
    
    deployment_mode = os.getenv("SA01_DEPLOYMENT_MODE", "DEV").upper()
    if deployment_mode == "PROD":
        raise RuntimeError(
            f"{env_var} is required in PROD mode. "
            "Secrets must be provided via Vault or environment. "
            "VIBE Rule 164: No hardcoded secrets."
        )
    
    if dev_default is None:
        raise RuntimeError(f"{env_var} is required but not set.")
    
    LOGGER.warning(
        "⚠️ Using insecure default for %s in DEV mode. Set %s for production.",
        env_var, env_var
    )
    return dev_default


@dataclass
class SaaSConfig:
    """Unified configuration for SOMA SaaS."""

    # ==========================================================================
    # Mode Configuration
    # ==========================================================================
    saas_mode: bool = field(
        default_factory=lambda: os.getenv("SOMA_SAAS_MODE", "true").lower() == "true"
    )

    # ==========================================================================
    # External Services (mode-aware host resolution)
    # ==========================================================================
    milvus_host: str = field(
        default_factory=lambda: _get_required_host("MILVUS_HOST", "localhost")
    )
    milvus_port: int = field(default_factory=lambda: int(os.getenv("MILVUS_PORT", "19530")))

    redis_host: str = field(
        default_factory=lambda: _get_required_host("REDIS_HOST", "localhost")
    )
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))

    postgres_host: str = field(
        default_factory=lambda: _get_required_host("POSTGRES_HOST", "localhost")
    )
    postgres_port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    postgres_db: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "soma"))
    postgres_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "soma"))
    postgres_password: str = field(
        default_factory=lambda: _get_secret("POSTGRES_PASSWORD", "soma")
    )

    # ==========================================================================
    # SomaBrain Settings (now in-process)
    # ==========================================================================
    hrr_dim: int = field(default_factory=lambda: int(os.getenv("SOMABRAIN_HRR_DIM", "8192")))
    hrr_dtype: str = field(default_factory=lambda: os.getenv("SOMABRAIN_HRR_DTYPE", "float32"))
    global_seed: int = field(default_factory=lambda: int(os.getenv("SOMABRAIN_GLOBAL_SEED", "42")))
    bhdc_sparsity: float = field(
        default_factory=lambda: float(os.getenv("SOMABRAIN_BHDC_SPARSITY", "0.1"))
    )

    # ==========================================================================
    # FractalMemory Settings (now in-process)
    # ==========================================================================
    sfm_collection: str = field(default_factory=lambda: os.getenv("SFM_COLLECTION", "memories"))
    sfm_vector_dim: int = field(default_factory=lambda: int(os.getenv("SFM_VECTOR_DIM", "8192")))

    # ==========================================================================
    # Agent Settings
    # ==========================================================================
    agent_name: str = field(default_factory=lambda: os.getenv("AGENT_NAME", "SOMA Agent"))
    agent_port: int = field(default_factory=lambda: int(os.getenv("AGENT_PORT", "9000")))
    debug: bool = field(
        default_factory=lambda: os.getenv("DJANGO_DEBUG", "false").lower() == "true"
    )

    def __post_init__(self) -> None:
        """Validate configuration."""
        if self.hrr_dim <= 0:
            raise ValueError(f"hrr_dim must be positive, got {self.hrr_dim}")
        if not 0 < self.bhdc_sparsity <= 1:
            raise ValueError(f"bhdc_sparsity must be in (0,1], got {self.bhdc_sparsity}")

    @property
    def postgres_dsn(self) -> str:
        """PostgreSQL connection string."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/0"


# Global config instance
config = SaaSConfig()
