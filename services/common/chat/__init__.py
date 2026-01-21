"""Chat service package.

VIBE Rule 245 Compliant: Original 898-line chat_service.py split into modules.

This package provides a facade over the extracted services:
- ConversationService: CRUD operations for conversations
- MessageService: Core send_message flow
- SessionManager: Agent session initialization
- ChatMemoryBridge: Memory operations delegation
- TitleGenerator: Conversation title generation
"""

from services.common.chat.conversation_service import ConversationService
from services.common.chat.memory_bridge import ChatMemoryBridge
from services.common.chat.message_service import MessageService
from services.common.chat.session_manager import SessionManager
from services.common.chat.title_generator import TitleGenerator

# Re-export schemas for backward compatibility
from services.common.chat_schemas import (
    AgentSession,
    Conversation,
    Memory,
    Message,
)

__all__ = [
    # Services
    "ConversationService",
    "MessageService",
    "SessionManager",
    "ChatMemoryBridge",
    "TitleGenerator",
    # Schemas (re-exported for convenience)
    "Conversation",
    "Message",
    "AgentSession",
    "Memory",
]
