"""Shared data models for SomaCore.

Defines the data structures used for direct memory integration between
SomaAgent01, SomaBrain, and SomaFractalMemory.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class MemoryWriteRequest:
    """Request to write a memory."""

    payload: Dict[str, Any]
    tenant_id: str = "default"
    namespace: str = "wm"  # working memory
    universe: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class MemoryWriteResponse:
    """Response from a memory write."""

    coordinate: List[float]
    memory_id: str
    status: str = "success"


@dataclass
class MemoryReadRequest:
    """Request to read/recall memories."""

    query: str
    limit: int = 10
    tenant_id: str = "default"
    namespace: str = "wm"
    universe: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class MemoryItem:
    """Single memory item returned from recall."""

    memory_id: str
    coordinate: List[float]
    payload: Dict[str, Any]
    score: float
    created_at: datetime


@dataclass
class MemoryReadResponse:
    """Response containing recalled memories."""

    memories: List[MemoryItem]
