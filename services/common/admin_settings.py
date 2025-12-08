from __future__ import annotations

"""Administrative configuration – deprecated proxy to the canonical ``cfg``.

The original ``admin_settings`` module duplicated configuration that now lives
in ``src.core.config.cfg``.  To satisfy VIBE rule **NO BULLSHIT** we keep this
module only as a thin proxy that forwards attribute access to the canonical
service configuration.  A deprecation warning is emitted on first use to guide
developers toward importing ``cfg`` directly.
"""

import warnings
from dataclasses import dataclass
from typing import Any

from src.core.config import cfg


@dataclass(slots=True)
class AdminSettings:
    """Deprecated thin proxy exposing service‑level configuration fields.

    All values are delegated to ``cfg.settings().service`` – the canonical
    configuration model.  A deprecation warning is emitted on first
    instantiation to guide developers toward using ``cfg`` directly.
    """

    # The underlying service configuration will be loaded lazily.
    _service_cfg: object = None
    _cfg: object = None  # Holds the full Config instance; required for legacy properties.

    def __init__(self) -> None:  # pragma: no cover – simple proxy constructor
        warnings.warn(
            "services.common.admin_settings.ADMIN_SETTINGS is deprecated – use src.core.config.cfg instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Load the full configuration once.
        self._cfg = cfg.settings()
        # Populate service‑level attributes for backward compatibility.
        self._service_cfg = self._cfg.service
        for name in getattr(self._service_cfg, "__dataclass_fields__", {}):
            setattr(self, name, getattr(self._service_cfg, name))

    # ---------------------------------------------------------------------
    # Legacy attribute helpers – many parts of the codebase (especially the
    # gateway routers) expect top‑level attributes such as ``postgres_dsn`` or
    # ``opa_url`` on the ``ADMIN_SETTINGS`` singleton.  These were originally
    # provided by the old ``admin_settings`` module.  The new implementation
    # delegates to the appropriate section of the central ``cfg`` object.
    # ---------------------------------------------------------------------
    @property
    def postgres_dsn(self) -> str:  # pragma: no cover – simple delegation
        return getattr(self._cfg.database, "dsn", "")

    @property
    def redis_url(self) -> str:  # pragma: no cover
        return getattr(self._cfg.redis, "url", "")

    @property
    def opa_url(self) -> str:  # pragma: no cover
        return getattr(self._cfg.external, "opa_url", "")

    @property
    def somabrain_base_url(self) -> str:  # pragma: no cover
        return getattr(self._cfg.external, "somabrain_base_url", "")

    # -----------------------------------------------------------------
    # Dynamic attribute fallback – many legacy modules access a variety of
    # configuration values directly on ``ADMIN_SETTINGS`` (e.g.
    # ``metrics_port``, ``metrics_host``, ``kafka_bootstrap_servers``,
    # ``deployment_mode``).  Rather than enumerating each one, we forward any
    # unknown attribute lookup to the underlying ``Config`` instance.  This
    # maintains backward compatibility with the original monolithic settings
    # object while keeping the implementation simple.
    # -----------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:  # pragma: no cover
        # Prefer top‑level Config attributes (service, database, etc.).
        if hasattr(self._cfg, name):
            return getattr(self._cfg, name)
        # Fall back to the nested ``service`` model for common service fields.
        if hasattr(self._cfg.service, name):
            return getattr(self._cfg.service, name)
        # Kafka bootstrap servers are accessed via ``kafka``.
        if name == "kafka_bootstrap_servers":
            return getattr(self._cfg.kafka, "bootstrap_servers", "")
        # Metrics host/port were historically exposed on the service config.
        if name in {"metrics_host", "metrics_port"}:
            return getattr(self._cfg.service, name, "")
        # Auth flag.
        if name == "auth_required":
            return getattr(self._cfg.auth, "auth_required", False)
        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {name!r}")


def _load() -> AdminSettings:
    """Factory returning a singleton admin configuration instance."""
    return AdminSettings()


# Export a singleton used throughout the codebase.
ADMIN_SETTINGS = _load()
