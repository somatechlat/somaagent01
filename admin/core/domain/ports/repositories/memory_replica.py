"""Memory replica store port interface.

This port defines the contract for memory replica persistence operations.
The interface matches the existing MemoryReplicaStore methods exactly
to enable seamless wrapping of the production implementation.

Production Implementation:
    src.core.infrastructure.repositories.memory_replica_store.MemoryReplicaStore
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class MemoryReplicaRowDTO:
    """Data transfer object for memory replica row.

    Mirrors the MemoryReplicaRow structure from the implementation.
    """

    id: int
    event_id: Optional[str]
    session_id: Optional[str]
    persona_id: Optional[str]
    tenant: Optional[str]
    role: Optional[str]
    coord: Optional[str]
    request_id: Optional[str]
    trace_id: Optional[str]
    payload: Dict[str, Any]
    wal_timestamp: Optional[float]
    created_at: datetime


class MemoryReplicaStorePort(ABC):
    """Abstract interface for memory replica persistence.

    This port wraps the existing MemoryReplicaStore implementation.
    All methods match the production implementation signature exactly.
    """

    @abstractmethod
    async def insert_from_wal(self, wal: Dict[str, Any]) -> int:
        """Insert a memory record from WAL event.

        Args:
            wal: WAL event payload containing memory data

        Returns:
            ID of inserted or existing record
        """
        ...

    @abstractmethod
    async def latest_wal_timestamp(self) -> Optional[float]:
        """Get the timestamp of the most recent WAL entry.

        Returns:
            Timestamp or None if no entries exist
        """
        ...

    @abstractmethod
    async def get_by_event_id(self, event_id: str) -> Optional[MemoryReplicaRowDTO]:
        """Get a memory record by event ID.

        Args:
            event_id: The event identifier

        Returns:
            Memory record or None if not found
        """
        ...

    @abstractmethod
    async def list_memories(
        self,
        *,
        limit: int = 50,
        after_id: Optional[int] = None,
        tenant: Optional[str] = None,
        persona_id: Optional[str] = None,
        role: Optional[str] = None,
        session_id: Optional[str] = None,
        universe: Optional[str] = None,
        namespace: Optional[str] = None,
        min_ts: Optional[float] = None,
        max_ts: Optional[float] = None,
        q: Optional[str] = None,
    ) -> List[MemoryReplicaRowDTO]:
        """List memory records with filtering.

        Args:
            limit: Maximum number of records to return
            after_id: Return records after this ID (pagination)
            tenant: Filter by tenant
            persona_id: Filter by persona
            role: Filter by role
            session_id: Filter by session
            universe: Filter by universe ID in metadata
            namespace: Filter by namespace
            min_ts: Minimum WAL timestamp
            max_ts: Maximum WAL timestamp
            q: Text search query

        Returns:
            List of memory records
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close database connections and release resources."""
        ...
