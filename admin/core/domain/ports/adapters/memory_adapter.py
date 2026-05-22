"""Memory adapter port for domain layer.

Port interface for memory storage operations.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol


class MemoryAdapterPort(Protocol):
    """Port interface for memory operations."""

    async def store_memory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Store memory payload."""
        ...

    async def recall_memory(
        self, query: str, *, session_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Recall memories matching query."""
        ...
