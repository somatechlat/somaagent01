"""Centralised configuration models for Soma stack services."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentAwareSettings(BaseSettings):
    """Base settings object that injects environment-specific defaults."""

    environment: str = Field(default="DEV", description="Logical deployment environment")
    deployment_mode: str = Field(
        default="LOCAL", description="Runtime mode switch for feature flags"
    )
    model_profiles_path: str = Field(default="conf/model_profiles.yaml")
    extra: dict[str, Any] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
        # Prevent pydantic warnings where fields like 'model_profiles_path'
        # conflict with the 'model_' protected namespace. Adding a custom
        # protected namespace for settings avoids the warning and is safe.
        protected_namespaces=("settings_",),
    )

    @classmethod
    def default_environment(cls) -> str:
        return "DEV"

    @classmethod
    def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
        return {}

    @classmethod
    def _payload_for_environment(
        cls,
        environment: str,
        overrides: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        env_key = environment.upper()
        defaults = dict(cls.environment_defaults().get(env_key, {}))
        if not defaults:
            raise ValueError(f"Unknown environment '{environment}' for {cls.__name__}")
        payload: dict[str, Any] = {**defaults, **(overrides or {})}
        payload["environment"] = env_key
        if "deployment_mode" in payload:
            payload["deployment_mode"] = str(payload["deployment_mode"]).upper()
        extra_payload = dict(payload.get("extra", {}))
        if "metrics_host" in payload:
            extra_payload.setdefault("metrics_host", payload["metrics_host"])
        if "metrics_port" in payload:
            extra_payload.setdefault("metrics_port", payload["metrics_port"])
        payload["extra"] = extra_payload
        return payload

    @classmethod
    def for_environment(
        cls,
        environment: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> "EnvironmentAwareSettings":
        payload = cls._payload_for_environment(environment, overrides)
        return cls(**payload)

    @classmethod
    def from_env(
        cls,
        *,
        environment_var: str = "SOMA_AGENT_ENV",
        overrides: Mapping[str, Any] | None = None,
    ) -> "EnvironmentAwareSettings":
        env_value = os.getenv(environment_var)
        if not env_value:
            env_value = os.getenv("SA01_ENVIRONMENT", cls.default_environment())
        return cls.for_environment(env_value, overrides=overrides)

    def model_profiles(self) -> dict[str, Any]:
        path = Path(self.model_profiles_path)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def environment_profile(self) -> dict[str, Any]:
        profiles = self.model_profiles()
        return profiles.get(self.deployment_mode.upper(), {})


_SHARED_DEFAULTS: dict[str, Any] = {
    "deployment_mode": "LOCAL",
    "postgres_dsn": "postgresql://soma:soma@postgres.soma.svc.cluster.local:5432/somaagent01",
    "kafka_bootstrap_servers": "kafka.soma.svc.cluster.local:9092",
    "redis_url": "redis://redis.soma.svc.cluster.local:6379/0",
    "otlp_endpoint": "http://jaeger-collector.soma.svc.cluster.local:4317",
    "auth_url": "http://auth.soma.svc.cluster.local:8080",
    "opa_url": "http://opa.soma.svc.cluster.local:8181",
    "vault_addr": "http://vault.soma.svc.cluster.local:8200",
    "feature_flag_endpoint": "etcd.soma.svc.cluster.local:2379",
    "metrics_host": "0.0.0.0",
    "metrics_port": 9301,
    "extra": {
        "metrics_host": "0.0.0.0",
        "metrics_port": 9301,
    },
}

_SA01_ENVIRONMENT_DEFAULTS: dict[str, dict[str, Any]] = {
    "DEV": {
        **_SHARED_DEFAULTS,
        "deployment_mode": "DEV",
    },
    "TEST": {
        **_SHARED_DEFAULTS,
        "deployment_mode": "TEST",
    },
    "STAGING": {
        **_SHARED_DEFAULTS,
        "deployment_mode": "STAGING",
    },
    "PROD": {
        **_SHARED_DEFAULTS,
        "deployment_mode": "PROD",
    },
}


class SA01Settings(EnvironmentAwareSettings):
    """Settings object for the SomaAgent01 service."""

    service_name: str = Field(default="sa01")
    # Read from SA01_* first, then fall back to unprefixed env vars used by docker-compose.dev.yaml
    postgres_dsn: str = Field(
        default=_SHARED_DEFAULTS["postgres_dsn"],
        validation_alias=AliasChoices("SA01_POSTGRES_DSN", "POSTGRES_DSN"),
    )
    kafka_bootstrap_servers: str = Field(
        default=_SHARED_DEFAULTS["kafka_bootstrap_servers"],
        validation_alias=AliasChoices("SA01_KAFKA_BOOTSTRAP_SERVERS", "KAFKA_BOOTSTRAP_SERVERS"),
    )
    redis_url: str = Field(
        default=_SHARED_DEFAULTS["redis_url"],
        validation_alias=AliasChoices("SA01_REDIS_URL", "REDIS_URL"),
    )
    otlp_endpoint: str = Field(default=_SHARED_DEFAULTS["otlp_endpoint"])
    auth_url: str = Field(default=_SHARED_DEFAULTS["auth_url"])
    opa_url: str = Field(default=_SHARED_DEFAULTS["opa_url"])
    vault_addr: str = Field(default=_SHARED_DEFAULTS["vault_addr"])
    feature_flag_endpoint: str = Field(default=_SHARED_DEFAULTS["feature_flag_endpoint"])
    metrics_host: str = Field(default=_SHARED_DEFAULTS["metrics_host"])
    metrics_port: int = Field(default=_SHARED_DEFAULTS["metrics_port"])

    model_config = SettingsConfigDict(
        env_prefix="SA01_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
        # Avoid protected namespace conflicts reported by pydantic for
        # fields that begin with 'model_'. This aligns with the warning
        # remediation suggestion and prevents noisy logs.
        protected_namespaces=("settings_",),
    )

    @classmethod
    def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
        return _SA01_ENVIRONMENT_DEFAULTS


@lru_cache(maxsize=4)
def get_sa01_settings(environment: str | None = None) -> SA01Settings:
    """Memoized accessor used by services to avoid repeated disk I/O."""

    if environment:
        return SA01Settings.for_environment(environment)
    return SA01Settings.from_env()
