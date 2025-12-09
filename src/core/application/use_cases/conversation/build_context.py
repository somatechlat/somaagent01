"""Build context use case.

This use case handles building LLM context from conversation history
and memory retrieval.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol

LOGGER = logging.getLogger(__name__)


class ContextBuilderProtocol(Protocol):
    """Protocol for context building."""

    async def build_for_turn(
        self, turn_envelope: Dict[str, Any], max_prompt_tokens: int
    ) -> Any: ...


class SessionRepositoryProtocol(Protocol):
    """Protocol for session operations."""

    async def list_events(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]: ...


@dataclass
class BuildContextInput:
    """Input for build context use case."""

    session_id: str
    tenant: str
    user_message: str
    persona_id: Optional[str] = None
    system_prompt: Optional[str] = None
    max_tokens: int = 4096


@dataclass
class BuildContextOutput:
    """Output from build context use case."""

    messages: List[Dict[str, str]]
    debug: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None


class BuildContextUseCase:
    """Use case for building LLM context."""

    def __init__(
        self,
        context_builder: ContextBuilderProtocol,
        session_repo: SessionRepositoryProtocol,
    ):
        self._context_builder = context_builder
        self._session_repo = session_repo

    async def execute(self, input_data: BuildContextInput) -> BuildContextOutput:
        """Build context for LLM turn."""
        try:
            # Get conversation history
            history = await self._session_repo.list_events(input_data.session_id, limit=20)
            history_messages = self._history_to_messages(history)

            # Build turn envelope
            turn_envelope = {
                "tenant_id": input_data.tenant,
                "session_id": input_data.session_id,
                "system_prompt": input_data.system_prompt or "",
                "user_message": input_data.user_message,
                "history": history_messages,
            }

            # Build context
            built_context = await self._context_builder.build_for_turn(
                turn_envelope, max_prompt_tokens=input_data.max_tokens
            )

            # Extract messages
            messages = [
                {"role": msg.get("role", "user"), "content": str(msg.get("content", ""))}
                for msg in built_context.messages
            ]

            return BuildContextOutput(
                messages=messages,
                debug=getattr(built_context, "debug", {}),
                success=True,
            )

        except Exception as e:
            LOGGER.exception("Context building failed")
            return BuildContextOutput(
                messages=[],
                success=False,
                error=str(e),
            )

    def _history_to_messages(self, events: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Convert history events to message format."""
        messages: List[Dict[str, str]] = []
        for entry in events:
            if not isinstance(entry, dict):
                continue
            role = entry.get("type")
            if role == "user":
                content = entry.get("message") or ""
                if content:
                    messages.append({"role": "user", "content": str(content)})
            elif role == "assistant":
                content = entry.get("message") or ""
                if content:
                    messages.append({"role": "assistant", "content": str(content)})
        return messages
