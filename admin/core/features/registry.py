"""Feature Registry — Single Source of Truth for System Capabilities.

SRS Source: SRS-FEATURE-FLAGS-2026-01-16

Applied Personas:
- PhD Architect: Dependency graph awareness
- Security Auditor: Credential requirements definition
- Product Owner: Tier stratification

Vibe Coding Rules:
- Immutable definitions (frozen)
- No runtime registration (static registry)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional


@dataclass(frozen=True)
class FeatureFlag:
    """Definition of a system feature.

    Attributes:
        code: Unique identifier (e.g., "voice_cloning")
        name: Human readable name
        description: User-facing description
        tier: Minimum plan tier required ("free", "starter", "team", "enterprise")
        dependencies: List of other feature codes required
        required_credentials: List of secret keys required in Vault
        is_core: If True, enabled by default for all valid tiers
        beta: If True, requires explicit opt-in
    """

    code: str
    name: str
    description: str
    tier: Literal["free", "starter", "team", "enterprise"] = "free"
    dependencies: List[str] = field(default_factory=list)
    required_credentials: List[str] = field(default_factory=list)
    is_core: bool = False
    beta: bool = False


# =============================================================================
# FEATURE REGISTRY — The Capability Matrix
# =============================================================================

FEATURE_REGISTRY: Dict[str, FeatureFlag] = {
    # -------------------------------------------------------------------------
    # CORE PLATFORM (Tier 1)
    # -------------------------------------------------------------------------
    "chat": FeatureFlag(
        code="chat",
        name="Basic Chat",
        description="Core conversational capability",
        tier="free",
        is_core=True,
    ),
    "personas": FeatureFlag(
        code="personas",
        name="Custom Personas",
        description="Create and customize agent personas",
        tier="free",
        is_core=True,
    ),
    "memory_basic": FeatureFlag(
        code="memory_basic",
        name="Short-term Memory",
        description="Conversation context window",
        tier="free",
        is_core=True,
    ),

    # -------------------------------------------------------------------------
    # ADVANCED INTELLIGENCE (Tier 2/3)
    # -------------------------------------------------------------------------
    "memory_long_term": FeatureFlag(
        code="memory_long_term",
        name="Long-term Memory (SomaBrain)",
        description="Vector-based semantic recall",
        tier="starter",
        dependencies=["memory_basic"],
    ),
    "learning": FeatureFlag(
        code="learning",
        name="Active Learning",
        description="Agent learns from interactions (RLM)",
        tier="team",
        dependencies=["memory_long_term"],
    ),
    "rlm_reasoning": FeatureFlag(
        code="rlm_reasoning",
        name="Recursive Reasoning",
        description="Multi-step thought process (System 2)",
        tier="team",
    ),

    # -------------------------------------------------------------------------
    # MULTIMODAL (Tier 2+)
    # -------------------------------------------------------------------------
    "vision": FeatureFlag(
        code="vision",
        name="Computer Vision",
        description="Analyze and understand images",
        tier="starter",
    ),
    "image_generation": FeatureFlag(
        code="image_generation",
        name="Image Generation",
        description="Create images from text",
        tier="starter",
        # credential requirement enforced at gateway/model router level usually,
        # but listing here for UI awareness
    ),
    "voice_synthesis": FeatureFlag(
        code="voice_synthesis",
        name="Voice Synthesis",
        description="Text-to-Speech capability",
        tier="starter",
    ),
    "voice_cloning": FeatureFlag(
        code="voice_cloning",
        name="Voice Cloning",
        description="Custom voice constraints",
        tier="team",
        dependencies=["voice_synthesis"],
        beta=True,
    ),

    # -------------------------------------------------------------------------
    # CONNECTIVITY & TOOLS (Tier 2+)
    # -------------------------------------------------------------------------
    "web_browsing": FeatureFlag(
        code="web_browsing",
        name="Web Browsing",
        description="Live internet access",
        tier="starter",
    ),
    "tools_custom": FeatureFlag(
        code="tools_custom",
        name="Custom Tools",
        description="Define custom Python/HTTP tools",
        tier="team",
    ),
    "mcp_server": FeatureFlag(
        code="mcp_server",
        name="MCP Protocol Support",
        description="Connect to MCP servers",
        tier="team",
        beta=True,
    ),
}


def get_feature(code: str) -> FeatureFlag:
    """Get feature definition.

    Args:
        code: Feature code

    Returns:
        FeatureFlag definition

    Raises:
        KeyError: If feature not found
    """
    if code not in FEATURE_REGISTRY:
        raise KeyError(f"Unknown feature: {code}")
    return FEATURE_REGISTRY[code]


def list_features() -> List[FeatureFlag]:
    """List all registered features."""
    return list(FEATURE_REGISTRY.values())
