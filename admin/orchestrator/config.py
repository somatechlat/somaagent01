"""Configuration re-exports for the orchestrator.

The project uses the **single source of truth** located in
``src.core.config`` (a Pydantic‑based configuration package).

* ``CentralizedConfig`` is an alias that returns the shared ``cfg``
  singleton from ``src.core.config``.
* ``load_config()`` returns the same singleton instance.

All code should import directly from ``src.core.config``.
"""

from __future__ import annotations

# Import the canonical configuration objects.
# from src.core.config import cfg as _cfg, Config as _Config, load_config as _load_config  # TODO: Removed - src/ deleted in Phase 1


class CentralizedConfig(_Config):
    """Alias – instantiating returns the global ``cfg``.

    The property getters are available directly on the canonical ``Config``
    model. ``__new__`` returns the already‑loaded singleton to ensure a
    single source of truth.
    """

    def __new__(cls, *args, **kwargs):  # pragma: no cover – simple delegation
        # Return the already‑instantiated configuration singleton.
        return _cfg


def load_config() -> _Config:
    """Return the canonical configuration singleton.

    ``src.core.config.load_config`` already implements lazy loading and
    caching, so we forward directly to it.
    """
    return _load_config()


# Export the public symbols.
# ``cfg`` is the singleton configuration instance.
__all__ = ["CentralizedConfig", "load_config", "cfg"]
