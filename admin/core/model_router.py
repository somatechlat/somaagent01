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
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

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

    provider: str  # e.g. "groq", "openai", "anthropic"
    name: str  # LLMModelConfig.name — never an invented catalog entry
    display_name: str
    capabilities: List[str] = field(default_factory=list)
    priority: int = 0  # Higher = preferred
    cost_tier: str = "standard"  # free, low, standard, premium
    reason: str = ""  # Selection reason for logging
    # Real catalog ctx_length from LLMModelConfig — 0 means unknown, never invented.
    ctx_length: int = 0


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


async def resolve_model_pin(name: str | None) -> Any | None:
    """Resolve an operator's pinned model name to a catalog row.

    A pin is an override, not a guess. It either names an active
    ``LLMModelConfig`` row or it is a refusal - silently falling through to
    "route by priority" turns a typo in a setting into a routing change
    nobody can see (fail-closed, Rule 91).

    ``None``/empty means no pin: capability and priority decide, which is
    the normal path.
    """
    if not name:
        return None

    from asgiref.sync import sync_to_async

    from admin.llm.models import LLMModelConfig

    def _lookup() -> Any | None:
        return (
            LLMModelConfig.objects.filter(name=name, is_active=True).first()
            or LLMModelConfig.objects.filter(display_name=name, is_active=True).first()
        )

    row = await sync_to_async(_lookup)()
    if row is None:
        raise NoCapableModelError(
            {"pinned": name},
            f"the pinned model {name!r} is not an active LLMModelConfig row",
        )
    return row


async def select_model(
    required_capabilities: Set[str],
    capsule_body: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
    prefer_cost_tier: Optional[str] = None,
    preferred_model_id: Optional[int] = None,
    preferred_name: Optional[str] = None,
) -> SelectedModel:
    """
    Select optimal LLM model based on requirements.

    Algorithm:
    1. Query LLMModelConfig (is_active=True)
    2. Filter by required capabilities
    3. Honour Capsule.chat_model (preferred_model_id) when active+capable
    4. Apply Capsule allowed_models constraint
    5. Apply cost tier preference
    6. Sort by priority DESC
    7. Return highest priority match

    Args:
        required_capabilities: Set of required capabilities
        capsule_body: Optional Capsule.body with allowed_models
        tenant_id: Tenant ID for isolation
        prefer_cost_tier: Preferred cost tier
        preferred_model_id: Capsule.chat_model PK — wins over priority when
            that model is active and capable; otherwise warn and fall through

    Returns:
        SelectedModel with selected model details

    Raises:
        NoCapableModelError: If no model matches, or the registry is unavailable
    """
    # An operator pin by name is an override, and it must resolve. resolve_model_pin
    # raises when the name is not an active catalog row rather than letting a typo
    # fall through to priority routing.
    if preferred_name:
        pinned = await resolve_model_pin(preferred_name)
        if pinned is not None:
            preferred_model_id = getattr(pinned, "id", preferred_model_id)

    # Try to import Django ORM model
    try:
        from asgiref.sync import sync_to_async

        from admin.llm.models import LLMModelConfig

        # 1. Query active models
        queryset = LLMModelConfig.objects.filter(is_active=True)

        # 2. Filter by tenant if provided and field exists
        if tenant_id and hasattr(LLMModelConfig, "tenant_id"):
            queryset = queryset.filter(tenant_id=tenant_id) | queryset.filter(
                tenant_id__isnull=True
            )

        # Execute query (async-safe)
        @sync_to_async
        def _query_models():
            return list(queryset.order_by("-priority"))

        models = await _query_models()

    except ImportError as exc:
        # Fail-closed: an unavailable registry is a routing failure. A
        # fabricated catalog would send real traffic at models nobody
        # provisioned (VIBE §1/§4).
        raise NoCapableModelError(
            required_capabilities,
            f"LLM model registry unavailable: {exc}",
        ) from exc

    # 3. Filter by capabilities
    capable_models = []
    for model in models:
        m: Any = model
        model_caps = set(
            m.capabilities if hasattr(m, "capabilities") else m.get("capabilities", [])
        )
        if required_capabilities.issubset(model_caps):
            capable_models.append(model)

    if not capable_models:
        raise NoCapableModelError(
            required_capabilities, "No active model has all required capabilities"
        )

    # 3b. Capsule.chat_model binding (admin/llm/api.py set_slots). The slot is
    # authoritative over priority when the model is active and capable.
    if preferred_model_id is not None:
        preferred = next(
            (m for m in capable_models if _get_attr(m, "id", None) == preferred_model_id),
            None,
        )
        if preferred is not None:
            return SelectedModel(
                provider=_get_attr(preferred, "provider", "openrouter"),
                name=_get_name(preferred),
                display_name=_get_attr(preferred, "display_name", _get_name(preferred)),
                capabilities=list(_get_attr(preferred, "capabilities", [])),
                priority=_get_priority(preferred),
                cost_tier=_get_tier(preferred),
                reason=f"Capsule.chat_model id={preferred_model_id}",
                ctx_length=int(_get_attr(preferred, "ctx_length", 0) or 0),
            )
        logger.warning(
            "Capsule.chat_model id=%s is not an active capable model — "
            "falling through to priority routing",
            preferred_model_id,
        )

    # 4. Apply Capsule allowed_models constraint
    if capsule_body:
        allowed = capsule_body.get("allowed_models")
        if allowed:
            capable_models = [m for m in capable_models if _get_name(m) in allowed]

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
        ctx_length=int(_get_attr(best, "ctx_length", 0) or 0),
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
