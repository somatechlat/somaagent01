"""Administrative (infrastructure) settings for SomaAgent.

This module provides a **single source of truth** for all system‑wide
configuration that is not UI‑specific (Kafka, Postgres, Redis, OPA, metrics,
auth flags, vault settings, etc.). It mirrors the existing :class:`SA01Settings`
but is exported as ``ADMIN_SETTINGS`` so that future code can clearly
distinguish between *admin* configuration and UI runtime overrides stored in
``UiSettingsStore``.

The original implementation duplicated defaults and bypassed the centralised
config. The current version replaces that with a thin proxy that reads from the
canonical ``src.core.config`` configuration model while preserving the legacy
attribute names expected by existing code.
"""

from __future__ import annotations

from src.core.config import cfg


class _AdminSettingsProxy:
    """Proxy exposing legacy attribute names backed by ``cfg.settings()``.

    The original ``AdminSettings`` inherited from ``SA01Settings`` and thus
    provided a flat namespace.  The proxy maps each accessed attribute to the
    appropriate field in the Pydantic ``Config`` model.
    """

    # Service‑level attributes
    @property
    def metrics_port(self) -> int:
        return cfg.settings().service.metrics_port

    @property
    def metrics_host(self) -> str:
        return cfg.settings().service.host

    # Infrastructure attributes
    @property
    def kafka_bootstrap_servers(self) -> str:
        return cfg.settings().kafka.bootstrap_servers

    @property
    def otlp_endpoint(self) -> str | None:
        # Directly expose the configured OTLP endpoint without fallback.
        # Returns ``None`` if not set, aligning with the single source of truth.
        return cfg.settings().external.otlp_endpoint

    @property
    def postgres_dsn(self) -> str:
        return cfg.settings().database.dsn

    # Preserve any future dynamic attribute access via ``__getattr__`` – fallback
    # to the underlying Config model for forward‑compatibility.
    def __getattr__(self, name: str):  # pragma: no cover – defensive
        return getattr(cfg.settings(), name)


# Export a singleton used throughout the codebase.
ADMIN_SETTINGS = _AdminSettingsProxy()
