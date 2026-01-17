"""
DerivedSettings - Pydantic model for all derived agent settings.

ALL fields are derived from the 3 knobs:
- intelligence_level (1-10)
- autonomy_level (1-10)
- resource_budget ($/turn)

VIBE RULE: No hardcoded values. All from capsule.body.persona.knobs.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ModelTier(str, Enum):
    """LLM model tier derived from intelligence level."""

    BUDGET = "budget"
    STANDARD = "standard"
    PREMIUM = "premium"
    FLAGSHIP = "flagship"


class ToolApproval(str, Enum):
    """Tool approval mode derived from autonomy level."""

    ALL = "all"  # Approve all tool uses
    DANGEROUS = "dangerous"  # Only approve dangerous tools
    NONE = "none"  # No approval needed


class EgressAllowed(str, Enum):
    """Egress permission derived from autonomy level."""

    NONE = "none"
    WHITELIST = "whitelist"
    EXPANDED = "expanded"
    UNRESTRICTED = "unrestricted"


class DerivedSettings(BaseModel):
    """
    Settings derived from capsule.body.persona.knobs.

    This is IMMUTABLE after creation. Pure data, no side effects.

    Performance Engineer: This is a frozen Pydantic model.
    PhD QA: All fields have bounds validation.
    """

    # --- From INTELLIGENCE (1-10) ---
    temperature: float = Field(ge=0.0, le=1.0, description="LLM temperature")
    max_tokens: int = Field(ge=256, le=16384, description="Max output tokens")
    rlm_iterations: int = Field(ge=1, le=10, description="RLM Mind-Body loop max")
    recall_limit: int = Field(ge=1, le=100, description="Memory recall limit")
    model_tier: ModelTier = Field(description="LLM model tier")
    brain_query_enabled: bool = Field(description="Can RLM query SomaBrain")

    # --- From AUTONOMY (1-10) ---
    require_hitl: bool = Field(description="Human-in-the-loop required")
    tool_approval: ToolApproval = Field(description="Tool approval mode")
    egress_allowed: EgressAllowed = Field(description="Network egress permission")

    # --- From RESOURCE ($/turn) ---
    token_limit: int = Field(ge=1000, le=200000, description="Total token budget")
    cost_tier: Literal["budget", "standard", "premium", "flagship"] = Field(
        description="Cost tier"
    )
    thinking_budget: int = Field(ge=0, le=8192, description="Thinking tokens budget")

    model_config = {"frozen": True}
