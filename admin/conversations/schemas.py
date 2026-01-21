"""Conversations API Schemas.

Pydantic models for conversation and message data transfer objects.

- PhD Dev: Strict validation
- PM: Clear contract
- QA: Type safety
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# =============================================================================
# CONVERSATION SCHEMAS
# =============================================================================


class Conversation(BaseModel):
    """Conversation definition.

    Represents a chat conversation between a user and an agent.

    Attributes:
        conversation_id: Unique identifier for the conversation.
        agent_id: The agent handling this conversation.
        user_id: The user participating in this conversation.
        tenant_id: Tenant isolation identifier.
        title: Optional human-readable title.
        status: Current state (active, ended, archived, deleted).
        message_count: Total messages in conversation.
        created_at: ISO 8601 creation timestamp.
        updated_at: ISO 8601 last update timestamp.
    """

    conversation_id: str
    agent_id: str
    user_id: str
    tenant_id: str
    title: Optional[str] = None
    status: str  # active, ended, archived, deleted
    message_count: int
    created_at: str
    updated_at: str


class ConversationCreate(BaseModel):
    """Create conversation request.

    Attributes:
        agent_id: Agent to handle the conversation.
        user_id: User starting the conversation.
        tenant_id: Tenant context.
        title: Optional initial title.
    """

    agent_id: str
    user_id: str
    tenant_id: str
    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Update conversation request.

    Attributes:
        title: New title for the conversation.
    """

    title: Optional[str] = None


# =============================================================================
# MESSAGE SCHEMAS
# =============================================================================


class Message(BaseModel):
    """Chat message.

    Represents a single message in a conversation.

    Attributes:
        message_id: Unique message identifier.
        conversation_id: Parent conversation.
        role: Message author role (user, assistant, system, tool).
        content: Message text content.
        metadata: Optional additional data (tool calls, etc.).
        created_at: ISO 8601 creation timestamp.
    """

    message_id: str
    conversation_id: str
    role: str  # user, assistant, system, tool
    content: str
    metadata: Optional[dict] = None
    created_at: str


class MessageCreate(BaseModel):
    """Send message request.

    Attributes:
        content: Message text to send.
        role: Message role (typically 'user' for client-sent messages).
    """

    content: str
    role: str = "user"


# =============================================================================
# STATS SCHEMAS
# =============================================================================


class ConversationStats(BaseModel):
    """Conversation statistics.

    Aggregate metrics for a conversation.

    Attributes:
        total_tokens: Total tokens consumed.
        user_messages: Count of user messages.
        assistant_messages: Count of assistant messages.
        tool_calls: Count of tool invocations.
        duration_seconds: Conversation duration in seconds.
    """

    total_tokens: int
    user_messages: int
    assistant_messages: int
    tool_calls: int
    duration_seconds: int


# =============================================================================
# SEARCH SCHEMAS
# =============================================================================


class ConversationSearchRequest(BaseModel):
    """Conversation search request.

    Attributes:
        query: Search query string.
        agent_id: Optional filter by agent.
        limit: Maximum results to return.
    """

    query: str
    agent_id: Optional[str] = None
    limit: int = 20


class ConversationSearchResult(BaseModel):
    """Search result container.

    Attributes:
        query: Original search query.
        results: Matching conversations.
        total: Total matches found.
    """

    query: str
    results: list[Conversation]
    total: int
