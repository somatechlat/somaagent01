"""
Triad Service Protocols - Abstract Interfaces for Brain and Memory.

These protocols define the contract between services, enabling:
- Direct Python calls in single-process mode (AAAS)
- HTTP/gRPC calls in distributed mode

VIBE Compliance:
- Rule 2: Real implementations only
- Rule 8: Django Ninja for HTTP adapters
- Rule 100: Centralized configuration
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BrainServiceProtocol(Protocol):
    """
    Protocol for accessing SomaBrain cognitive services.

    In single-process mode: DirectBrainAdapter uses Python imports
    In distributed mode: HTTPBrainAdapter uses httpx to :9696
    """

    def encode(self, text: str) -> list[float]:
        """Encode text to vector using quantum layer."""
        ...

    def remember(
        self,
        content: str,
        *,
        tenant: str = "default",
        session_id: str | None = None,
        agent_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Store a memory in the cognitive core."""
        ...

    def recall(
        self,
        query: str,
        *,
        top_k: int = 10,
        tenant: str = "default",
        filters: dict | None = None,
    ) -> list[dict]:
        """Recall memories matching the query."""
        ...

    def apply_feedback(
        self,
        session_id: str,
        signal: str,
        value: float,
    ) -> dict:
        """Apply reinforcement signal to learning system."""
        ...


@runtime_checkable
class MemoryServiceProtocol(Protocol):
    """
    Protocol for accessing SomaFractalMemory storage services.

    In single-process mode: DirectMemoryAdapter uses Python imports
    In distributed mode: HTTPMemoryAdapter uses httpx to :10101
    """

    def store(
        self,
        coordinate: tuple[float, ...],
        payload: dict,
        *,
        tenant: str = "default",
        namespace: str = "default",
    ) -> dict:
        """Store data at a coordinate."""
        ...

    def search(
        self,
        query: str | list[float],
        *,
        top_k: int = 10,
        tenant: str = "default",
        namespace: str = "default",
        filters: dict | None = None,
    ) -> list[dict]:
        """Search for similar vectors."""
        ...

    def get(
        self,
        coordinate: tuple[float, ...],
        *,
        tenant: str = "default",
        namespace: str = "default",
    ) -> dict | None:
        """Get data at a specific coordinate."""
        ...

    def delete(
        self,
        coordinate: tuple[float, ...],
        *,
        tenant: str = "default",
        namespace: str = "default",
    ) -> bool:
        """Delete data at a coordinate."""
        ...

    def health(self) -> dict:
        """Health check."""
        ...
