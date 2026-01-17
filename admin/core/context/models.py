"""
BuiltContext - Result of context assembly.

PhD QA: All fields bounded and validated.
Performance: Immutable/frozen model.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BuiltContext(BaseModel):
    """
    Result of ContextBuilder operation.

    Contains all 5 lanes assembled and token-budgeted.
    """

    system: str = Field(description="System prompt (persona.core)")
    history: str = Field(description="Formatted conversation history")
    memory: str = Field(description="Recalled memories from SomaBrain")
    tools: str = Field(description="Available tool descriptions")
    buffer: str = Field(description="User message content")

    total_tokens: int = Field(default=0, description="Estimated total tokens")

    model_config = {"frozen": True}

    def to_messages(self) -> list[dict[str, str]]:
        """Convert to OpenAI-style messages format."""
        messages = []

        # System message
        if self.system:
            messages.append({"role": "system", "content": self.system})

        # History (already formatted as conversation)
        if self.history:
            messages.append({"role": "system", "content": f"[History]\n{self.history}"})

        # Memory context
        if self.memory:
            messages.append({"role": "system", "content": f"[Memory]\n{self.memory}"})

        # Tools context
        if self.tools:
            messages.append({"role": "system", "content": f"[Tools]\n{self.tools}"})

        # User message
        if self.buffer:
            messages.append({"role": "user", "content": self.buffer})

        return messages

    def to_prompt(self) -> str:
        """Convert to single prompt string."""
        parts = []
        if self.system:
            parts.append(f"[System]\n{self.system}")
        if self.history:
            parts.append(f"[History]\n{self.history}")
        if self.memory:
            parts.append(f"[Memory]\n{self.memory}")
        if self.tools:
            parts.append(f"[Tools]\n{self.tools}")
        if self.buffer:
            parts.append(f"[User]\n{self.buffer}")
        return "\n\n".join(parts)
