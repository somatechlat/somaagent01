"""Service settings for SomaAgent 01 (self-contained).

This replaces the old shim that imported from a non-existent ``common`` package.
It provides a minimal, robust SA01Settings based on ``BaseServiceSettings`` with
DEV defaults aligned to docker-compose host port mappings so the gateway and
workers can run locally against the running infra.
"""

from __future__ import annotations

import os
from services.common import runtime_config as cfg
from dataclasses import dataclass
from typing import Any, Mapping

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

    @classmethod
    def default_environment(cls) -> str:
        # Canonical selector: use SOMA_AGENT_ENV only (DEV default)
        return cfg.env("SOMA_AGENT_ENV", "DEV").upper()

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
                "SA01_POSTGRES_DSN", "postgresql://soma:soma@localhost:20002/somaagent01"
            ),
            "kafka_bootstrap_servers": cfg.env("KAFKA_BOOTSTRAP_SERVERS", "localhost:20000"),
            "redis_url": cfg.env("REDIS_URL", "redis://localhost:20001/0"),
            "otlp_endpoint": cfg.env("OTLP_ENDPOINT", ""),
            "model_profiles_path": cfg.env("MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
            "extra": {},
            # Extended fields
            "metrics_port": int(cfg.env("GATEWAY_METRICS_PORT", "9400")),
            "metrics_host": cfg.env("GATEWAY_METRICS_HOST", "0.0.0.0"),
            "opa_url": cfg.env("OPA_URL", "http://localhost:20009"),
        }

        # Placeholders for non-DEV; expect env to provide concrete values
        staging_defaults = {
            # Treat STAGING as production-like for profile selection
            "deployment_mode": "PROD",
            "postgres_dsn": cfg.env(
                "SA01_POSTGRES_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"
            ),
            "kafka_bootstrap_servers": cfg.env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "redis_url": cfg.env("REDIS_URL", "redis://redis:6379/0"),
            "otlp_endpoint": cfg.env("OTLP_ENDPOINT", ""),
            "model_profiles_path": cfg.env("MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
            "extra": {},
            "metrics_port": int(cfg.env("GATEWAY_METRICS_PORT", "9400")),
            "metrics_host": cfg.env("GATEWAY_METRICS_HOST", "0.0.0.0"),
            "opa_url": cfg.env("OPA_URL", "http://opa:8181"),
        }

        prod_defaults = {
            "deployment_mode": "PROD",
            "postgres_dsn": cfg.env(
                "SA01_POSTGRES_DSN", "postgresql://soma:soma@postgres:5432/somaagent01"
            ),
            "kafka_bootstrap_servers": cfg.env("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092"),
            "redis_url": cfg.env("REDIS_URL", "redis://redis:6379/0"),
            "otlp_endpoint": cfg.env("OTLP_ENDPOINT", ""),
            "model_profiles_path": cfg.env("MODEL_PROFILES_PATH", "conf/model_profiles.yaml"),
            "extra": {},
            "metrics_port": int(cfg.env("GATEWAY_METRICS_PORT", "9400")),
            "metrics_host": cfg.env("GATEWAY_METRICS_HOST", "0.0.0.0"),
            "opa_url": cfg.env("OPA_URL", "http://opa:8181"),
        }

        return {
            "DEV": dev_defaults,
            "STAGING": staging_defaults,
            "PROD": prod_defaults,
        }
