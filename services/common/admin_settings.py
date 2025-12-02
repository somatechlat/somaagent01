"""Administrative (infrastructure) settings for SomaAgent.

This module provides a **single source of truth** for all system‑wide configuration
that is not UI‑specific (Kafka, Postgres, Redis, OPA, metrics, auth flags, vault
settings, etc.).  It mirrors the existing :class:`SA01Settings` but is exported
as ``ADMIN_SETTINGS`` so that future code can clearly distinguish between
*admin* configuration and UI runtime overrides stored in ``UiSettingsStore``.

The class simply inherits from :class:`SA01Settings` – which already contains the
required defaults – and exposes a ready‑made instance via ``ADMIN_SETTINGS``.
Existing code that imports ``APP_SETTINGS`` continues to work because ``APP_SETTINGS``
is still defined in ``services/gateway/main.py``; new code should import
``ADMIN_SETTINGS`` from this module.
"""

"""Administrative configuration derived from the central ``cfg`` system.

Historically this module wrapped :class:`SA01Settings`.  The VIBE refactor
replaces that legacy approach with the unified configuration exposed via
``src.core.config.cfg``.  To retain the original public name ``ADMIN_SETTINGS``
while providing the same attribute surface (e.g. ``metrics_port``,
``kafka_bootstrap_servers``), we expose the ``service`` portion of the central
configuration object.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.config import cfg


@dataclass(slots=True)
class AdminSettings:
    """Thin proxy exposing service‑level configuration fields.

    The attributes are populated from ``cfg.settings().service`` which
    contains the canonical values for metrics, Kafka, Postgres, etc.
    """

    # The service configuration model provides all required fields.
    # Using ``type: ignore`` because we dynamically assign attributes.

    def __init__(self) -> None:  # pragma: no cover – simple proxy constructor
        service_cfg = cfg.settings().service
        # Copy all attributes from the ServiceConfig onto this instance.
        for name in getattr(service_cfg, "__dataclass_fields__", {}):
            setattr(self, name, getattr(service_cfg, name))


def _load() -> AdminSettings:
    """Factory returning a singleton admin configuration instance."""
    return AdminSettings()


# Export a singleton used throughout the codebase.
ADMIN_SETTINGS = _load()
