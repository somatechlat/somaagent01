"""Legacy service settings module – now deprecated.

The original ``SA01Settings`` class duplicated the functionality provided by the
new canonical configuration system under ``src.core.config.cfg``.  To satisfy the
VIBE rule **NO BULLSHIT** we keep this module only as a thin proxy that forwards
attribute access to the real configuration object.  Importers can continue to
use ``from services.common.settings_sa01 import SA01Settings`` without code
changes, but a runtime warning is emitted to encourage migration to ``cfg``.

All fields are resolved lazily from ``cfg.settings().service`` which mirrors the
previous ``BaseServiceSettings`` layout.  The proxy implements ``__getattr__``
so that any future fields added to the canonical model are automatically
available.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any, Mapping

# Import the new configuration façade.
from src.core.config import cfg


@dataclass(slots=True)
class SA01Settings:
    """Deprecated proxy for legacy ``SA01Settings``.

    The class mimics the original dataclass interface but defers all values to
    ``cfg.settings().service``.  This satisfies existing type checks while
    ensuring a **single source of truth**.
    """

    # Placeholder for the underlying service configuration; populated lazily.
    _service_cfg: Any = None

    def __post_init__(self) -> None:  # pragma: no cover – simple proxy
        # Emit a deprecation warning the first time an instance is created.
        warnings.warn(
            "services.common.settings_sa01.SA01Settings is deprecated – use src.core.config.cfg instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Load the underlying service configuration lazily.
        self._service_cfg = cfg.settings().service

    # ---------------------------------------------------------------------
    # Dynamic attribute forwarding – mirrors the original dataclass fields.
    # ---------------------------------------------------------------------
    def __getattr__(self, name: str) -> Any:
        # If the underlying config has the attribute, return it.
        if self._service_cfg is not None and hasattr(self._service_cfg, name):
            return getattr(self._service_cfg, name)
        raise AttributeError(f"{self.__class__.__name__!s} has no attribute {name!r}")

    # The original implementation exposed classmethods for defaults.  They are
    # retained as thin wrappers that delegate to the canonical config.
    @classmethod
    def default_environment(cls) -> str:
        """Return the default environment as defined by the canonical config."""
        return cfg.settings().service.environment

    @classmethod
    def environment_defaults(cls) -> Mapping[str, Mapping[str, Any]]:
        """Provide environment‑specific defaults.

        The legacy method returned a dictionary of defaults per environment.
        Here we construct a compatible structure from the current ``cfg``
        object.  This is primarily used by tests; production code should query
        ``cfg`` directly.
        """
        service = cfg.settings().service
        # Build a minimal mapping that matches the legacy shape.
        defaults = {
            "deployment_mode": service.deployment_mode,
            "postgres_dsn": cfg.settings().database.dsn,
            "kafka_bootstrap_servers": cfg.settings().kafka.bootstrap_servers,
            "redis_url": cfg.settings().redis.url,
            "otlp_endpoint": cfg.settings().external.otlp_endpoint,
            "model_profiles_path": getattr(service, "model_profiles_path", "conf/model_profiles.yaml"),
            "extra": {},
            "metrics_port": getattr(service, "metrics_port", 9400),
            "metrics_host": getattr(service, "metrics_host", "0.0.0.0"),
            "opa_url": cfg.settings().external.opa_url,
            "gateway_port": getattr(service, "port", 8010),
            "soma_base_url": getattr(service, "soma_base_url", None),
        }
        return {"DEV": defaults, "STAGING": defaults, "PROD": defaults}
