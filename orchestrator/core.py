"""Centralized configuration wrapper for the orchestrator.

The existing configuration system lives in ``src.core.config`` and already
provides a fully‑validated ``Config`` model.  This thin wrapper exposes only the
values that services need while guaranteeing a **single source of truth**.

All code that previously imported ``services.common.runtime_config.cfg`` should
now import ``orchestrator.core.cfg``.  The wrapper forwards calls to the
underlying loader, so no duplicate validation logic is introduced.
"""

from __future__ import annotations

"""Thin wrapper that re‑exports the canonical configuration.

The project now stores all configuration in ``src.core.config`` (a Pydantic
``Config`` model).  Historically the orchestrator defined its own
``CentralizedConfig`` class; that duplicate implementation is no longer needed.

To keep backward compatibility **without duplicating logic**, we simply import
the ``CentralizedConfig`` alias from ``orchestrator.config`` and expose the
singleton ``cfg`` exactly as before.  This satisfies the VIBE rule *NO UNNECESSARY
FILES* and guarantees a **single source of truth**.
"""

from orchestrator.config import CentralizedConfig, cfg  # re‑export

__all__ = ["CentralizedConfig", "cfg"]
