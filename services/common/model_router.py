"""Simple, elegant model router.

One function. Capability-based. Capsule-constrained.
100% Django ORM. Single canonical source: LLMModelConfig.

VIBE Compliance: KISS principle - ~100 lines total.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class SelectedModel:
    """Result of model selection."""

    provider: str
    name: str
    display_name: str
    capabilities: list[str]
    priority: int
    cost_tier: str
    reason: str


class NoCapableModelError(Exception):
    """No model found with required capabilities."""

    pass


async def select_model(
    required_capabilities: set[str],
    capsule_body: Optional[dict] = None,
    tenant_id: Optional[str] = None,
    prefer_cost_tier: Optional[str] = None,
) -> SelectedModel:
    """Select the best model for given capabilities.

    THE ENTIRE MODEL ROUTER IN ONE SIMPLE FUNCTION.

    SINGLE SOURCE OF TRUTH: LLMModelConfig Django ORM table.

    Args:
        required_capabilities: Set like {"text", "vision"}
        capsule_body: Optional Capsule.body with allowed_models
        tenant_id: Optional tenant for future per-tenant catalogs
        prefer_cost_tier: Optional cost preference ("free", "low", "standard", "premium")

    Returns:
        SelectedModel with provider, name, and reason

    Raises:
        NoCapableModelError if no matching model found
    """
    from admin.llm.models import LLMModelConfig

    # 1. Get all active models from LLMModelConfig (SINGLE SOURCE OF TRUTH)
    models = (
        await LLMModelConfig.objects.filter(
            is_active=True,
            model_type="chat",
        )
        .order_by("-priority")
        .avalues()
    )

    # Convert to list for filtering
    models = [m async for m in models]

    # 2. Filter: has required capabilities
    capable = [
        m for m in models if required_capabilities.issubset(set(m.get("capabilities") or ["text"]))
    ]

    # 3. Filter: Capsule constraints (if any)
    if capsule_body and capsule_body.get("allowed_models"):
        allowed = set(capsule_body["allowed_models"])
        capable = [m for m in capable if m["name"] in allowed]

    # 4. Filter: Cost tier preference (if specified)
    if prefer_cost_tier:
        cost_matches = [m for m in capable if m.get("cost_tier") == prefer_cost_tier]
        if cost_matches:
            capable = cost_matches

    # 5. Return best match (already sorted by priority)
    if not capable:
        raise NoCapableModelError(f"No model found with capabilities: {required_capabilities}")

    best = capable[0]
    logger.info(
        "Model Router selected: %s/%s for capabilities=%s (priority=%d)",
        best.get("provider"),
        best.get("name"),
        required_capabilities,
        best.get("priority", 50),
    )

    return SelectedModel(
        provider=best.get("provider", "openrouter"),
        name=best.get("name"),
        display_name=best.get("display_name") or best.get("name"),
        capabilities=best.get("capabilities") or [],
        priority=best.get("priority", 50),
        cost_tier=best.get("cost_tier", "standard"),
        reason=f"Best match for {required_capabilities} (priority={best.get('priority', 50)})",
    )


def detect_required_capabilities(
    message: str,
    attachments: Optional[list] = None,
) -> set[str]:
    """Detect required capabilities from message and attachments.

    Simple MIME-based detection. No ML needed.

    Args:
        message: User message text
        attachments: List of attachment dicts with 'content_type' key

    Returns:
        Set of capability strings like {"text", "vision"}
    """
    caps: set[str] = {"text"}  # Always need text

    if not attachments:
        return caps

    for att in attachments:
        content_type = (att.get("content_type") or att.get("mime_type") or "").lower()

        # Image detection
        if content_type.startswith("image/"):
            caps.add("vision")

        # Video detection
        elif content_type.startswith("video/"):
            caps.add("video")

        # Audio detection
        elif content_type.startswith("audio/"):
            caps.add("audio")

        # CAD files
        elif content_type in (
            "application/x-dwg",
            "application/x-dxf",
            "model/vnd.dwf",
            "application/acad",
        ):
            caps.add("cad")

        # Documents (might need long context)
        elif content_type in (
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ):
            caps.add("long_context")

        # Code files
        elif content_type in (
            "text/x-python",
            "text/javascript",
            "application/json",
            "text/x-c",
            "text/x-java-source",
        ):
            caps.add("code")

    return caps


# Capability taxonomy for reference
CAPABILITY_TAXONOMY = {
    "text": "Basic text generation and chat",
    "vision": "Image understanding and analysis",
    "video": "Video understanding and analysis",
    "audio": "Audio transcription and understanding",
    "code": "Code generation, review, and execution",
    "long_context": "Long context window (>100k tokens)",
    "structured_output": "JSON/schema structured output",
    "function_calling": "Tool/function calling support",
    "cad": "CAD/engineering file processing",
    "medical": "Medical/healthcare domain expertise",
    "legal": "Legal domain expertise",
    "scientific": "Scientific research domain",
}


__all__ = [
    "SelectedModel",
    "NoCapableModelError",
    "select_model",
    "detect_required_capabilities",
    "CAPABILITY_TAXONOMY",
]
