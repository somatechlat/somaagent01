"""Central configuration shim.

The project now uses ``src.core.config`` as the single source of truth for
settings.  This module re‑exports that singleton under the historic name
``cfg`` and provides a compatibility alias ``CentralizedConfig`` so that any
existing ``isinstance`` checks continue to work without modification.
"""

from __future__ import annotations

# Import the canonical configuration objects.
from src.core.config import cfg as _cfg, Config as _Config


class CentralizedConfig(_Config):
    """Compatibility alias for the original ``CentralizedConfig``.

    Instantiating this class returns the shared singleton ``_cfg`` so that
    ``CentralizedConfig()`` behaves exactly like ``cfg``.
    """

    def __new__(cls, *args, **kwargs):  # pragma: no cover – simple delegation
        return _cfg


# Export the shared singleton under the historic name.
cfg = _cfg

__all__ = ["CentralizedConfig", "cfg"]
