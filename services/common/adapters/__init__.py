"""Triad memory store adapters — SomaBrain is the ONLY store dialect.

SomaBrainAdapter -> SomaBrain  POST /memory/remember|recall|forget

SomaBrain is the sole bridge to somafractalmemory (T-1). Nothing else may
talk to a memory store. Callers go through
``services.common.memory_gateway.FanoutMemoryGateway`` — never a factory,
never a second adapter. (See ARCHITECTURE-INVARIANTS.md §0.)

Deleted 2026-09-26 — do not resurrect:

    memory_direct.py / memory_http.py   a parallel adapter stack with zero
                                        importers

Removed 2026-09-27 — agent must never connect to SFM directly:

    sfm_adapter.py  (store dialect bypassing SomaBrain)
"""

from services.common.adapters.somabrain_adapter import SomaBrainAdapter

__all__ = ["SomaBrainAdapter"]
