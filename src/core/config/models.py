"""Configuration Models for SomaAgent01.

VIBE CODING RULES COMPLIANT:
- NO SHIMS: Real Pydantic models with validation
- NO FALLBACKS: Strict validation only
- NO FAKE ANYTHING: Production-ready field validation
- NO LEGACY: Modern Pydantic patterns only
- NO BACKUPS: No duplicate model definitions
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import os


class DatabaseConfig(BaseModel):
    """Database configuration with validation."""
    
    dsn: str = Field(description="Database connection string")
    pool_size: int = Field(default=20, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=10, ge=0, le=50, description="Maximum overflow connections")
    pool_timeout: int = Field(default=30, ge=1, le=300, description="Pool timeout in seconds")
    
    @field_validator('dsn')
    @classmethod
    def validate_dsn(cls, v: str) -> str:
        """Validate database DSN format."""
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('DSN must start with postgresql:// or postgres://')
        return v


class KafkaConfig(BaseModel):
    """Kafka configuration with validation."""
    
    bootstrap_servers: str = Field(description="Kafka bootstrap servers")
    security_protocol: str = Field(default="PLAINTEXT", description="Security protocol")
    sasl_mechanism: Optional[str] = Field(default=None, description="SASL mechanism")
    sasl_username: Optional[str] = Field(default=None, description="SASL username")
    sasl_password: Optional[str] = Field(default=None, description="SASL password")
    
    @field_validator('bootstrap_servers')
    @classmethod
    def validate_bootstrap_servers(cls, v: str) -> str:
        """Validate bootstrap servers format."""
        if not v or not v.strip():
            raise ValueError('Bootstrap servers cannot be empty')
        return v.strip()


class RedisConfig(BaseModel):
    """Redis configuration with validation."""
    
    url: str = Field(description="Redis connection URL")
    max_connections: int = Field(default=20, ge=1, le=100, description="Maximum connections")
    retry_on_timeout: bool = Field(default=True, description="Retry on timeout")
    socket_timeout: int = Field(default=5, ge=1, le=60, description="Socket timeout in seconds")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate Redis URL format."""
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError('Redis URL must start with redis:// or rediss://')
        return v


class ServiceConfig(BaseModel):
    """Service configuration with validation."""
    
    name: str = Field(description="Service name")
    environment: str = Field(description="Environment (DEV, STAGING, PROD)")
    deployment_mode: str = Field(description="Deployment mode")
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(ge=1, le=65535, description="Service port")
    metrics_port: int = Field(ge=1, le=65535, description="Metrics port")
    log_level: str = Field(default="INFO", description="Log level")
    
    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = {'DEV', 'STAGING', 'PROD'}
        if v.upper() not in valid_envs:
            raise ValueError(f'Environment must be one of: {valid_envs}')
        return v.upper()
    
    @field_validator('deployment_mode')
    @classmethod
    def validate_deployment_mode(cls, v: str) -> str:
        """Validate deployment mode."""
        valid_modes = {'DEV', 'STAGING', 'PROD', 'LOCAL'}
        if v.upper() not in valid_modes:
            raise ValueError(f'Deployment mode must be one of: {valid_modes}')
        return v.upper()


class ExternalServiceConfig(BaseModel):
    """External service configuration with validation."""
    
    somabrain_base_url: str = Field(description="SomaBrain base URL")
    opa_url: str = Field(description="OPA service URL")
    otlp_endpoint: Optional[str] = Field(default=None, description="OTLP endpoint")
    
    @field_validator('somabrain_base_url')
    @classmethod
    def validate_somabrain_url(cls, v: str) -> str:
        """Validate SomaBrain URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('SomaBrain URL must start with http:// or https://')
        return v.rstrip('/')
    
    @field_validator('opa_url')
    @classmethod
    def validate_opa_url(cls, v: str) -> str:
        """Validate OPA URL."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('OPA URL must start with http:// or https://')
        return v.rstrip('/')


class AuthConfig(BaseModel):
    """Authentication configuration with validation."""
    
    auth_required: bool = Field(default=True, description="Whether authentication is required")
    jwt_secret: Optional[str] = Field(default=None, description="JWT secret key")
    jwt_public_key: Optional[str] = Field(default=None, description="JWT public key")
    jwt_jwks_url: Optional[str] = Field(default=None, description="JWKS URL")
    jwt_algorithms: list[str] = Field(default=["RS256"], description="JWT algorithms")
    jwt_audience: Optional[str] = Field(default=None, description="JWT audience")
    jwt_issuer: Optional[str] = Field(default=None, description="JWT issuer")
    jwt_leeway: int = Field(default=60, ge=0, description="JWT leeway in seconds")
    internal_token: Optional[str] = Field(default=None, description="Internal auth token")


class Config(BaseModel):
    """Main configuration model - single source of truth.
    
    VIBE CODING RULES COMPLIANT:
    - NO SHIMS: Real configuration with validation
    - NO FALLBACKS: Single source of truth only
    - NO FAKE ANYTHING: Production-ready settings
    - NO LEGACY: Modern Pydantic patterns
    - NO BACKUPS: No duplicate configuration
    """
    
    # Service configuration
    service: ServiceConfig = Field(description="Service configuration")
    
    # Infrastructure configuration
    database: DatabaseConfig = Field(description="Database configuration")
    kafka: KafkaConfig = Field(description="Kafka configuration")
    redis: RedisConfig = Field(description="Redis configuration")
    
    # External services
    external: ExternalServiceConfig = Field(description="External service configuration")
    
    # Authentication
    auth: AuthConfig = Field(description="Authentication configuration")
    
    # Feature flags
    feature_flags: Dict[str, bool] = Field(default_factory=dict, description="Feature flags")
    
    # Additional configuration
    extra: Dict[str, Any] = Field(default_factory=dict, description="Additional configuration")
    
    @model_validator(mode='after')
    def validate_config(self) -> Config:
        """Cross-field validation."""
        # Validate that required auth settings are present if auth is required
        if self.auth.auth_required:
            if not any([
                self.auth.jwt_secret,
                self.auth.jwt_public_key,
                self.auth.jwt_jwks_url
            ]):
                raise ValueError('At least one of jwt_secret, jwt_public_key, or jwt_jwks_url is required when auth_required=True')
        
        return self
    
    def get_somabrain_url(self) -> str:
        """Get SomaBrain URL with backward compatibility."""
        return self.external.somabrain_base_url
    
    def get_opa_url(self) -> str:
        """Get OPA URL with backward compatibility."""
        return self.external.opa_url
    
    def get_postgres_dsn(self) -> str:
        """Get PostgreSQL DSN with backward compatibility."""
        return self.database.dsn
    
    def get_kafka_bootstrap_servers(self) -> str:
        """Get Kafka bootstrap servers with backward compatibility."""
        return self.kafka.bootstrap_servers
    
    def get_redis_url(self) -> str:
        """Get Redis URL with backward compatibility."""
        return self.redis.url
    
    def is_auth_required(self) -> bool:
        """Check if authentication is required."""
        return self.auth.auth_required
    
    def get_deployment_mode(self) -> str:
        """Get deployment mode with backward compatibility."""
        return self.service.deployment_mode
    
    def get_environment(self) -> str:
        """Get environment with backward compatibility."""
        return self.service.environment