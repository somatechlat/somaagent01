"""Capsule policy enforcement hooks.

Enforces capsule policies at runtime: egress/domain filtering, resource limits,
HITL requirements, and RL export restrictions.
"""

from __future__ import annotations

import fnmatch
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from enum import Enum


@dataclass
class CapsuleRecord:
    """Capsule policy record."""

    capsule_id: str
    egress_mode: str = "open"
    # Persona Identity (VIBE Rule: Agent Owns Identity)
    system_prompt: str = ""
    personality_traits: Dict[str, float] = field(default_factory=dict)
    neuromodulator_baseline: Dict[str, float] = field(default_factory=dict)
    allowed_domains: List[str] = field(default_factory=list)
    blocked_domains: List[str] = field(default_factory=list)
    max_wall_clock_seconds: int = 300
    max_concurrent_nodes: int = 10
    default_hitl_mode: str = "none"
    max_pending_hitl: int = 5
    risk_thresholds: Dict[str, float] = field(default_factory=dict)
    prohibited_tools: List[str] = field(default_factory=list)
    allowed_tools: Optional[List[str]] = None
    tool_risk_profile: str = "medium"
    rl_export_allowed: bool = True
    rl_export_scope: str = "tenant"
    rl_excluded_fields: List[str] = field(default_factory=list)
    example_store_policy: str = "allow"


class CapsuleStatus(str, Enum):
    """Status of a capsule."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"
    DISABLED = "disabled"


__all__ = [
    "EnforcementResult",
    "EnforcementAction",
    "CapsuleEnforcer",
    "EgressEnforcer",
    "ResourceEnforcer",
    "HITLEnforcer",
    "ExportEnforcer",
    "CapsuleStatus",
]


class EnforcementAction(str, Enum):
    """Action taken by enforcement hook."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_HITL = "require_hitl"
    WARN = "warn"


@dataclass
class EnforcementResult:
    """Result of an enforcement check."""

    action: EnforcementAction
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.action in {EnforcementAction.ALLOW, EnforcementAction.WARN}


class EgressEnforcer:
    """Enforces egress/domain policies for network requests."""

    def __init__(self, capsule: CapsuleRecord):
        self.capsule = capsule
        self.egress_mode = capsule.egress_mode
        self.allowed_domains = set(capsule.allowed_domains)
        self.blocked_domains = set(capsule.blocked_domains)

    def check_domain(self, domain: str) -> EnforcementResult:
        """Check if a domain is allowed for egress.

        Args:
            domain: Domain to check (e.g., "api.example.com")

        Returns:
            EnforcementResult with action and reason
        """
        # No egress allowed
        if self.egress_mode == "none":
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason=f"Egress blocked: mode is 'none'",
                details={"domain": domain, "egress_mode": self.egress_mode},
            )

        # Check blocked list first (explicit deny)
        for pattern in self.blocked_domains:
            if self._match_domain(domain, pattern):
                return EnforcementResult(
                    action=EnforcementAction.DENY,
                    reason=f"Domain {domain} is explicitly blocked by pattern: {pattern}",
                    details={"domain": domain, "blocked_pattern": pattern},
                )

        # Open mode allows all (except blocked)
        if self.egress_mode == "open":
            return EnforcementResult(
                action=EnforcementAction.ALLOW,
                reason="Egress allowed: mode is 'open'",
                details={"domain": domain},
            )

        # Restricted mode: must match allowed list
        if self.egress_mode == "restricted":
            for pattern in self.allowed_domains:
                if self._match_domain(domain, pattern):
                    return EnforcementResult(
                        action=EnforcementAction.ALLOW,
                        reason=f"Domain {domain} matches allowed pattern: {pattern}",
                        details={"domain": domain, "allowed_pattern": pattern},
                    )

            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason=f"Domain {domain} not in allowed list (restricted mode)",
                details={"domain": domain, "allowed_domains": list(self.allowed_domains)},
            )

        # Unknown mode - deny by default
        return EnforcementResult(
            action=EnforcementAction.DENY,
            reason=f"Unknown egress mode: {self.egress_mode}",
            details={"domain": domain},
        )

    def _match_domain(self, domain: str, pattern: str) -> bool:
        """Match domain against pattern (supports wildcards)."""
        # Handle wildcard patterns like *.example.com
        if pattern.startswith("*."):
            suffix = pattern[1:]  # .example.com
            return domain.endswith(suffix) or domain == pattern[2:]
        return fnmatch.fnmatch(domain, pattern)


class ResourceEnforcer:
    """Enforces resource limits: wall clock time, concurrency."""

    def __init__(self, capsule: CapsuleRecord):
        self.capsule = capsule
        self.max_wall_clock_seconds = capsule.max_wall_clock_seconds
        self.max_concurrent_nodes = capsule.max_concurrent_nodes
        self._start_time: Optional[float] = None
        self._active_nodes: int = 0

    def start(self) -> None:
        """Start timing for wall clock enforcement."""
        self._start_time = time.time()

    def check_wall_clock(self) -> EnforcementResult:
        """Check if wall clock limit exceeded."""
        if self._start_time is None:
            return EnforcementResult(action=EnforcementAction.ALLOW, reason="Timer not started")

        elapsed = time.time() - self._start_time
        if elapsed > self.max_wall_clock_seconds:
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason=f"Wall clock limit exceeded: {elapsed:.1f}s > {self.max_wall_clock_seconds}s",
                details={"elapsed": elapsed, "limit": self.max_wall_clock_seconds},
            )

        remaining = self.max_wall_clock_seconds - elapsed
        return EnforcementResult(
            action=EnforcementAction.ALLOW,
            reason=f"Within wall clock limit: {elapsed:.1f}s / {self.max_wall_clock_seconds}s",
            details={
                "elapsed": elapsed,
                "remaining": remaining,
                "limit": self.max_wall_clock_seconds,
            },
        )

    def check_concurrency(self, current_nodes: int) -> EnforcementResult:
        """Check if concurrency limit would be exceeded."""
        if current_nodes >= self.max_concurrent_nodes:
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason=f"Concurrency limit reached: {current_nodes} >= {self.max_concurrent_nodes}",
                details={"current": current_nodes, "limit": self.max_concurrent_nodes},
            )

        return EnforcementResult(
            action=EnforcementAction.ALLOW,
            reason=f"Within concurrency limit: {current_nodes} / {self.max_concurrent_nodes}",
            details={"current": current_nodes, "limit": self.max_concurrent_nodes},
        )

    def acquire_node(self) -> EnforcementResult:
        """Try to acquire a concurrent node slot."""
        result = self.check_concurrency(self._active_nodes)
        if result.allowed:
            self._active_nodes += 1
            return EnforcementResult(
                action=EnforcementAction.ALLOW,
                reason=f"Node acquired: {self._active_nodes} / {self.max_concurrent_nodes}",
                details={"active": self._active_nodes, "limit": self.max_concurrent_nodes},
            )
        return result

    def release_node(self) -> None:
        """Release a concurrent node slot."""
        if self._active_nodes > 0:
            self._active_nodes -= 1


class HITLEnforcer:
    """Enforces Human-in-the-Loop requirements."""

    def __init__(self, capsule: CapsuleRecord):
        self.capsule = capsule
        self.default_mode = capsule.default_hitl_mode
        self.max_pending = capsule.max_pending_hitl
        self.risk_thresholds = capsule.risk_thresholds
        self._pending_count: int = 0

    def check_action(
        self,
        action_type: str,
        risk_score: float = 0.0,
        tool_name: Optional[str] = None,
    ) -> EnforcementResult:
        """Check if action requires HITL approval.

        Args:
            action_type: Type of action (e.g., "tool_call", "code_exec")
            risk_score: Computed risk score for the action (0.0-1.0)
            tool_name: Name of tool being called (if applicable)

        Returns:
            EnforcementResult indicating if HITL is required
        """
        # Check if tool is in prohibited list
        if tool_name and tool_name in self.capsule.prohibited_tools:
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason=f"Tool '{tool_name}' is prohibited by capsule policy",
                details={"tool": tool_name, "prohibited_tools": self.capsule.prohibited_tools},
            )

        # HITL mode: none - never require approval
        if self.default_mode == "none":
            return EnforcementResult(
                action=EnforcementAction.ALLOW, reason="HITL mode is 'none' - no approval required"
            )

        # HITL mode: required - always require approval
        if self.default_mode == "required":
            if self._pending_count >= self.max_pending:
                return EnforcementResult(
                    action=EnforcementAction.DENY,
                    reason=f"Max pending HITL requests reached: {self._pending_count} >= {self.max_pending}",
                    details={"pending": self._pending_count, "max": self.max_pending},
                )
            return EnforcementResult(
                action=EnforcementAction.REQUIRE_HITL,
                reason="HITL mode is 'required' - approval needed",
                details={"action_type": action_type, "risk_score": risk_score},
            )

        # HITL mode: optional - check risk thresholds
        if self.default_mode == "optional":
            # Check if risk exceeds thresholds
            threshold = self.risk_thresholds.get(action_type, 0.7)
            if risk_score >= threshold:
                if self._pending_count >= self.max_pending:
                    return EnforcementResult(
                        action=EnforcementAction.DENY,
                        reason=f"High risk action, but max pending HITL reached",
                        details={"risk_score": risk_score, "threshold": threshold},
                    )
                return EnforcementResult(
                    action=EnforcementAction.REQUIRE_HITL,
                    reason=f"Risk score {risk_score:.2f} exceeds threshold {threshold:.2f}",
                    details={
                        "action_type": action_type,
                        "risk_score": risk_score,
                        "threshold": threshold,
                    },
                )

            return EnforcementResult(
                action=EnforcementAction.ALLOW,
                reason=f"Risk score {risk_score:.2f} below threshold {threshold:.2f}",
                details={"risk_score": risk_score, "threshold": threshold},
            )

        # Unknown mode - require HITL by default
        return EnforcementResult(
            action=EnforcementAction.REQUIRE_HITL, reason=f"Unknown HITL mode: {self.default_mode}"
        )

    def add_pending(self) -> bool:
        """Add a pending HITL request. Returns False if limit reached."""
        if self._pending_count >= self.max_pending:
            return False
        self._pending_count += 1
        return True

    def resolve_pending(self) -> None:
        """Resolve a pending HITL request."""
        if self._pending_count > 0:
            self._pending_count -= 1


class ExportEnforcer:
    """Enforces RL export restrictions."""

    def __init__(self, capsule: CapsuleRecord):
        self.capsule = capsule
        self.export_allowed = capsule.rl_export_allowed
        self.export_scope = capsule.rl_export_scope
        self.excluded_fields = set(capsule.rl_excluded_fields)
        self.example_store_policy = capsule.example_store_policy

    def check_export(self, scope: str = "tenant") -> EnforcementResult:
        """Check if RL export is allowed.

        Args:
            scope: Requested export scope ("tenant" or "global")
        """
        if not self.export_allowed:
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason="RL export is disabled for this capsule",
                details={"rl_export_allowed": False},
            )

        if scope == "global" and self.export_scope == "tenant":
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason="Global export not allowed (scope is tenant-only)",
                details={"requested_scope": scope, "allowed_scope": self.export_scope},
            )

        return EnforcementResult(
            action=EnforcementAction.ALLOW,
            reason=f"RL export allowed for scope: {scope}",
            details={"scope": scope},
        )

    def filter_export_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive fields from export data."""
        if not self.excluded_fields:
            return data

        return self._filter_recursive(data, self.excluded_fields)

    def _filter_recursive(self, data: Dict[str, Any], excluded: Set[str]) -> Dict[str, Any]:
        """Recursively filter excluded fields."""
        result = {}
        for key, value in data.items():
            if key in excluded:
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = self._filter_recursive(value, excluded)
            else:
                result[key] = value
        return result

    def get_store_policy(self) -> str:
        """Get the example store policy."""
        return self.example_store_policy


class CapsuleEnforcer:
    """Main enforcer combining all policy checks."""

    def __init__(self, capsule: CapsuleRecord):
        self.capsule = capsule
        self.egress = EgressEnforcer(capsule)
        self.resources = ResourceEnforcer(capsule)
        self.hitl = HITLEnforcer(capsule)
        self.export = ExportEnforcer(capsule)

    def start_execution(self) -> None:
        """Start execution tracking (wall clock timer)."""
        self.resources.start()

    def check_tool_call(
        self,
        tool_name: str,
        risk_score: float = 0.0,
        target_domain: Optional[str] = None,
    ) -> EnforcementResult:
        """Check if a tool call is allowed.

        Combines tool restrictions, HITL requirements, and egress policies.
        """
        # Check tool allowed
        if tool_name in self.capsule.prohibited_tools:
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason=f"Tool '{tool_name}' is prohibited",
                details={"tool": tool_name},
            )

        # If allowed_tools is specified, tool must be in list
        if self.capsule.allowed_tools and tool_name not in self.capsule.allowed_tools:
            return EnforcementResult(
                action=EnforcementAction.DENY,
                reason=f"Tool '{tool_name}' not in allowed list",
                details={"tool": tool_name, "allowed": self.capsule.allowed_tools},
            )

        # Check egress if domain specified
        if target_domain:
            egress_result = self.egress.check_domain(target_domain)
            if not egress_result.allowed:
                return egress_result

        # Check HITL requirements
        hitl_result = self.hitl.check_action(
            action_type="tool_call", risk_score=risk_score, tool_name=tool_name
        )

        return hitl_result
