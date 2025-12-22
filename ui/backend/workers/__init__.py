"""
Eye of God Kafka Workers Package
Per Eye of God UIX Design and CANONICAL_DESIGN.md

VIBE COMPLIANT:
- Real Kafka consumers
- No mocks or stubs
- Production-grade error handling
"""

from .conversation import ConversationWorker
from .tool_executor import ToolExecutorWorker
from .audit import AuditWorker

__all__ = [
    "ConversationWorker",
    "ToolExecutorWorker",
    "AuditWorker",
]
