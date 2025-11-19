"""Centralized configuration wrapper for the orchestrator.

The existing configuration system lives in ``src.core.config`` and already
provides a fully‑validated ``Config`` model.  This thin wrapper exposes only the
values that services need while guaranteeing a **single source of truth**.

All code that previously imported ``services.common.runtime_config.cfg`` should
now import ``orchestrator.core.cfg``.  The wrapper forwards calls to the
underlying loader, so no duplicate validation logic is introduced.
"""

from __future__ import annotations

from src.core.config.loader import get_config, reload_config


class CentralizedConfig:
    """Facade around the singleton ``Config`` object.

    The orchestrator creates one instance of this class (exported as ``cfg``)
    and passes it to services that need configuration values.  Because the
    underlying ``Config`` model is immutable after loading, the facade is safe
    to share across async tasks.
    """

    def __init__(self) -> None:
        self._cfg = get_config()

    # ------------------------------------------------------------------
    # Typed getters – expose only the fields used by services.
    # ------------------------------------------------------------------
    def get_postgres_dsn(self) -> str:
        return self._cfg.get_postgres_dsn()

    def get_kafka_bootstrap_servers(self) -> str:
        return self._cfg.get_kafka_bootstrap_servers()

    def get_redis_url(self) -> str:
        return self._cfg.get_redis_url()

    def get_somabrain_url(self) -> str:
        return self._cfg.get_somabrain_url()

    def get_opa_url(self) -> str:
        return self._cfg.get_opa_url()

    def is_auth_required(self) -> bool:
        return self._cfg.is_auth_required()

    # ------------------------------------------------------------------
    # Reload helper – used by the config‑update listener.
    # ------------------------------------------------------------------
    def reload(self) -> None:
        """Force a reload of the configuration from environment/files.

        ``reload_config`` clears the module‑level cache; after calling it we
        re‑fetch the ``Config`` instance so that subsequent calls see the new
        values.
        """
        reload_config()
        self._cfg = get_config()


# Export a singleton that mirrors the historic ``cfg`` façade used throughout the
# code base.
cfg = CentralizedConfig()
