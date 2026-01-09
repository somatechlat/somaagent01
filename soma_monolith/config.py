"""
SOMA Monolith Configuration
============================

Unified configuration for the monolith deployment.
All settings from SomaBrain, FractalMemory, and Agent01 in one place.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MonolithConfig:
    """Unified configuration for SOMA Monolith."""
    
    # ==========================================================================
    # Mode Configuration
    # ==========================================================================
    monolith_mode: bool = field(
        default_factory=lambda: os.getenv("SOMA_MONOLITH_MODE", "true").lower() == "true"
    )
    
    # ==========================================================================
    # External Services (still require network)
    # ==========================================================================
    milvus_host: str = field(default_factory=lambda: os.getenv("MILVUS_HOST", "localhost"))
    milvus_port: int = field(default_factory=lambda: int(os.getenv("MILVUS_PORT", "19530")))
    
    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    
    postgres_host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    postgres_port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    postgres_db: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "soma"))
    postgres_user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "soma"))
    postgres_password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "soma"))
    
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
    debug: bool = field(default_factory=lambda: os.getenv("DJANGO_DEBUG", "false").lower() == "true")
    
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
config = MonolithConfig()
