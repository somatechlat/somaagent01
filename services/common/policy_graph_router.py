"""Policy Graph Router for multimodal capability selection.

Selects a single capability per modality with OPA policy integration
and budget enforcement. Used by the ToolExecutor to select providers
for multimodal requests.

SRS Reference: Section 16.3 (Policy Graph Router)
Feature Flag: SA01_ENABLE_multimodal_capabilities
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from services.common.capability_registry import (
    CapabilityRecord,
    CapabilityRegistry,
    CapabilityHealth,
    CostTier,
)
from services.common.policy_client import PolicyClient, PolicyRequest

__all__ = [
    "PolicyGraphRouter",
    "RoutingDecision",
]

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RoutingDecision:
    """Result of policy graph routing.

    Attributes:
        capability: Selected CapabilityRecord (None if no option available)
        tool_id: Selected tool identifier
        provider: Selected provider
        success: Whether routing succeeded
        denied_options: List of (tool_id, provider, reason) tuples that were denied
        budget_remaining_cents: Remaining budget after this selection (if tracked)
        policy_context: Context passed to OPA for this decision
    """

    capability: Optional[CapabilityRecord] = None
    tool_id: Optional[str] = None
    provider: Optional[str] = None
    success: bool = False
    denied_options: List[Tuple[str, str, str]] = field(default_factory=list)
    budget_remaining_cents: Optional[int] = None
    policy_context: Dict[str, Any] = field(default_factory=dict)


class PolicyGraphRouter:
    """Routes multimodal requests through policy-controlled selection.

    The router:
    1. Queries the capability registry for matching modality candidates
    2. Checks budget constraints
    3. Evaluates OPA policy
    4. Returns the first valid option
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        policy_client: Optional[PolicyClient] = None,
        dsn: Optional[str] = None,
    ) -> None:
        self._registry = registry or CapabilityRegistry(dsn=dsn)
        self._policy_client = policy_client
        self._policy_initialized = False

    async def ensure_schema(self) -> None:
        """Ensure the capability registry schema exists."""
        await self._registry.ensure_schema()

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
        context: Optional[Dict[str, Any]] = None,
    ) -> RoutingDecision:
        """Route a multimodal request to the best available capability.

        Args:
            modality: Modality/subtype key (e.g., 'image_diagram', 'image_photo')
            tenant_id: Tenant making the request
            persona_id: Optional persona ID for policy evaluation
            budget_limit_cents: Maximum budget in cents (None = unlimited)
            budget_used_cents: Budget already consumed
            context: Additional context for OPA policy evaluation

        Returns:
            RoutingDecision with selected capability or failure details
        """
        context = context or {}

        candidates = await self._registry.find_candidates(
            modality=modality,
            tenant_id=tenant_id,
            include_unhealthy=False,
        )

        if not candidates:
            logger.warning("No capability candidates for modality: %s", modality)
            return RoutingDecision(
                success=False,
                denied_options=[],
                policy_context={"modality": modality, **context},
            )

        denied_options: List[Tuple[str, str, str]] = []

        for capability in candidates:
            tool_id = capability.tool_id
            provider = capability.provider

            if not capability.enabled:
                denied_options.append((tool_id, provider, "disabled"))
                continue

            if capability.health_status == CapabilityHealth.UNAVAILABLE:
                denied_options.append((tool_id, provider, "unavailable"))
                continue

            estimated_cost = self._estimate_cost(capability)
            budget_ok, budget_reason = self._check_budget(
                capability=capability,
                budget_limit_cents=budget_limit_cents,
                budget_used_cents=budget_used_cents,
            )
            if not budget_ok:
                denied_options.append((tool_id, provider, budget_reason))
                continue

            policy_context = {
                "modality": modality,
                "tool_id": tool_id,
                "provider": provider,
                "cost_tier": capability.cost_tier.value,
                "estimated_cost_cents": estimated_cost,
                **context,
            }
            if budget_limit_cents is not None:
                policy_context["budget_limit_cents"] = budget_limit_cents
                policy_context["budget_used_cents"] = budget_used_cents
                policy_context["budget_remaining_cents"] = budget_limit_cents - budget_used_cents

            policy_ok, policy_reason = await self._check_policy(
                tool_id=tool_id,
                provider=provider,
                tenant_id=tenant_id,
                persona_id=persona_id,
                policy_context=policy_context,
            )
            if not policy_ok:
                denied_options.append((tool_id, provider, policy_reason))
                continue

            budget_remaining = None
            if budget_limit_cents is not None:
                budget_remaining = budget_limit_cents - budget_used_cents - estimated_cost

            logger.info(
                "Routed %s to %s/%s",
                modality,
                tool_id,
                provider,
            )

            return RoutingDecision(
                capability=capability,
                tool_id=tool_id,
                provider=provider,
                success=True,
                denied_options=denied_options,
                budget_remaining_cents=budget_remaining,
                policy_context=policy_context,
            )

        logger.warning(
            "No eligible capability for modality %s: %s",
            modality,
            denied_options,
        )
        return RoutingDecision(
            success=False,
            denied_options=denied_options,
            policy_context={"modality": modality, **context},
        )

    def _check_budget(
        self,
        capability: CapabilityRecord,
        budget_limit_cents: Optional[int],
        budget_used_cents: int,
    ) -> Tuple[bool, str]:
        """Check if capability fits within budget."""
        if budget_limit_cents is None:
            return True, ""

        estimated_cost = self._estimate_cost(capability)
        remaining = budget_limit_cents - budget_used_cents

        if estimated_cost > remaining:
            return False, f"estimated_cost_{estimated_cost}_exceeds_remaining_{remaining}"

        return True, ""

    def _estimate_cost(self, capability: CapabilityRecord) -> int:
        """Estimate cost in cents based on cost tier."""
        cost_estimates = {
            CostTier.FREE: 0,
            CostTier.LOW: 5,
            CostTier.MEDIUM: 20,
            CostTier.HIGH: 50,
            CostTier.PREMIUM: 100,
        }
        return cost_estimates.get(capability.cost_tier, 20)

    async def _check_policy(
        self,
        tool_id: str,
        provider: str,
        tenant_id: str,
        persona_id: Optional[str],
        policy_context: Dict[str, Any],
    ) -> Tuple[bool, str]:
        """Check OPA policy for capability authorization."""
        try:
            policy_client = await self._get_policy_client()

            request = PolicyRequest(
                tenant=tenant_id,
                persona_id=persona_id,
                action="multimodal.capability.execute",
                resource=f"{tool_id}/{provider}",
                context=policy_context,
            )

            allowed = await policy_client.evaluate(request)

            if not allowed:
                return False, "opa_policy_denied"
            return True, ""

        except Exception as exc:
            logger.warning(
                "Policy evaluation failed for %s/%s: %s",
                tool_id,
                provider,
                exc,
            )
            return False, f"policy_error_{type(exc).__name__}"
