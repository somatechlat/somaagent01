"""Triad memory store adapters — the ONLY two store dialects.

These implement ``services.common.memory_contract`` against the real HTTP APIs:

    SFMAdapter        -> SomaFractalMemory   POST /memories, /memories/search,
                                             DELETE /memories/{coord}
    SomaBrainAdapter  -> SomaBrain           POST /memory/remember, /memory/recall,
                                             POST /memory/forget

Nothing else may talk to a memory store. Callers go through
``services.common.memory_gateway.FanoutMemoryGateway`` — never a factory,
never a third adapter. (See ARCHITECTURE-INVARIANTS.md §0.)

Deleted 2026-09-26 — do not resurrect:

    memory_direct.py / memory_http.py   a parallel adapter stack with zero
                                        importers, reached only through the
                                        get_memory_service() factory that also
                                        had zero importers
    protocols/__init__.py               BrainServiceProtocol +
                                        MemoryServiceProtocol, the 3rd/4th
                                        declaration of one concept
"""

from __future__ import annotations

from services.common.adapters.sfm_adapter import SFMAdapter
from services.common.adapters.somabrain_adapter import SomaBrainAdapter

__all__ = [
    "SFMAdapter",
    "SomaBrainAdapter",
]
