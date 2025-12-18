"""Policy Graph Router for multimodal capability selection.

Implements deterministic fallback ladders per modality with OPA policy
integration and budget enforcement. Used by the ToolExecutor to select
appropriate providers for multimodal requests.

SRS Reference: Section 16.3 (Policy Graph Router)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from services.common.capability_registry import (
    CapabilityRecord,
    CapabilityRegistry,
    CapabilityHealth,
    CostTier,
)
from services.common.policy_client import PolicyClient, PolicyRequest
from src.core.config import cfg

__all__ = [
    "PolicyGraphRouter",
    "RoutingDecision",
    "FallbackReason",
    "FALLBACK_LADDERS",
]

logger = logging.getLogger(__name__)


class FallbackReason(str, Enum):
    """Reason why a fallback occurred."""
    NONE = "none"                    # Primary provider used
    POLICY_DENIED = "policy_denied"  # OPA denied this provider
    OVER_BUDGET = "over_budget"      # Cost tier exceeds budget
    UNHEALTHY = "unhealthy"          # Provider marked degraded/unavailable
    NOT_AVAILABLE = "not_available"  # Capability not registered
    USER_OVERRIDE = "user_override"  # User specified different provider


# Deterministic fallback ladders per modality/subtype
# Order matters: first item is primary, subsequent are fallbacks
FALLBACK_LADDERS: Dict[str, List[Tuple[str, str]]] = {
    # Diagram generation: prefer local tools, fallback to generative
    "image_diagram": [
        ("mermaid_diagram", "local"),      # Free, fast, precise
        ("plantuml_diagram", "local"),     # Free, UML specialist
        ("dalle3_image_gen", "openai"),    # Expensive but can interpret diagram requests
    ],
    # Photo-realistic image generation
    "image_photo": [
        ("dalle3_image_gen", "openai"),    # Highest quality
        ("stability_image_gen", "stability"),  # Lower cost alternative
    ],
    # Screenshot capture
    "screenshot": [
        ("playwright_screenshot", "local"),  # Primary: Playwright
    ],
    # Short video generation (future)
    "video_short": [
        # Runway and Pika to be added when available
    ],
    # Generic image (fallback category)
    "image": [
        ("dalle3_image_gen", "openai"),
        ("stability_image_gen", "stability"),
    ],
    # Generic diagram (fallback category)
    "diagram": [
        ("mermaid_diagram", "local"),
        ("plantuml_diagram", "local"),
    ],
}


@dataclass(slots=True)
class RoutingDecision:
    """Result of policy graph routing.
    
    Contains the selected capability and rationale for the decision,
    including the full fallback ladder considered.
    
    Attributes:
        capability: Selected CapabilityRecord (None if all options exhausted)
        tool_id: Selected tool identifier
        provider: Selected provider
        success: Whether routing succeeded
        fallback_reason: Why we used this option (NONE if primary)
        fallback_position: Position in ladder (0 = primary)
        ladder_considered: List of (tool_id, provider) tuples considered
        denied_options: List of (tool_id, provider, reason) tuples that were denied
        budget_remaining_cents: Remaining budget after this selection (if tracked)
        policy_context: Context passed to OPA for this decision
    """
    capability: Optional[CapabilityRecord] = None
    tool_id: Optional[str] = None
    provider: Optional[str] = None
    success: bool = False
    fallback_reason: FallbackReason = FallbackReason.NONE
    fallback_position: int = 0
    ladder_considered: List[Tuple[str, str]] = field(default_factory=list)
    denied_options: List[Tuple[str, str, str]] = field(default_factory=list)
    budget_remaining_cents: Optional[int] = None
    policy_context: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_primary(self) -> bool:
        """True if the primary (first) option was selected."""
        return self.fallback_position == 0 and self.success


class PolicyGraphRouter:
    """Routes multimodal requests through policy-controlled fallback ladders.
    
    Implements the "A" component from the multimodal architecture: deterministic
    fallback ladders with OPA policy integration for capability authorization
    and budget enforcement.
    
    The router:
    1. Determines the fallback ladder for the requested modality/subtype
    2. For each option in order:
       - Checks OPA policy (multimodal.capability.allow)
       - Checks cost tier against budget
       - Checks capability health status
    3. Returns first valid option, or failure if all exhausted
    
    Usage:
        router = PolicyGraphRouter()
        decision = await router.route(
            modality="image_diagram",
            tenant_id="acme-corp",
            persona_id="analyst",
            budget_limit_cents=500,
            user_override=None,  # User can force a specific provider
        )
        if decision.success:
            await tool_executor.execute(decision.tool_id, decision.provider, ...)
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        policy_client: Optional[PolicyClient] = None,
        dsn: Optional[str] = None,
    ) -> None:
        """Initialize router with capability registry and policy client.
        
        Args:
            registry: CapabilityRegistry instance. Created if not provided.
            policy_client: PolicyClient for OPA evaluation. Created if not provided.
            dsn: Database DSN for registry (if registry not provided).
        """
        self._registry = registry or CapabilityRegistry(dsn=dsn)
        self._policy_client = policy_client
        self._policy_initialized = False

    async def _get_policy_client(self) -> PolicyClient:
        """Lazy-initialize policy client."""
        if self._policy_client is None:
            self._policy_client = PolicyClient()
            self._policy_initialized = True
        return self._policy_client

    async def route(
        self,
        modality: str,
        tenant_id: str,
        persona_id: Optional[str] = None,
        budget_limit_cents: Optional[int] = None,
        budget_used_cents: int = 0,
        user_override: Optional[Tuple[str, str]] = None,
        context: Optional[Dict[str, Any]] = None,
        excluded_options: Optional[List[Tuple[str, str]]] = None,
    ) -> RoutingDecision:
        """Route a multimodal request to the best available capability.
        
        Evaluates the fallback ladder for the modality, applying OPA policy
        checks, budget constraints, and health status filtering.
        
        Args:
            modality: Modality/subtype key (e.g., 'image_diagram', 'image_photo')
            tenant_id: Tenant making the request
            persona_id: Optional persona ID for policy evaluation
            budget_limit_cents: Maximum budget in cents (None = unlimited)
            budget_used_cents: Budget already consumed
            user_override: Optional (tool_id, provider) to force selection
            context: Additional context for OPA policy evaluation
            excluded_options: List of (tool_id, provider) to skip (e.g. previous failures)
            
        Returns:
            RoutingDecision with selected capability or failure details
        """
        context = context or {}
        excluded_options = excluded_options or []
        ladder = self._get_fallback_ladder(modality)
        
        if not ladder:
            logger.warning("No fallback ladder for modality: %s", modality)
            return RoutingDecision(
                success=False,
                fallback_reason=FallbackReason.NOT_AVAILABLE,
                ladder_considered=[],
                policy_context={"modality": modality, **context},
            )

        # Handle user override
        if user_override:
            tool_id, provider = user_override
            return await self._try_with_override(
                tool_id=tool_id,
                provider=provider,
                tenant_id=tenant_id,
                persona_id=persona_id,
                budget_limit_cents=budget_limit_cents,
                budget_used_cents=budget_used_cents,
                ladder=ladder,
                context=context,
            )

        # Walk the fallback ladder
        denied_options: List[Tuple[str, str, str]] = []
        
        for position, (tool_id, provider) in enumerate(ladder):
            # Check exclusions
            if (tool_id, provider) in excluded_options:
                denied_options.append((tool_id, provider, "excluded_by_retry"))
                continue

            # Get capability from registry
            capability = await self._registry.get(tool_id, provider)
            
            if capability is None:
                denied_options.append((tool_id, provider, "not_registered"))
                continue
            
            if not capability.enabled:
                denied_options.append((tool_id, provider, "disabled"))
                continue

            # Check health status
            if capability.health_status == CapabilityHealth.UNAVAILABLE:
                denied_options.append((tool_id, provider, "unavailable"))
                continue

            # Check budget
            budget_ok, budget_reason = self._check_budget(
                capability=capability,
                budget_limit_cents=budget_limit_cents,
                budget_used_cents=budget_used_cents,
            )
            if not budget_ok:
                denied_options.append((tool_id, provider, budget_reason))
                continue

            # Check OPA policy
            policy_ok, policy_reason = await self._check_policy(
                tool_id=tool_id,
                provider=provider,
                tenant_id=tenant_id,
                persona_id=persona_id,
                modality=modality,
                context=context,
            )
            if not policy_ok:
                denied_options.append((tool_id, provider, policy_reason))
                continue

            # Success! Use this capability
            fallback_reason = (
                FallbackReason.NONE if position == 0
                else self._infer_fallback_reason(denied_options)
            )
            
            budget_remaining = None
            if budget_limit_cents is not None:
                estimated_cost = self._estimate_cost(capability)
                budget_remaining = budget_limit_cents - budget_used_cents - estimated_cost

            logger.info(
                "Routed %s to %s/%s (position=%d, reason=%s)",
                modality, tool_id, provider, position, fallback_reason.value
            )

            return RoutingDecision(
                capability=capability,
                tool_id=tool_id,
                provider=provider,
                success=True,
                fallback_reason=fallback_reason,
                fallback_position=position,
                ladder_considered=ladder,
                denied_options=denied_options,
                budget_remaining_cents=budget_remaining,
                policy_context={"modality": modality, **context},
            )

        # All options exhausted
        logger.warning(
            "All options exhausted for modality %s: %s",
            modality, denied_options
        )
        return RoutingDecision(
            success=False,
            fallback_reason=FallbackReason.NOT_AVAILABLE,
            ladder_considered=ladder,
            denied_options=denied_options,
            policy_context={"modality": modality, **context},
        )

    async def _try_with_override(
        self,
        tool_id: str,
        provider: str,
        tenant_id: str,
        persona_id: Optional[str],
        budget_limit_cents: Optional[int],
        budget_used_cents: int,
        ladder: List[Tuple[str, str]],
        context: Dict[str, Any],
    ) -> RoutingDecision:
        """Handle user-specified override."""
        capability = await self._registry.get(tool_id, provider)
        
        if capability is None:
            return RoutingDecision(
                success=False,
                fallback_reason=FallbackReason.NOT_AVAILABLE,
                ladder_considered=ladder,
                denied_options=[(tool_id, provider, "user_override_not_found")],
                policy_context=context,
            )

        # Still check policy and budget for override
        policy_ok, policy_reason = await self._check_policy(
            tool_id=tool_id,
            provider=provider,
            tenant_id=tenant_id,
            persona_id=persona_id,
            modality="user_override",
            context=context,
        )
        if not policy_ok:
            return RoutingDecision(
                success=False,
                fallback_reason=FallbackReason.POLICY_DENIED,
                ladder_considered=ladder,
                denied_options=[(tool_id, provider, policy_reason)],
                policy_context=context,
            )

        budget_ok, budget_reason = self._check_budget(
            capability=capability,
            budget_limit_cents=budget_limit_cents,
            budget_used_cents=budget_used_cents,
        )
        if not budget_ok:
            return RoutingDecision(
                success=False,
                fallback_reason=FallbackReason.OVER_BUDGET,
                ladder_considered=ladder,
                denied_options=[(tool_id, provider, budget_reason)],
                policy_context=context,
            )

        # Override accepted
        position = next(
            (i for i, (t, p) in enumerate(ladder) if t == tool_id and p == provider),
            -1
        )
        return RoutingDecision(
            capability=capability,
            tool_id=tool_id,
            provider=provider,
            success=True,
            fallback_reason=FallbackReason.USER_OVERRIDE,
            fallback_position=position if position >= 0 else 0,
            ladder_considered=ladder,
            denied_options=[],
            policy_context=context,
        )

    def _get_fallback_ladder(self, modality: str) -> List[Tuple[str, str]]:
        """Get the fallback ladder for a modality.
        
        Supports exact match and category fallback (e.g., 'image_diagram' -> 'image').
        """
        if modality in FALLBACK_LADDERS:
            return FALLBACK_LADDERS[modality]
        
        # Try category fallback (strip suffix after underscore)
        if "_" in modality:
            category = modality.split("_")[0]
            if category in FALLBACK_LADDERS:
                return FALLBACK_LADDERS[category]
        
        return []

    def _check_budget(
        self,
        capability: CapabilityRecord,
        budget_limit_cents: Optional[int],
        budget_used_cents: int,
    ) -> Tuple[bool, str]:
        """Check if capability fits within budget.
        
        Returns:
            Tuple of (is_ok, reason_if_not_ok)
        """
        if budget_limit_cents is None:
            return True, ""
        
        estimated_cost = self._estimate_cost(capability)
        remaining = budget_limit_cents - budget_used_cents
        
        if estimated_cost > remaining:
            return False, f"estimated_cost_{estimated_cost}_exceeds_remaining_{remaining}"
        
        return True, ""

    def _estimate_cost(self, capability: CapabilityRecord) -> int:
        """Estimate cost in cents based on cost tier.
        
        These are rough estimates for budget checking. Actual costs
        are recorded after execution from provider responses.
        """
        cost_estimates = {
            CostTier.FREE: 0,
            CostTier.LOW: 5,      # ~$0.05
            CostTier.MEDIUM: 20,  # ~$0.20
            CostTier.HIGH: 50,    # ~$0.50
            CostTier.PREMIUM: 100,  # ~$1.00
        }
        return cost_estimates.get(capability.cost_tier, 20)

    async def _check_policy(
        self,
        tool_id: str,
        provider: str,
        tenant_id: str,
        persona_id: Optional[str],
        modality: str,
        context: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """Check OPA policy for capability authorization.
        
        Returns:
            Tuple of (is_allowed, reason_if_denied)
        """
        try:
            policy_client = await self._get_policy_client()
            
            request = PolicyRequest(
                tenant=tenant_id,
                persona_id=persona_id,
                action="multimodal.capability.execute",
                resource=f"{tool_id}/{provider}",
                context={
                    "modality": modality,
                    "tool_id": tool_id,
                    "provider": provider,
                    **context,
                },
            )
            
            allowed = await policy_client.evaluate(request)
            
            if not allowed:
                return False, "opa_policy_denied"
            return True, ""
            
        except Exception as exc:
            # Policy client fail-closed behavior already returns False
            # Log and treat as denial
            logger.warning(
                "Policy evaluation failed for %s/%s: %s",
                tool_id, provider, exc
            )
            return False, f"policy_error_{type(exc).__name__}"

    def _infer_fallback_reason(
        self, 
        denied_options: List[Tuple[str, str, str]]
    ) -> FallbackReason:
        """Infer the primary reason for fallback from denied options."""
        if not denied_options:
            return FallbackReason.NONE
        
        # Check last denial reason
        _, _, reason = denied_options[-1]
        
        if "policy" in reason or "opa" in reason:
            return FallbackReason.POLICY_DENIED
        if "budget" in reason or "cost" in reason or "exceeds" in reason:
            return FallbackReason.OVER_BUDGET
        if "unavailable" in reason or "unhealthy" in reason:
            return FallbackReason.UNHEALTHY
        
        return FallbackReason.NOT_AVAILABLE

    def get_ladder(self, modality: str) -> List[Tuple[str, str]]:
        """Get the fallback ladder for introspection/debugging.
        
        Args:
            modality: Modality key
            
        Returns:
            List of (tool_id, provider) tuples in fallback order
        """
        return self._get_fallback_ladder(modality)
