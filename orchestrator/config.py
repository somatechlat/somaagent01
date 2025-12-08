"""Canonical configuration shim for the orchestrator.

The project now uses the **single source of truth** located in
``src.core.config`` (a Pydantic‑based configuration package).  Older code
still imports ``orchestrator.config.CentralizedConfig`` and calls
``load_config()``.  To keep backward compatibility without duplicating any
logic we provide a very thin shim that simply re‑exports the canonical
objects.

* ``CentralizedConfig`` is an alias that returns the shared ``cfg``
  singleton from ``src.core.config``.
* ``load_config()`` returns the same singleton instance.

All new code should import directly from ``src.core.config``; this shim
exists only to avoid breaking existing imports.
"""

from __future__ import annotations

# Import the canonical configuration objects.
from src.core.config import cfg as _cfg, Config as _Config, load_config as _load_config

cfg = _cfg
class CentralizedConfig(_Config):
    """Compatibility alias – instantiating returns the global ``cfg``.

    The original ``CentralizedConfig`` was a subclass of the Pydantic model
    with a few legacy property getters.  Those getters are now available
    directly on the canonical ``Config`` model, so we simply expose the same
    class and make ``__new__`` return the already‑loaded singleton.  This
    ensures that ``CentralizedConfig()`` behaves exactly like the historic
    factory while keeping a single source of truth.
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


# Export the legacy names expected by existing imports.
# Export the public symbols expected by legacy imports.
# ``cfg`` is the singleton configuration instance defined above.
__all__ = ["CentralizedConfig", "load_config", "cfg"]
