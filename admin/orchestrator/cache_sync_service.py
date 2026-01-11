"""CacheSyncService – a lightweight service that synchronises Redis‑based cache entries.

The orchestrator will mount this service in the deterministic order after the
memory service.  The implementation follows the
functional, documented, and uses the existing ``BaseSomaService`` contract.
"""

from __future__ import annotations

import logging
from typing import Any

from .base_service import BaseSomaService

LOGGER = logging.getLogger(__name__)


class CacheSyncService(BaseSomaService):
    """Wraps the existing Redis‑based cache sync worker.

    The orchestrator will mount this service under the ``/cache-sync`` prefix.
    """

    name = "cache_sync"

    def __init__(self) -> None:
        """Initialize the instance."""

        super().__init__()
        # Import lazily to avoid circular imports.
        from services.cache_sync.main import app as cache_app

        self.app: Any = cache_app

    async def _start(self) -> None:
        """Execute start."""

        LOGGER.debug("CacheSyncService start – nothing to initialise")

    async def _stop(self) -> None:
        """Execute stop."""

        LOGGER.debug("CacheSyncService stop – nothing to clean up")

    async def health(self) -> dict[str, Any]:
        """Return a simple status dictionary.
        The orchestrator will query this method when aggregating health.
        """
        return {"healthy": True, "details": {"name": self.name}}
