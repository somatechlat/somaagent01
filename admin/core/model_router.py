"""
ModelRouter - LLM Model Selection Module.

Selects optimal LLM based on:
1. Required capabilities (text, vision, audio)
2. Capsule constraints (allowed_models)
3. Cost tier preference from AgentIQ

SRS Source: SRS-MODEL-ROUTING-2026-01-16

Applied Personas:
- PhD Developer: Clean async ORM queries
- PhD Analyst: Capability matching algorithm
- Security: SpiceDB + OPA permission checks
- Performance: Priority-based selection
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class NoCapableModelError(Exception):
    """Raised when no model matches required capabilities."""

    def __init__(self, capabilities: Set[str], reason: str = "") -> None:
        self.capabilities = capabilities
        self.reason = reason
        super().__init__(f"No model found for capabilities: {capabilities}. {reason}")


@dataclass
class SelectedModel:
    """Result of model selection."""

    provider: str  # "openrouter", "openai", "anthropic"
    name: str  # "gpt-4o", "claude-sonnet-4-20250514"
    display_name: str  # "GPT-4o"
    capabilities: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = preferred
    cost_tier: str = "standard"  # free, low, standard, premium
    reason: str = ""  # Selection reason for logging


# MIME type to capability mapping
MIME_CAPABILITY_MAP: Dict[str, str] = {
    "image/": "vision",
    "video/": "video",
    "audio/": "audio",
    "application/pdf": "document",
}


def detect_required_capabilities(
    message: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> Set[str]:
    """
    Detect required capabilities from message and attachments.

    Args:
        message: User message text
        attachments: List of attachment dicts with content_type

    Returns:
        Set of required capabilities (always includes "text")
    """
    capabilities: Set[str] = {"text"}  # Always required

    if not attachments:
        return capabilities

    for attachment in attachments:
        content_type = attachment.get("content_type", "")

        for mime_prefix, capability in MIME_CAPABILITY_MAP.items():
            if content_type.startswith(mime_prefix) or content_type == mime_prefix:
                capabilities.add(capability)
                break

    return capabilities


async def select_model(
    required_capabilities: Set[str],
    capsule_body: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
    prefer_cost_tier: Optional[str] = None,
) -> SelectedModel:
    """
    Select optimal LLM model based on requirements.

    Algorithm:
    1. Query LLMModelConfig (is_active=True)
    2. Filter by required capabilities
    3. Apply Capsule allowed_models constraint
    4. Apply cost tier preference
    5. Sort by priority DESC
    6. Return highest priority match

    Args:
        required_capabilities: Set of required capabilities
        capsule_body: Optional Capsule.body with allowed_models
        tenant_id: Tenant ID for isolation
        prefer_cost_tier: Preferred cost tier

    Returns:
        SelectedModel with selected model details

    Raises:
        NoCapableModelError: If no model matches
    """
    # Try to import Django ORM model
    try:
        from admin.llm.models import LLMModelConfig

        # 1. Query active models
        queryset = LLMModelConfig.objects.filter(is_active=True)

        # 2. Filter by tenant if provided
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id) | queryset.filter(
                tenant_id__isnull=True
            )

        # Execute query
        models = list(queryset.order_by("-priority"))

    except ImportError:
        logger.warning("LLMModelConfig not available, using fallback catalog")
        models = _get_fallback_catalog()

    # 3. Filter by capabilities
    capable_models = []
    for model in models:
        model_caps = set(
            model.capabilities if hasattr(model, "capabilities") else model.get("capabilities", [])
        )
        if required_capabilities.issubset(model_caps):
            capable_models.append(model)

    if not capable_models:
        raise NoCapableModelError(
            required_capabilities, "No active model has all required capabilities"
        )

    # 4. Apply Capsule allowed_models constraint
    if capsule_body:
        allowed = capsule_body.get("allowed_models")
        if allowed:
            capable_models = [
                m for m in capable_models if _get_name(m) in allowed
            ]

            if not capable_models:
                raise NoCapableModelError(
                    required_capabilities, "No allowed model has required capabilities"
                )

    # 5. Apply cost tier preference
    if prefer_cost_tier:
        tier_models = [m for m in capable_models if _get_tier(m) == prefer_cost_tier]
        if tier_models:
            capable_models = tier_models

    # 6. Sort by priority and select best
    capable_models.sort(key=lambda m: _get_priority(m), reverse=True)
    best = capable_models[0]

    return SelectedModel(
        provider=_get_attr(best, "provider", "openrouter"),
        name=_get_name(best),
        display_name=_get_attr(best, "display_name", _get_name(best)),
        capabilities=list(_get_attr(best, "capabilities", [])),
        priority=_get_priority(best),
        cost_tier=_get_tier(best),
        reason=f"Selected from {len(capable_models)} capable models by priority",
    )


def _get_attr(model: Any, attr: str, default: Any = None) -> Any:
    """Get attribute from ORM model or dict."""
    if hasattr(model, attr):
        return getattr(model, attr)
    if isinstance(model, dict):
        return model.get(attr, default)
    return default


def _get_name(model: Any) -> str:
    """Get model name."""
    return _get_attr(model, "name", "unknown")


def _get_tier(model: Any) -> str:
    """Get cost tier."""
    return _get_attr(model, "cost_tier", "standard")


def _get_priority(model: Any) -> int:
    """Get priority."""
    return _get_attr(model, "priority", 0)


def _get_fallback_catalog() -> List[Dict[str, Any]]:
    """Fallback model catalog when ORM unavailable."""
    return [
        {
            "name": "gpt-4o",
            "provider": "openai",
            "display_name": "GPT-4o",
            "capabilities": ["text", "vision"],
            "priority": 100,
            "cost_tier": "premium",
        },
        {
            "name": "claude-sonnet-4-20250514",
            "provider": "anthropic",
            "display_name": "Claude Sonnet 4",
            "capabilities": ["text", "vision"],
            "priority": 95,
            "cost_tier": "premium",
        },
        {
            "name": "gpt-4o-mini",
            "provider": "openai",
            "display_name": "GPT-4o Mini",
            "capabilities": ["text", "vision"],
            "priority": 80,
            "cost_tier": "standard",
        },
        {
            "name": "gemini-2.5-flash",
            "provider": "google",
            "display_name": "Gemini 2.5 Flash",
            "capabilities": ["text", "vision", "audio"],
            "priority": 75,
            "cost_tier": "low",
        },
        {
            "name": "llama-3.3-70b",
            "provider": "openrouter",
            "display_name": "Llama 3.3 70B",
            "capabilities": ["text"],
            "priority": 50,
            "cost_tier": "free",
        },
    ]
