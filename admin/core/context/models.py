"""BuiltContext — Result of 5-lane context assembly.

Immutable Pydantic model. Conversion to LangChain messages
lives in the orchestrator, not here.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class BuiltContext(BaseModel):
    """Result of ContextBuilder.build().

    Contains all 5 lanes assembled and token-budgeted.
    Frozen — no mutation after construction.
    """

    system: str = Field(description="System prompt (persona.core + injection prompts)")
    history: str = Field(description="Formatted conversation history")
    memory: str = Field(description="Recalled memories from SomaBrain / SFM")
    tools: str = Field(description="Available tool descriptions")
    buffer: str = Field(description="Current user message")

    total_tokens: int = Field(default=0, description="Estimated total tokens")

    model_config = {"frozen": True}
