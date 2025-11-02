"""Shared base settings helpers for SomaAgent services."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Self

import yaml


@dataclass(slots=True)
class BaseServiceSettings:
    """Base configuration for SomaAgent services.

    Sub-classes provide environment defaults and extend the data structure with
    any additional service-specific knobs.  The base class handles environment
    resolution, .env overrides, and lazy YAML helpers so that individual
    services can focus on behaviour instead of plumbing.
    """

    environment: str
    deployment_mode: str
    postgres_dsn: str
    kafka_bootstrap_servers: str
    redis_url: str
    otlp_endpoint: str
    model_profiles_path: str = "conf/model_profiles.yaml"
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.environment = self.environment.upper()
        self.deployment_mode = self.deployment_mode.upper()

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------
    @classmethod
    def default_environment(cls) -> str:
        return "DEV"

    @classmethod
    def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
        raise NotImplementedError

    @classmethod
    def from_env(
        cls,
        *,
        environment_var: str = "SOMA_AGENT_ENV",
        overrides: Mapping[str, Any] | None = None,
    ) -> Self:
        environment = os.getenv(environment_var, cls.default_environment()).upper()
        return cls.for_environment(environment, overrides=overrides)

    @classmethod
    def for_environment(
        cls,
        environment: str,
        *,
        overrides: Mapping[str, Any] | None = None,
    ) -> Self:
        env_key = environment.upper()
        defaults = dict(cls.environment_defaults().get(env_key, {}))
        if not defaults:
            raise ValueError(f"Unknown environment '{environment}' for {cls.__name__}")
        merged: Dict[str, Any] = {**defaults, **(overrides or {})}
        return cls(environment=env_key, **merged)

    # ------------------------------------------------------------------
    # Derived helpers
    # ------------------------------------------------------------------
    def model_profiles(self) -> dict[str, Any]:
        path = Path(self.model_profiles_path)
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data

    def environment_profile(self) -> dict[str, Any]:
        profiles = self.model_profiles()
        return profiles.get(self.deployment_mode, {})

    def copy_with(self, **updates: Any) -> Self:
        payload = {**self.__dict__, **updates}
        payload.setdefault("extra", dict(self.extra))
        return type(self)(**payload)
