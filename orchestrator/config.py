"""Centralized configuration for the orchestrator.

The orchestrator consolidates configuration that was previously scattered
across the individual services (gateway, workers, memory services, etc.).
It uses ``pydantic``'s ``BaseSettings`` to read environment variables with
defaults that match the existing VIBE coding rules.

Only a subset of settings required for the orchestrator skeleton are
included – additional fields can be added later without breaking the public
API.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from pydantic_settings import BaseSettings
from pydantic import Field, model_validator


class CentralizedConfig(BaseSettings):
    """Configuration model used by ``run_orchestrator``.

    The fields mirror the most common environment variables used throughout
    the code base.  Defaults are chosen to be safe for local development and
    to satisfy the VIBE rule *no placeholder values* – every field has a
    concrete default.
    """

    # General service identification
    service_name: str = Field("orchestrator", description="Name of the orchestrator service")
    environment: str = Field("DEV", description="Deployment environment (DEV/PROD)")

    # Connection strings – these are required by many downstream services.
    postgres_dsn: str = Field(default_factory=lambda: os.getenv("POSTGRES_DSN", "postgresql://postgres:postgres@localhost:5432/postgres"))
    kafka_bootstrap_servers: str = Field(default_factory=lambda: os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"))
    redis_url: str = Field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))

    # Observability / tracing
    otlp_endpoint: str = Field("http://localhost:4317", description="OTLP collector endpoint")

    # Optional feature toggles – boolean values are read as strings and then normalized.
    enable_metrics: bool = Field(True, description="Expose Prometheus metrics endpoint")
    enable_tracing: bool = Field(True, description="Enable OpenTelemetry tracing")

    class Config:
        env_prefix = ""  # No extra prefix – match existing env vars.
        case_sensitive = False

    @model_validator(mode="before")
    @classmethod
    def _coerce_bool(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Coerce common truthy strings to ``bool`` for toggle fields.

        ``pydantic`` will automatically cast ``bool`` values, but environment
        variables are always strings. This validator makes "true", "1", etc. behave as True.
        """
        for key in ("enable_metrics", "enable_tracing"):
            if key in values:
                raw = str(values[key]).lower()
                values[key] = raw in {"true", "1", "yes", "on"}
        # Normalise environment to upper case.
        if "environment" in values:
            values["environment"] = str(values["environment"]).upper()
        return values


def load_config() -> CentralizedConfig:
    """Helper to load the configuration.

    ``CentralizedConfig`` reads from the process environment, so calling this
    function is effectively a thin wrapper that can be mocked in tests.
    """
    return CentralizedConfig()
