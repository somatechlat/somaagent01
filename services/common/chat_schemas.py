"""ChatService Schemas - Data classes for chat operations.

Extracted from chat_service.py for 650-line compliance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Conversation:
    """Conversation record."""

    id: str
    agent_id: str
    user_id: str
    tenant_id: str
    title: Optional[str]
    status: str
    message_count: int
    created_at: datetime
    updated_at: datetime


@dataclass
class Message:
    """Message record."""

    id: str
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    token_count: int
    model: Optional[str]
    latency_ms: Optional[int]
    created_at: datetime


@dataclass
class AgentSession:
    """Agent session from SomaBrain."""

    session_id: str
    agent_id: str
    conversation_id: str
    created_at: datetime


@dataclass
class Memory:
    """Memory record from SomaFractalMemory."""

    id: str
    content: str
    memory_type: str
    relevance_score: float
    created_at: datetime


__all__ = ["Conversation", "Message", "AgentSession", "Memory"]
