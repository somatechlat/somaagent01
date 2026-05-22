"""Base protocol and utilities for data stores.

Provides a uniform interface across all store implementations in services/common/.
Stores should inherit from BaseStore and implement the abstract methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, Protocol, TypeVar

T = TypeVar("T")


class StoreProtocol(Protocol, Generic[T]):
    """Uniform protocol for all stores.

    Implementations may add domain-specific methods, but must provide
    the standard CRUD surface for consistency.
    """

    async def ensure_schema(self) -> None:
        """Idempotently create required tables, indices, or Redis keys."""
        ...

    async def get(self, identifier: str) -> Optional[T]:
        """Retrieve a single record by primary identifier."""
        ...

    async def create(self, record: T) -> T:
        """Persist a new record and return the stored representation."""
        ...

    async def update(self, identifier: str, changes: dict[str, Any]) -> Optional[T]:
        """Apply partial updates and return the updated record."""
        ...

    async def delete(self, identifier: str) -> bool:
        """Hard or soft-delete a record. Returns True if something was deleted."""
        ...

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[T]:
        """List records with optional pagination and filtering."""
        ...


class BaseStore(ABC, Generic[T]):
    """Abstract base class for stores.

    Subclasses must implement the CRUD methods.  Optional helpers such as
    ``ensure_schema`` and ``list`` have default no-op or empty-list
    implementations so that minimal stores only need to override what they
    support.
    """

    @abstractmethod
    async def get(self, identifier: str) -> Optional[T]:
        """Retrieve a single record by primary identifier."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, record: T) -> T:
        """Persist a new record and return the stored representation."""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, identifier: str) -> bool:
        """Remove a record. Returns True if a record was removed."""
        raise NotImplementedError

    async def update(self, identifier: str, changes: dict[str, Any]) -> Optional[T]:
        """Apply partial updates. Default raises NotImplementedError."""
        raise NotImplementedError

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[T]:
        """Default implementation returns an empty list."""
        return []

    async def ensure_schema(self) -> None:
        """Idempotent schema / key setup. Default is a no-op."""
        pass
