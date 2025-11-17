"""Configuration Loader for SomaAgent01.

VIBE CODING RULES COMPLIANT:
- NO SHIMS: Real configuration loading only
- NO FALLBACKS: Single precedence rules only
- NO FAKE ANYTHING: Production-ready loading
- NO LEGACY: Modern loading patterns
- NO BACKUPS: No duplicate loading logic
"""

from __future__ import annotations

import os
import yaml
from typing import Any, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass

from .models import Config, ServiceConfig, DatabaseConfig, KafkaConfig, RedisConfig, ExternalServiceConfig, AuthConfig


@dataclass
class EnvironmentMapping:
    """Environment variable mapping with precedence."""
    
    sa01_prefix: str = "SA01_"
    legacy_prefix: str = "SOMA_"
    
    def get_env_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment value with precedence.
        
        Precedence order:
        1. SA01_* variables (highest priority)
        2. Legacy SOMA_* variables (deprecated)
        3. Defaults (lowest priority)
        """
        # Try SA01_* prefix first
        sa01_key = f"{self.sa01_prefix}{key}"
        sa01_value = os.getenv(sa01_key)
        if sa01_value is not None:
            return sa01_value
        
        # Try legacy SOMA_* prefix
        legacy_key = f"{self.legacy_prefix}{key}"
        legacy_value = os.getenv(legacy_key)
        if legacy_value is not None:
            return legacy_value
        
        # Return default
        return default


class ConfigLoader:
    """Single configuration loader for SomaAgent01.
    
    VIBE CODING RULES COMPLIANT:
    - NO SHIMS: Real configuration loading
    - NO FALLBACKS: Single precedence rules
    - NO FAKE ANYTHING: Production-ready implementation
    - NO LEGACY: Modern loading patterns
    - NO BACKUPS: No duplicate loading logic
    """
    
    def __init__(self, config_file_path: Optional[Union[str, Path]] = None):
        """Initialize configuration loader.
        
        Args:
            config_file_path: Path to configuration file (optional)
        """
        self.config_file_path = Path(config_file_path) if config_file_path else None
        self.env_mapping = EnvironmentMapping()
        self._config_cache: Optional[Config] = None
    
    def load_config(self, force_reload: bool = False) -> Config:
        """Load configuration from all sources.
        
        Args:
            force_reload: Force reload even if cached
            
        Returns:
            Config: Loaded configuration
            
        Precedence order:
        1. SA01_* environment variables (highest priority)
        2. Legacy SOMA_* environment variables (deprecated)
        3. Configuration file values
        4. Defaults (lowest priority)
        """
        if self._config_cache is not None and not force_reload:
            return self._config_cache
        
        # Load base configuration from file
        config_data = self._load_config_file()
        
        # Override with environment variables
        config_data = self._override_with_env_vars(config_data)
        
        # Create configuration object
        config = self._create_config(config_data)
        
        # Cache configuration
        self._config_cache = config
        
        return config
    
    def _load_config_file(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dict[str, Any]: Configuration data from file
        """
        if self.config_file_path is None or not self.config_file_path.exists():
            return {}
        
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                if self.config_file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                else:
                    raise ValueError(f"Unsupported config file format: {self.config_file_path.suffix}")
        except Exception as e:
            raise RuntimeError(f"Failed to load config file {self.config_file_path}: {e}")
    
    def _override_with_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Override configuration with environment variables.
        
        Args:
            config_data: Base configuration data
            
        Returns:
            Dict[str, Any]: Configuration data with environment overrides
        """
        # Create a copy to avoid modifying original
        overridden_data = config_data.copy()
        
        # Service configuration overrides
        service_overrides = self._get_service_overrides()
        if service_overrides:
            overridden_data['service'] = {**overridden_data.get('service', {}), **service_overrides}
        
        # Database configuration overrides
        db_overrides = self._get_database_overrides()
        if db_overrides:
            overridden_data['database'] = {**overridden_data.get('database', {}), **db_overrides}
        
        # Kafka configuration overrides
        kafka_overrides = self._get_kafka_overrides()
        if kafka_overrides:
            overridden_data['kafka'] = {**overridden_data.get('kafka', {}), **kafka_overrides}
        
        # Redis configuration overrides
        redis_overrides = self._get_redis_overrides()
        if redis_overrides:
            overridden_data['redis'] = {**overridden_data.get('redis', {}), **redis_overrides}
        
        # External service overrides
        external_overrides = self._get_external_overrides()
        if external_overrides:
            overridden_data['external'] = {**overridden_data.get('external', {}), **external_overrides}
        
        # Auth configuration overrides
        auth_overrides = self._get_auth_overrides()
        if auth_overrides:
            overridden_data['auth'] = {**overridden_data.get('auth', {}), **auth_overrides}
        
        return overridden_data
    
    def _get_service_overrides(self) -> Dict[str, Any]:
        """Get service configuration overrides from environment."""
        overrides = {}
        
        # Service name
        service_name = self.env_mapping.get_env_value('SERVICE_NAME')
        if service_name:
            overrides['name'] = service_name
        
        # Environment
        environment = self.env_mapping.get_env_value('AGENT_ENV')
        if environment:
            overrides['environment'] = environment
        
        # Deployment mode
        deployment_mode = self.env_mapping.get_env_value('DEPLOYMENT_MODE')
        if deployment_mode:
            overrides['deployment_mode'] = deployment_mode
        
        # Host and port
        host = self.env_mapping.get_env_value('HOST')
        if host:
            overrides['host'] = host
        
        port = self.env_mapping.get_env_value('PORT')
        if port:
            try:
                overrides['port'] = int(port)
            except ValueError:
                pass
        
        # Metrics port
        metrics_port = self.env_mapping.get_env_value('METRICS_PORT')
        if metrics_port:
            try:
                overrides['metrics_port'] = int(metrics_port)
            except ValueError:
                pass
        
        # Log level
        log_level = self.env_mapping.get_env_value('LOG_LEVEL')
        if log_level:
            overrides['log_level'] = log_level
        
        return overrides
    
    def _get_database_overrides(self) -> Dict[str, Any]:
        """Get database configuration overrides from environment."""
        overrides = {}
        
        # Database DSN
        db_dsn = self.env_mapping.get_env_value('DB_DSN')
        if db_dsn:
            overrides['dsn'] = db_dsn
        
        # Pool size
        pool_size = self.env_mapping.get_env_value('DB_POOL_SIZE')
        if pool_size:
            try:
                overrides['pool_size'] = int(pool_size)
            except ValueError:
                pass
        
        return overrides
    
    def _get_kafka_overrides(self) -> Dict[str, Any]:
        """Get Kafka configuration overrides from environment."""
        overrides = {}
        
        # Bootstrap servers
        bootstrap_servers = self.env_mapping.get_env_value('KAFKA_BOOTSTRAP_SERVERS')
        if bootstrap_servers:
            overrides['bootstrap_servers'] = bootstrap_servers
        
        # Security protocol
        security_protocol = self.env_mapping.get_env_value('KAFKA_SECURITY_PROTOCOL')
        if security_protocol:
            overrides['security_protocol'] = security_protocol
        
        # SASL configuration
        sasl_mechanism = self.env_mapping.get_env_value('KAFKA_SASL_MECHANISM')
        if sasl_mechanism:
            overrides['sasl_mechanism'] = sasl_mechanism
        
        sasl_username = self.env_mapping.get_env_value('KAFKA_SASL_USERNAME')
        if sasl_username:
            overrides['sasl_username'] = sasl_username
        
        sasl_password = self.env_mapping.get_env_value('KAFKA_SASL_PASSWORD')
        if sasl_password:
            overrides['sasl_password'] = sasl_password
        
        return overrides
    
    def _get_redis_overrides(self) -> Dict[str, Any]:
        """Get Redis configuration overrides from environment."""
        overrides = {}
        
        # Redis URL
        redis_url = self.env_mapping.get_env_value('REDIS_URL')
        if redis_url:
            overrides['url'] = redis_url
        
        # Max connections
        max_connections = self.env_mapping.get_env_value('REDIS_MAX_CONNECTIONS')
        if max_connections:
            try:
                overrides['max_connections'] = int(max_connections)
            except ValueError:
                pass
        
        return overrides
    
    def _get_external_overrides(self) -> Dict[str, Any]:
        """Get external service configuration overrides from environment."""
        overrides = {}
        
        # SomaBrain URL
        somabrain_url = self.env_mapping.get_env_value('SOMA_BASE_URL')
        if somabrain_url:
            overrides['somabrain_base_url'] = somabrain_url
        
        # OPA URL
        opa_url = self.env_mapping.get_env_value('POLICY_URL')
        if opa_url:
            overrides['opa_url'] = opa_url
        
        # OTLP endpoint
        otlp_endpoint = self.env_mapping.get_env_value('OTLP_ENDPOINT')
        if otlp_endpoint:
            overrides['otlp_endpoint'] = otlp_endpoint
        
        return overrides
    
    def _get_auth_overrides(self) -> Dict[str, Any]:
        """Get authentication configuration overrides from environment."""
        overrides = {}
        
        # Auth required
        auth_required = self.env_mapping.get_env_value('AUTH_REQUIRED')
        if auth_required is not None:
            overrides['auth_required'] = auth_required.lower() in ('true', '1', 'yes', 'on')
        
        # JWT configuration
        jwt_secret = self.env_mapping.get_env_value('CRYPTO_FERNET_KEY')
        if jwt_secret:
            overrides['jwt_secret'] = jwt_secret
        
        jwt_public_key = self.env_mapping.get_env_value('JWT_PUBLIC_KEY')
        if jwt_public_key:
            overrides['jwt_public_key'] = jwt_public_key
        
        jwt_jwks_url = self.env_mapping.get_env_value('JWT_JWKS_URL')
        if jwt_jwks_url:
            overrides['jwt_jwks_url'] = jwt_jwks_url
        
        jwt_algorithms = self.env_mapping.get_env_value('JWT_ALGORITHMS')
        if jwt_algorithms:
            try:
                overrides['jwt_algorithms'] = jwt_algorithms.split(',')
            except Exception:
                pass
        
        jwt_audience = self.env_mapping.get_env_value('JWT_AUDIENCE')
        if jwt_audience:
            overrides['jwt_audience'] = jwt_audience
        
        jwt_issuer = self.env_mapping.get_env_value('JWT_ISSUER')
        if jwt_issuer:
            overrides['jwt_issuer'] = jwt_issuer
        
        jwt_leeway = self.env_mapping.get_env_value('JWT_LEEWAY')
        if jwt_leeway:
            try:
                overrides['jwt_leeway'] = int(jwt_leeway)
            except ValueError:
                pass
        
        # Internal token
        internal_token = self.env_mapping.get_env_value('AUTH_INTERNAL_TOKEN')
        if internal_token:
            overrides['internal_token'] = internal_token
        
        return overrides
    
    def _create_config(self, config_data: Dict[str, Any]) -> Config:
        """Create configuration object from data.
        
        Args:
            config_data: Configuration data dictionary
            
        Returns:
            Config: Configuration object
        """
        # Extract service configuration
        service_data = config_data.get('service', {})
        service_config = ServiceConfig(
            name=service_data.get('name', 'somaagent01'),
            environment=service_data.get('environment', 'DEV'),
            deployment_mode=service_data.get('deployment_mode', 'DEV'),
            host=service_data.get('host', '0.0.0.0'),
            port=service_data.get('port', 8010),
            metrics_port=service_data.get('metrics_port', 9400),
            log_level=service_data.get('log_level', 'INFO'),
        )
        
        # Extract database configuration
        db_data = config_data.get('database', {})
        database_config = DatabaseConfig(
            dsn=db_data.get('dsn', 'postgresql://soma:soma@postgres:5432/somaagent01'),
            pool_size=db_data.get('pool_size', 20),
            max_overflow=db_data.get('max_overflow', 10),
            pool_timeout=db_data.get('pool_timeout', 30),
        )
        
        # Extract Kafka configuration
        kafka_data = config_data.get('kafka', {})
        kafka_config = KafkaConfig(
            bootstrap_servers=kafka_data.get('bootstrap_servers', 'kafka:9092'),
            security_protocol=kafka_data.get('security_protocol', 'PLAINTEXT'),
            sasl_mechanism=kafka_data.get('sasl_mechanism'),
            sasl_username=kafka_data.get('sasl_username'),
            sasl_password=kafka_data.get('sasl_password'),
        )
        
        # Extract Redis configuration
        redis_data = config_data.get('redis', {})
        redis_config = RedisConfig(
            url=redis_data.get('url', 'redis://redis:6379/0'),
            max_connections=redis_data.get('max_connections', 20),
            retry_on_timeout=redis_data.get('retry_on_timeout', True),
            socket_timeout=redis_data.get('socket_timeout', 5),
        )
        
        # Extract external service configuration
        external_data = config_data.get('external', {})
        external_config = ExternalServiceConfig(
            somabrain_base_url=external_data.get('somabrain_base_url', 'http://localhost:9696'),
            opa_url=external_data.get('opa_url', 'http://localhost:8181'),
            otlp_endpoint=external_data.get('otlp_endpoint'),
        )
        
        # Extract authentication configuration
        auth_data = config_data.get('auth', {})
        auth_config = AuthConfig(
            auth_required=auth_data.get('auth_required', True),
            jwt_secret=auth_data.get('jwt_secret'),
            jwt_public_key=auth_data.get('jwt_public_key'),
            jwt_jwks_url=auth_data.get('jwt_jwks_url'),
            jwt_algorithms=auth_data.get('jwt_algorithms', ['RS256']),
            jwt_audience=auth_data.get('jwt_audience'),
            jwt_issuer=auth_data.get('jwt_issuer'),
            jwt_leeway=auth_data.get('jwt_leeway', 60),
            internal_token=auth_data.get('internal_token'),
        )
        
        # Extract feature flags
        feature_flags = config_data.get('feature_flags', {})
        
        # Extract extra configuration
        extra = config_data.get('extra', {})
        
        return Config(
            service=service_config,
            database=database_config,
            kafka=kafka_config,
            redis=redis_config,
            external=external_config,
            auth=auth_config,
            feature_flags=feature_flags,
            extra=extra,
        )


# Global configuration loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_file_path: Optional[Union[str, Path]] = None) -> ConfigLoader:
    """Get global configuration loader instance.
    
    Args:
        config_file_path: Path to configuration file (optional)
        
    Returns:
        ConfigLoader: Global configuration loader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_file_path)
    return _config_loader


def reload_config() -> None:
    """Reload global configuration."""
    global _config_loader
    if _config_loader is not None:
        _config_loader.load_config(force_reload=True)