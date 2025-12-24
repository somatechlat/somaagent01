"""
OPA Policy Adapter for Tool Execution
Per CANONICAL_REQUIREMENTS.md REQ-SEC-001, REQ-SEC-002, REQ-SEC-003

VIBE COMPLIANT:
- Real HTTP client to OPA
- Fail-closed security (REQ-SEC-002)
- Tenant/persona scoped policies (REQ-SEC-003)
- Prometheus metrics
- Circuit breaker pattern
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

import httpx
from prometheus_client import Counter, Histogram


LOGGER = logging.getLogger(__name__)

# Prometheus metrics
OPA_REQUESTS = Counter(
    "opa_policy_requests_total",
    "Total OPA policy evaluation requests",
    labelnames=("action", "resource", "decision"),
)
OPA_LATENCY = Histogram(
    "opa_policy_latency_seconds",
    "OPA policy evaluation latency",
    labelnames=("action",),
)


@dataclass
class PolicyDecision:
    """Result of an OPA policy evaluation."""
    allowed: bool
    reason: Optional[str] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    audit_id: Optional[str] = None


@dataclass
class PolicyContext:
    """Context for policy evaluation."""
    tenant_id: str
    user_id: Optional[str] = None
    persona_id: Optional[str] = None
    session_id: Optional[str] = None
    capsule_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class OPAPolicyAdapter:
    """
    Adapter for OPA policy enforcement in tool execution.
    
    Implements the PolicyPort interface from CANONICAL_DESIGN.md.
    All tool invocations MUST flow through this adapter per REQ-SEC-001.
    
    Security Model:
    - Fail-closed: If OPA is unavailable, deny the action (REQ-SEC-002)
    - Tenant-scoped: Policies filter by tenant_id and persona_id (REQ-SEC-003)
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 2.5,
        fail_open: bool = False,  # Default fail-closed per VIBE
    ):
        self.base_url = (
            base_url
            or os.getenv("SA01_OPA_URL")
            or os.getenv("SA01_SOMA_BASE_URL", "").rstrip("/")
        )
        if not self.base_url:
            raise ValueError(
                "OPA base URL required. Set SA01_OPA_URL or SA01_SOMA_BASE_URL. "
                "No hardcoded defaults per VIBE rules."
            )
        
        self.evaluate_url = f"{self.base_url}/v1/policy/evaluate"
        self.timeout = timeout
        self.fail_open = fail_open
        
        # Circuit breaker state
        self._cb_failures = 0
        self._cb_open_until = 0.0
        self._CB_THRESHOLD = 3
        self._CB_COOLDOWN_SEC = 15.0
    
    async def check_tool_access(
        self,
        tool_name: str,
        context: PolicyContext,
        tool_args: Optional[Mapping[str, Any]] = None,
    ) -> PolicyDecision:
        """
        Check if tool execution is allowed for the given context.
        
        Args:
            tool_name: Name of the tool to execute
            context: Policy evaluation context (tenant, user, roles, etc.)
            tool_args: Optional tool arguments for fine-grained policy
            
        Returns:
            PolicyDecision with allowed status and constraints
            
        Raises:
            PolicyDeniedError: If policy denies the action
            PolicyUnavailableError: If OPA is unavailable (fail-closed mode)
        """
        return await self._evaluate(
            action="tool.request",
            resource=tool_name,
            context=context,
            additional_input={"tool_args": dict(tool_args)} if tool_args else None,
        )
    
    async def check_action(
        self,
        action: str,
        resource: str,
        context: PolicyContext,
        additional_input: Optional[Mapping[str, Any]] = None,
    ) -> PolicyDecision:
        """
        Generic policy check for any action/resource pair.
        
        Args:
            action: Action type (e.g., "tool.request", "task.run", "delegate")
            resource: Resource identifier (tool name, task ID, etc.)
            context: Policy evaluation context
            additional_input: Additional data for policy evaluation
            
        Returns:
            PolicyDecision with allowed status
        """
        return await self._evaluate(action, resource, context, additional_input)
    
    async def _evaluate(
        self,
        action: str,
        resource: str,
        context: PolicyContext,
        additional_input: Optional[Mapping[str, Any]] = None,
    ) -> PolicyDecision:
        """Send evaluation request to OPA."""
        
        # Check circuit breaker
        now = time.time()
        if self._cb_open_until and now < self._cb_open_until:
            if self.fail_open:
                LOGGER.warning("OPA circuit open, fail-open mode: allowing")
                OPA_REQUESTS.labels(action, resource, "skipped").inc()
                return PolicyDecision(allowed=True, reason="circuit_open_failopen")
            LOGGER.error("OPA circuit open, fail-closed mode: denying")
            OPA_REQUESTS.labels(action, resource, "denied_circuit").inc()
            return PolicyDecision(allowed=False, reason="opa_unavailable_circuit_open")
        
        # Build request payload per soma.policy package
        payload = {
            "input": {
                "action": action,
                "resource": resource,
                "tenant": context.tenant_id,
                "tenant_id": context.tenant_id,  # Both formats for compatibility
                "user_id": context.user_id,
                "persona_id": context.persona_id,
                "session_id": context.session_id,
                "capsule_id": context.capsule_id,
                "roles": context.roles,
                **(additional_input or {}),
            }
        }
        
        start_ts = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.evaluate_url, json=payload)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            # Network/timeout error
            self._cb_failures += 1
            if self._cb_failures >= self._CB_THRESHOLD:
                self._cb_open_until = time.time() + self._CB_COOLDOWN_SEC
                LOGGER.warning(f"OPA circuit opened for {self._CB_COOLDOWN_SEC}s")
            
            duration = time.perf_counter() - start_ts
            OPA_LATENCY.labels(action).observe(duration)
            
            if self.fail_open:
                LOGGER.warning(f"OPA request failed, fail-open: {exc}")
                OPA_REQUESTS.labels(action, resource, "skipped").inc()
                return PolicyDecision(allowed=True, reason="opa_error_failopen")
            
            LOGGER.error(f"OPA request failed, fail-closed: {exc}")
            OPA_REQUESTS.labels(action, resource, "denied_error").inc()
            return PolicyDecision(allowed=False, reason=f"opa_unavailable: {exc}")
        
        # Success - reset circuit breaker
        self._cb_failures = 0
        self._cb_open_until = 0.0
        
        duration = time.perf_counter() - start_ts
        OPA_LATENCY.labels(action).observe(duration)
        
        # Parse response
        allowed = bool(data.get("allow", False))
        reason = data.get("reason") or data.get("message")
        constraints = data.get("constraints", {})
        
        decision = "allowed" if allowed else "denied"
        OPA_REQUESTS.labels(action, resource, decision).inc()
        
        LOGGER.debug(
            f"OPA decision: action={action} resource={resource} "
            f"tenant={context.tenant_id} allowed={allowed}"
        )
        
        return PolicyDecision(
            allowed=allowed,
            reason=reason,
            constraints=constraints,
        )
    
    async def batch_check(
        self,
        checks: Sequence[tuple[str, str, PolicyContext]],
    ) -> List[PolicyDecision]:
        """
        Batch policy check for multiple action/resource pairs.
        
        Args:
            checks: List of (action, resource, context) tuples
            
        Returns:
            List of PolicyDecision in same order as input
        """
        tasks = [
            self._evaluate(action, resource, context)
            for action, resource, context in checks
        ]
        return await asyncio.gather(*tasks)


class PolicyDeniedError(Exception):
    """Raised when policy denies an action."""
    
    def __init__(self, action: str, resource: str, reason: Optional[str] = None):
        self.action = action
        self.resource = resource
        self.reason = reason
        super().__init__(f"Policy denied {action} on {resource}: {reason or 'no reason given'}")


class PolicyUnavailableError(Exception):
    """Raised when OPA is unavailable in fail-closed mode."""
    
    def __init__(self, message: str = "OPA policy service unavailable"):
        super().__init__(message)


# Singleton instance
_adapter_instance: Optional[OPAPolicyAdapter] = None


def get_policy_adapter() -> OPAPolicyAdapter:
    """Get or create the singleton OPA policy adapter."""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = OPAPolicyAdapter()
    return _adapter_instance


__all__ = [
    "OPAPolicyAdapter",
    "PolicyContext",
    "PolicyDecision",
    "PolicyDeniedError",
    "PolicyUnavailableError",
    "get_policy_adapter",
]
