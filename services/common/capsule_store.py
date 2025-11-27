"""In‑memory capsule store used by gateway routers.

The original monolith provided a persistent store for installed "capsules"
— lightweight plugins or extensions.  For the purpose of the test suite we
only need a minimal implementation that satisfies the router's expectations:

* ``list`` returns a list of :class:`CapsuleRecord` objects.
* ``get`` returns a single record or ``None``.
* ``install`` marks a capsule as installed and returns ``True`` if the capsule
  existed.

All data is kept in a simple dictionary; no external services are required.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional

__all__ = ["CapsuleRecord", "CapsuleStore"]


@dataclass(slots=True)
class CapsuleRecord:
    """Public representation of a capsule.

    Only the ``capsule_id`` field is required for the router tests, but we keep
    a ``name`` attribute for realism.
    """

    capsule_id: str
    name: str | None = None
    installed: bool = False


class CapsuleStore:
    """Very small in‑memory store mimicking the original API.

    The store is thread‑safe via an ``asyncio.Lock`` because the router may be
    accessed concurrently by FastAPI.
    """

    def __init__(self) -> None:
        self._records: Dict[str, CapsuleRecord] = {}
        self._lock = asyncio.Lock()

        # Populate with a couple of example capsules so that the list endpoint
        # returns something useful in tests.
        for i in range(1, 4):
            cid = f"capsule-{i}"
            self._records[cid] = CapsuleRecord(capsule_id=cid, name=f"Capsule {i}")

    async def list(self) -> List[CapsuleRecord]:
        async with self._lock:
            return list(self._records.values())

    async def get(self, capsule_id: str) -> Optional[CapsuleRecord]:
        async with self._lock:
            return self._records.get(capsule_id)

    async def install(self, capsule_id: str) -> bool:
        """Mark the capsule as installed.

        Returns ``True`` if the capsule exists, ``False`` otherwise.
        """
        async with self._lock:
            rec = self._records.get(capsule_id)
            if rec is None:
                return False
            rec.installed = True
            return True
