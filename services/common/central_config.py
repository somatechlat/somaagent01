"""Legacy shim for configuration – forwards everything to the canonical
``src.core.config`` package.

Historically the project used a bespoke ``CentralizedConfig`` class defined
here and exported a module‑level singleton ``cfg``.  The modern refactor has
consolidated all settings into the **single source of truth** located in
``src.core.config`` (a Pydantic ``Config`` model with a ``cfg`` facade).

To keep existing imports working without duplicating any logic we simply
re‑export that canonical singleton.  The ``CentralizedConfig`` name is kept
as an alias so that ``isinstance(cfg, CentralizedConfig)`` continues to
behave as expected, but it points to the same underlying object.
"""

from __future__ import annotations

# Import the canonical configuration objects.
from src.core.config import cfg as _cfg, Config as _Config


class CentralizedConfig(_Config):
    """Compatibility alias – behaves exactly like the canonical ``Config``.

    The class does not add any new behaviour; it merely exists so that code
    importing ``CentralizedConfig`` continues to resolve.  Instantiating the
    class returns the shared singleton ``_cfg``.
    """

    def __new__(cls, *args, **kwargs):  # pragma: no cover – simple delegation
        return _cfg


# Export the shared singleton under the historic name.
cfg = _cfg

__all__ = ["CentralizedConfig", "cfg"]
