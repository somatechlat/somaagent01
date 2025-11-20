"""Centralized configuration for the SomaAgent01 codebase.

This module defines a single source of truth for all environment variables
required by the application.  It uses ``pydantic.BaseSettings`` so values are
validated on start‑up and can be overridden via the environment, a ``.env``
file, or explicit arguments.

The class is instantiated exactly once (a module‑level singleton) and is
exported as ``cfg`` – matching the historic ``services.common.runtime_config``
API that many modules still import.  The existing ``runtime_config`` shim now
delegates to this implementation, allowing a gradual migration without
breaking imports.
"""

from __future__ import annotations

import os
from typing import Any, Dict

from pydantic import BaseSettings, Field, validator


class CentralizedConfig(BaseSettings):
    """Application configuration loaded from environment variables.

    Only a subset of settings required for the current test suite are
    declared explicitly; additional settings can be added later without
    changing the public interface.
    """

    # Example core settings – extend as needed
    otlp_endpoint: str = Field(
        default="",
        description="OpenTelemetry collector endpoint (e.g. http://localhost:4317)",
    )
    metrics_port: int = Field(
        default=8000,
        description="Port on which the Prometheus metrics server should listen",
    )
    metrics_host: str = Field(
        default="0.0.0.0",
        description="Host for the metrics HTTP server",
    )

    # Feature‑flags – can be toggled via env var FEATURE_X=1/0
    enable_tool_executor: bool = Field(default=True)
    enable_conversation_worker: bool = Field(default=True)
    enable_outbox_sync: bool = Field(default=True)
    enable_delegation_worker: bool = Field(default=True)
    enable_gateway: bool = Field(default=True)
    enable_memory_sync: bool = Field(default=True)

    class Config:
        env_prefix = "SA01_"  # All vars are prefixed with SA01_
        case_sensitive = False

    # Helper to fetch raw env values – mirrors the historic ``runtime_config.env``
    @staticmethod
    def env(name: str, default: Any = None) -> Any:  # pragma: no cover – thin wrapper
        return os.getenv(name, default)

    # Generic getter used by the old shim
    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


# Instantiate a singleton that will be imported by the shim module.
cfg = CentralizedConfig()
