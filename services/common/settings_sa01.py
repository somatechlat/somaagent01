"""Service settings for SomaAgent 01 (self-contained).

This replaces the old shim that imported from a non-existent ``common`` package.
It provides a minimal, robust SA01Settings based on ``BaseServiceSettings`` with
DEV defaults aligned to docker-compose host port mappings so the gateway and
workers can run locally against the running infra.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from services.common import runtime_config as cfg
from services.common.settings_base import BaseServiceSettings


@dataclass(slots=True)
class SA01Settings(BaseServiceSettings):
    """Concrete settings for SomaAgent 01 services.

    Extends BaseServiceSettings with a few service-wide knobs used across
    multiple processes. Environment variables at runtime can still override
    specific connection strings; these defaults are primarily for local DEV.
    """

    # Extra service-wide fields consumed by various services
    metrics_port: int = 9400
    metrics_host: str = "0.0.0.0"
    opa_url: str = "http://localhost:8181"

    # Canonical authentication / security / crypto configuration
    auth_required: bool = False
    jwt_secret: str | None = None
    jwt_public_key: str | None = None
    jwt_jwks_url: str | None = None
    jwt_algorithms: list[str] = None  # populated from env (comma separated)
    jwt_audience: str | None = None
    jwt_issuer: str | None = None
    jwt_leeway: int = 10
    jwt_tenant_claims: list[str] = None
    jwt_ttl_seconds: int = 3600

    # Canonical cookie configuration
    jwt_cookie_name: str = "jwt"
    jwt_cookie_domain: str | None = None
    jwt_cookie_path: str = "/"
    jwt_cookie_samesite: str = "Lax"
    jwt_cookie_http_only: bool = True
    jwt_cookie_max_age: int | None = None

    # Internal token for service to gateway authentication
    internal_token: str | None = None

    # Encryption key for credential storage (Fernet urlsafe base64 32 bytes)
    crypto_fernet_key: str | None = None

    # Upload configuration
    upload_dir: str | None = None
    upload_max_mb: int = 25
    upload_max_files: int = 10
    upload_allowed_mime: list[str] | None = None
    upload_denied_mime: list[str] | None = None

    # CORS configuration
    cors_origins: list[str] | None = None
    cors_methods: list[str] | None = None
    cors_headers: list[str] | None = None
    cors_expose_headers: list[str] | None = None
    cors_credentials: bool = False

    # Gateway public surface
    gateway_port: int = 21016
    gateway_base_url: str | None = None

    # Admin/API rate limiting (simple in-process limiter)
    admin_rps: float = 0.0
    admin_burst: int = 10

    # Somabrain integration
    soma_base_url: str | None = None
    soma_tenant_id: str | None = None
    soma_namespace: str | None = None
    soma_memory_namespace: str | None = None

    # Vault (optional secret sourcing)
    jwt_vault_path: str | None = None
    jwt_vault_mount: str | None = None
    jwt_vault_secret_key: str | None = None

    def __post_init__(self) -> None:  # type: ignore[override]
        BaseServiceSettings.__post_init__(self)
        # Normalize algorithms / tenant claims lists if provided as strings
        if isinstance(self.jwt_algorithms, str):
            self.jwt_algorithms = [a.strip() for a in self.jwt_algorithms.split(",") if a.strip()]
        if self.jwt_algorithms is None:
            self.jwt_algorithms = ["HS256", "RS256"]
        if isinstance(self.jwt_tenant_claims, str):
            self.jwt_tenant_claims = [
                c.strip() for c in self.jwt_tenant_claims.split(",") if c.strip()
            ]
        if self.jwt_tenant_claims is None:
            self.jwt_tenant_claims = ["tenant", "org", "customer"]

        # Fail-closed: if auth_required is true we need signing material (secret OR public key OR JWKS)
        if self.auth_required:
            if not (self.jwt_secret or self.jwt_public_key or self.jwt_jwks_url):
                raise ValueError(
                    "Auth required but no JWT signing material present (SA01_AUTH_JWT_SECRET, SA01_AUTH_JWT_PUBLIC_KEY, or SA01_AUTH_JWKS_URL)."
                )
        # Fail-closed: encryption key must be present if any credentials subsystem depends on it
        if self.crypto_fernet_key is None:
            # We do not auto-generate – strict posture
            raise ValueError(
                "Missing SA01_CRYPTO_FERNET_KEY; credential encryption disabled and startup aborted."
            )
        # Basic validation for Fernet key length (urlsafe base64 44 chars for 32 bytes)
        if self.crypto_fernet_key and len(self.crypto_fernet_key.strip()) < 32:
            raise ValueError("Invalid SA01_CRYPTO_FERNET_KEY; appears too short.")
        # Upload lists normalization
        if isinstance(self.upload_allowed_mime, str):
            self.upload_allowed_mime = [
                m.strip() for m in self.upload_allowed_mime.split(",") if m.strip()
            ]
        if isinstance(self.upload_denied_mime, str):
            self.upload_denied_mime = [
                m.strip() for m in self.upload_denied_mime.split(",") if m.strip()
            ]
        # CORS list normalization
        if isinstance(self.cors_origins, str):
            self.cors_origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if isinstance(self.cors_methods, str):
            self.cors_methods = [m.strip() for m in self.cors_methods.split(",") if m.strip()]
        if isinstance(self.cors_headers, str):
            self.cors_headers = [h.strip() for h in self.cors_headers.split(",") if h.strip()]
        if isinstance(self.cors_expose_headers, str):
            self.cors_expose_headers = [
                h.strip() for h in self.cors_expose_headers.split(",") if h.strip()
            ]
        # Gateway base URL fallback
        if not self.gateway_base_url:
            self.gateway_base_url = f"http://localhost:{self.gateway_port}"
        # Somabrain defaults
        if not self.soma_base_url:
            self.soma_base_url = "http://localhost:9696"

    @classmethod
    def default_environment(cls) -> str:
        # Canonical selector: use SA01_ENV only (DEV default)
        return cfg.env("SA01_ENV", "DEV").upper()

    @classmethod
    def from_env(
        cls,
        *,
        environment_var: str = "SA01_ENV",
        overrides: Mapping[str, Any] | None = None,
    ) -> "SA01Settings":
        # Force canonical environment variable for environment selection
        return super(SA01Settings, cls).from_env(
            environment_var=environment_var, overrides=overrides
        )

    @classmethod
    def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
        """Return sane defaults per environment.

        - DEV defaults target docker-compose forwarded host ports so a locally
          running gateway can connect to the infra containers.
        - STAGING/PROD provide placeholders that should be overridden via env.
        """
        dev_defaults = {
            # BaseServiceSettings required fields
            # Map local developer environment to the canonical LOCAL profile set
            "deployment_mode": "LOCAL",
            # Compose maps host ports: kafka 20000->9092, redis 20001->6379, pg 20002->5432, opa 20009->8181
            "postgres_dsn": cfg.env(
                "SA01_DB_DSN", "postgresql://soma:soma@localhost:20002/somaagent01"
            ),
            "kafka_bootstrap_servers": cfg.env("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:20000"),
            "redis_url": cfg.env("SA01_REDIS_URL", "redis://localhost:20001/0"),
            "otlp_endpoint": cfg.env("SA01_OTLP_ENDPOINT", ""),
            "model_profiles_path": cfg.env("SA01_MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
            "extra": {},
            # Extended fields
            "metrics_port": int(cfg.env("SA01_METRICS_PORT", "9400")),
            "metrics_host": cfg.env("SA01_METRICS_HOST", "0.0.0.0"),
            "opa_url": cfg.env("SA01_POLICY_URL", "http://localhost:20009"),
            # Auth / security
            "auth_required": (cfg.env("SA01_AUTH_REQUIRED", "false") or "false").lower()
            in {"true", "1", "yes"},
            "jwt_secret": cfg.env("SA01_AUTH_JWT_SECRET"),
            "jwt_public_key": cfg.env("SA01_AUTH_JWT_PUBLIC_KEY"),
            "jwt_jwks_url": cfg.env("SA01_AUTH_JWKS_URL"),
            "jwt_algorithms": cfg.env("SA01_AUTH_JWT_ALGORITHMS", "HS256,RS256"),
            "jwt_audience": cfg.env("SA01_AUTH_JWT_AUDIENCE"),
            "jwt_issuer": cfg.env("SA01_AUTH_JWT_ISSUER"),
            "jwt_leeway": int(cfg.env("SA01_AUTH_JWT_LEEWAY", "10") or "10"),
            "jwt_tenant_claims": cfg.env("SA01_AUTH_JWT_TENANT_CLAIMS", "tenant,org,customer"),
            "jwt_ttl_seconds": int(cfg.env("SA01_AUTH_JWT_TTL_SECONDS", "3600") or "3600"),
            "jwt_cookie_name": cfg.env("SA01_AUTH_JWT_COOKIE_NAME", "jwt"),
            "jwt_cookie_domain": cfg.env("SA01_AUTH_JWT_COOKIE_DOMAIN"),
            "jwt_cookie_path": cfg.env("SA01_AUTH_JWT_COOKIE_PATH", "/"),
            "jwt_cookie_samesite": cfg.env("SA01_AUTH_JWT_COOKIE_SAMESITE", "Lax"),
            "jwt_cookie_http_only": (
                cfg.env("SA01_AUTH_JWT_COOKIE_HTTPONLY", "true") or "true"
            ).lower()
            in {"true", "1", "yes"},
            "jwt_cookie_max_age": (
                int(cfg.env("SA01_AUTH_JWT_COOKIE_MAX_AGE", "0") or "0") or None
            ),
            "internal_token": cfg.env("SA01_AUTH_INTERNAL_TOKEN"),
            "crypto_fernet_key": cfg.env("SA01_CRYPTO_FERNET_KEY"),
            # Uploads
            "upload_dir": cfg.env("SA01_UPLOAD_DIR", "/git/agent-zero/tmp/uploads"),
            "upload_max_mb": int(cfg.env("SA01_UPLOAD_MAX_MB", "25") or "25"),
            "upload_max_files": int(cfg.env("SA01_UPLOAD_MAX_FILES", "10") or "10"),
            "upload_allowed_mime": cfg.env("SA01_UPLOAD_ALLOWED_MIME", ""),
            "upload_denied_mime": cfg.env("SA01_UPLOAD_DENIED_MIME", ""),
            # CORS
            "cors_origins": cfg.env("SA01_CORS_ORIGINS", ""),
            "cors_methods": cfg.env("SA01_CORS_METHODS", ""),
            "cors_headers": cfg.env("SA01_CORS_HEADERS", ""),
            "cors_expose_headers": cfg.env("SA01_CORS_EXPOSE_HEADERS", ""),
            "cors_credentials": (cfg.env("SA01_CORS_CREDENTIALS", "false") or "false").lower()
            in {"true", "1", "yes", "on"},
            # Gateway surface
            "gateway_port": int(cfg.env("SA01_GATEWAY_PORT", "21016") or "21016"),
            "gateway_base_url": cfg.env("SA01_GATEWAY_BASE_URL"),
            # Admin limiter
            "admin_rps": float(cfg.env("SA01_ADMIN_RPS", "0") or "0"),
            "admin_burst": int(cfg.env("SA01_ADMIN_BURST", "10") or "10"),
            # Somabrain integration
            "soma_base_url": cfg.env("SA01_SOMA_BASE_URL"),
            "soma_tenant_id": cfg.env("SA01_SOMA_TENANT_ID"),
            "soma_namespace": cfg.env("SA01_SOMA_NAMESPACE"),
            "soma_memory_namespace": cfg.env("SA01_SOMA_MEMORY_NAMESPACE"),
            # Vault (optional)
            "jwt_vault_path": cfg.env("SA01_AUTH_JWT_VAULT_PATH"),
            "jwt_vault_mount": cfg.env("SA01_AUTH_JWT_VAULT_MOUNT"),
            "jwt_vault_secret_key": cfg.env("SA01_AUTH_JWT_VAULT_SECRET_KEY"),
        }

        # Placeholders for non-DEV; expect env to provide concrete values
        staging_defaults = {
            # Treat STAGING as production-like for profile selection
            "deployment_mode": "PROD",
            "postgres_dsn": cfg.env(
                "SA01_DB_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"
            ),
            "kafka_bootstrap_servers": cfg.env("SA01_KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "redis_url": cfg.env("SA01_REDIS_URL", "redis://redis:6379/0"),
            "otlp_endpoint": cfg.env("SA01_OTLP_ENDPOINT", ""),
            "model_profiles_path": cfg.env("SA01_MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
            "extra": {},
            "metrics_port": int(cfg.env("SA01_METRICS_PORT", "9400")),
            "metrics_host": cfg.env("SA01_METRICS_HOST", "0.0.0.0"),
            "opa_url": cfg.env("SA01_POLICY_URL", "http://opa:8181"),
            "auth_required": (cfg.env("SA01_AUTH_REQUIRED", "true") or "true").lower()
            in {"true", "1", "yes"},
            "jwt_secret": cfg.env("SA01_AUTH_JWT_SECRET"),
            "jwt_public_key": cfg.env("SA01_AUTH_JWT_PUBLIC_KEY"),
            "jwt_jwks_url": cfg.env("SA01_AUTH_JWKS_URL"),
            "jwt_algorithms": cfg.env("SA01_AUTH_JWT_ALGORITHMS", "HS256,RS256"),
            "jwt_audience": cfg.env("SA01_AUTH_JWT_AUDIENCE"),
            "jwt_issuer": cfg.env("SA01_AUTH_JWT_ISSUER"),
            "jwt_leeway": int(cfg.env("SA01_AUTH_JWT_LEEWAY", "10") or "10"),
            "jwt_tenant_claims": cfg.env("SA01_AUTH_JWT_TENANT_CLAIMS", "tenant,org,customer"),
            "jwt_ttl_seconds": int(cfg.env("SA01_AUTH_JWT_TTL_SECONDS", "3600") or "3600"),
            "jwt_cookie_name": cfg.env("SA01_AUTH_JWT_COOKIE_NAME", "jwt"),
            "jwt_cookie_domain": cfg.env("SA01_AUTH_JWT_COOKIE_DOMAIN"),
            "jwt_cookie_path": cfg.env("SA01_AUTH_JWT_COOKIE_PATH", "/"),
            "jwt_cookie_samesite": cfg.env("SA01_AUTH_JWT_COOKIE_SAMESITE", "Lax"),
            "jwt_cookie_http_only": (
                cfg.env("SA01_AUTH_JWT_COOKIE_HTTPONLY", "true") or "true"
            ).lower()
            in {"true", "1", "yes"},
            "jwt_cookie_max_age": (
                int(cfg.env("SA01_AUTH_JWT_COOKIE_MAX_AGE", "0") or "0") or None
            ),
            "internal_token": cfg.env("SA01_AUTH_INTERNAL_TOKEN"),
            "crypto_fernet_key": cfg.env("SA01_CRYPTO_FERNET_KEY"),
            "upload_dir": cfg.env("SA01_UPLOAD_DIR", "/uploads"),
            "upload_max_mb": int(cfg.env("SA01_UPLOAD_MAX_MB", "25") or "25"),
            "upload_max_files": int(cfg.env("SA01_UPLOAD_MAX_FILES", "10") or "10"),
            "upload_allowed_mime": cfg.env("SA01_UPLOAD_ALLOWED_MIME", ""),
            "upload_denied_mime": cfg.env("SA01_UPLOAD_DENIED_MIME", ""),
            "cors_origins": cfg.env("SA01_CORS_ORIGINS", ""),
            "cors_methods": cfg.env("SA01_CORS_METHODS", ""),
            "cors_headers": cfg.env("SA01_CORS_HEADERS", ""),
            "cors_expose_headers": cfg.env("SA01_CORS_EXPOSE_HEADERS", ""),
            "cors_credentials": (cfg.env("SA01_CORS_CREDENTIALS", "false") or "false").lower()
            in {"true", "1", "yes", "on"},
            "gateway_port": int(cfg.env("SA01_GATEWAY_PORT", "21016") or "21016"),
            "gateway_base_url": cfg.env("SA01_GATEWAY_BASE_URL"),
            "admin_rps": float(cfg.env("SA01_ADMIN_RPS", "0") or "0"),
            "admin_burst": int(cfg.env("SA01_ADMIN_BURST", "10") or "10"),
            "soma_base_url": cfg.env("SA01_SOMA_BASE_URL"),
            "soma_tenant_id": cfg.env("SA01_SOMA_TENANT_ID"),
            "soma_namespace": cfg.env("SA01_SOMA_NAMESPACE"),
            "soma_memory_namespace": cfg.env("SA01_SOMA_MEMORY_NAMESPACE"),
            "jwt_vault_path": cfg.env("SA01_AUTH_JWT_VAULT_PATH"),
            "jwt_vault_mount": cfg.env("SA01_AUTH_JWT_VAULT_MOUNT"),
            "jwt_vault_secret_key": cfg.env("SA01_AUTH_JWT_VAULT_SECRET_KEY"),
        }

        prod_defaults = {
            "deployment_mode": "PROD",
            "postgres_dsn": cfg.env(
                "SA01_DB_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"
            ),
            "kafka_bootstrap_servers": cfg.env("SA01_KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "redis_url": cfg.env("SA01_REDIS_URL", "redis://redis:6379/0"),
            "otlp_endpoint": cfg.env("SA01_OTLP_ENDPOINT", ""),
            "model_profiles_path": cfg.env("SA01_MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
            "extra": {},
            "metrics_port": int(cfg.env("SA01_METRICS_PORT", "9400")),
            "metrics_host": cfg.env("SA01_METRICS_HOST", "0.0.0.0"),
            "opa_url": cfg.env("SA01_POLICY_URL", "http://opa:8181"),
            "auth_required": (cfg.env("SA01_AUTH_REQUIRED", "true") or "true").lower()
            in {"true", "1", "yes"},
            "jwt_secret": cfg.env("SA01_AUTH_JWT_SECRET"),
            "jwt_public_key": cfg.env("SA01_AUTH_JWT_PUBLIC_KEY"),
            "jwt_jwks_url": cfg.env("SA01_AUTH_JWKS_URL"),
            "jwt_algorithms": cfg.env("SA01_AUTH_JWT_ALGORITHMS", "HS256,RS256"),
            "jwt_audience": cfg.env("SA01_AUTH_JWT_AUDIENCE"),
            "jwt_issuer": cfg.env("SA01_AUTH_JWT_ISSUER"),
            "jwt_leeway": int(cfg.env("SA01_AUTH_JWT_LEEWAY", "10") or "10"),
            "jwt_tenant_claims": cfg.env("SA01_AUTH_JWT_TENANT_CLAIMS", "tenant,org,customer"),
            "jwt_ttl_seconds": int(cfg.env("SA01_AUTH_JWT_TTL_SECONDS", "3600") or "3600"),
            "jwt_cookie_name": cfg.env("SA01_AUTH_JWT_COOKIE_NAME", "jwt"),
            "jwt_cookie_domain": cfg.env("SA01_AUTH_JWT_COOKIE_DOMAIN"),
            "jwt_cookie_path": cfg.env("SA01_AUTH_JWT_COOKIE_PATH", "/"),
            "jwt_cookie_samesite": cfg.env("SA01_AUTH_JWT_COOKIE_SAMESITE", "Lax"),
            "jwt_cookie_http_only": (
                cfg.env("SA01_AUTH_JWT_COOKIE_HTTPONLY", "true") or "true"
            ).lower()
            in {"true", "1", "yes"},
            "jwt_cookie_max_age": (
                int(cfg.env("SA01_AUTH_JWT_COOKIE_MAX_AGE", "0") or "0") or None
            ),
            "internal_token": cfg.env("SA01_AUTH_INTERNAL_TOKEN"),
            "crypto_fernet_key": cfg.env("SA01_CRYPTO_FERNET_KEY"),
            "upload_dir": cfg.env("SA01_UPLOAD_DIR", "/uploads"),
            "upload_max_mb": int(cfg.env("SA01_UPLOAD_MAX_MB", "25") or "25"),
            "upload_max_files": int(cfg.env("SA01_UPLOAD_MAX_FILES", "10") or "10"),
            "upload_allowed_mime": cfg.env("SA01_UPLOAD_ALLOWED_MIME", ""),
            "upload_denied_mime": cfg.env("SA01_UPLOAD_DENIED_MIME", ""),
            "cors_origins": cfg.env("SA01_CORS_ORIGINS", ""),
            "cors_methods": cfg.env("SA01_CORS_METHODS", ""),
            "cors_headers": cfg.env("SA01_CORS_HEADERS", ""),
            "cors_expose_headers": cfg.env("SA01_CORS_EXPOSE_HEADERS", ""),
            "cors_credentials": (cfg.env("SA01_CORS_CREDENTIALS", "false") or "false").lower()
            in {"true", "1", "yes", "on"},
            "gateway_port": int(cfg.env("SA01_GATEWAY_PORT", "21016") or "21016"),
            "gateway_base_url": cfg.env("SA01_GATEWAY_BASE_URL"),
            "admin_rps": float(cfg.env("SA01_ADMIN_RPS", "0") or "0"),
            "admin_burst": int(cfg.env("SA01_ADMIN_BURST", "10") or "10"),
            "soma_base_url": cfg.env("SA01_SOMA_BASE_URL"),
            "soma_tenant_id": cfg.env("SA01_SOMA_TENANT_ID"),
            "soma_namespace": cfg.env("SA01_SOMA_NAMESPACE"),
            "soma_memory_namespace": cfg.env("SA01_SOMA_MEMORY_NAMESPACE"),
            "jwt_vault_path": cfg.env("SA01_AUTH_JWT_VAULT_PATH"),
            "jwt_vault_mount": cfg.env("SA01_AUTH_JWT_VAULT_MOUNT"),
            "jwt_vault_secret_key": cfg.env("SA01_AUTH_JWT_VAULT_SECRET_KEY"),
        }

        return {
            "DEV": dev_defaults,
            "STAGING": staging_defaults,
            "PROD": prod_defaults,
        }
