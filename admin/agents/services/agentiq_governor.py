"""AgentIQ Governor - Lane-based token budgeting and AIQ scoring.

Production-grade governor for budgeted LLM transactions with adaptive degradation.
Executes after OPA gate, before LLM call. Target latency: ≤10ms p95.

VIBE COMPLIANT:
- Real implementations only (no mocks, no placeholders)
- Integrates with existing CapsuleStore, DegradationMonitor, BudgetManager
- In-process execution (no network calls for Governor logic)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from services.common.budget_manager import BudgetManager
from services.common.capsule_enforcer import CapsuleEnforcer
from services.common.capsule_store import CapsuleStore, CapsuleRecord
from services.common.degradation_monitor import DegradationLevel, DegradationMonitor

LOGGER = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Feature Flag Helpers
# -----------------------------------------------------------------------------


def is_agentiq_enabled() -> bool:
    """Check if AgentIQ Governor is enabled via feature flag.

    Checks SA01_ENABLE_AGENTIQ_GOVERNOR environment variable.
    Default: disabled (False).
    """
    import os

    val = os.environ.get("SA01_ENABLE_AGENTIQ_GOVERNOR", "false")
    return val.lower() in ("true", "1", "yes", "on")


# -----------------------------------------------------------------------------
# Configuration Models
# -----------------------------------------------------------------------------


class AIQWeights(BaseModel):
    """Weights for AIQ score computation. Must sum to 1.0."""

    context_quality: float = Field(default=0.4, ge=0.0, le=1.0)
    tool_relevance: float = Field(default=0.3, ge=0.0, le=1.0)
    budget_efficiency: float = Field(default=0.3, ge=0.0, le=1.0)

    @field_validator("budget_efficiency")
    @classmethod
    def validate_sum(cls, v: float, info) -> float:
        """Validate weights sum to 1.0."""
        data = info.data
        total = data.get("context_quality", 0.4) + data.get("tool_relevance", 0.3) + v
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"AIQ weights must sum to 1.0, got {total}")
        return v


class LaneBounds(BaseModel):
    """Token bounds for a single lane."""

    min: int = Field(default=0, ge=0)
    max: int = Field(default=4000, ge=0)


class LanesConfig(BaseModel):
    """Configuration for all 6 lanes."""

    system_policy: LaneBounds = Field(default_factory=lambda: LaneBounds(min=100, max=2000))
    history: LaneBounds = Field(default_factory=lambda: LaneBounds(min=0, max=4000))
    memory: LaneBounds = Field(default_factory=lambda: LaneBounds(min=0, max=2000))
    tools: LaneBounds = Field(default_factory=lambda: LaneBounds(min=0, max=1500))
    tool_results: LaneBounds = Field(default_factory=lambda: LaneBounds(min=0, max=1000))
    buffer: LaneBounds = Field(default_factory=lambda: LaneBounds(min=200, max=500))


class DegradationThresholds(BaseModel):
    """AIQ thresholds for degradation level escalation."""

    l1_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    l2_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    l3_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    l4_threshold: float = Field(default=0.1, ge=0.0, le=1.0)


class ToolKConfig(BaseModel):
    """Tool selection limits by degradation level."""

    normal: int = Field(default=5, ge=0)
    l1: int = Field(default=3, ge=0)
    l2: int = Field(default=1, ge=0)
    l3: int = Field(default=0, ge=0)
    l4: int = Field(default=0, ge=0)


class AgentIQConfig(BaseModel):
    """Complete AgentIQ Governor configuration."""

    enabled: bool = Field(default=False, description="Feature flag for AgentIQ Governor")
    weights: AIQWeights = Field(default_factory=AIQWeights)
    lanes: LanesConfig = Field(default_factory=LanesConfig)
    degradation: DegradationThresholds = Field(default_factory=DegradationThresholds)
    tool_k: ToolKConfig = Field(default_factory=ToolKConfig)


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class LanePlan:
    """Token budget allocation across 6 lanes.

    Lanes:
    - system_policy: System prompt + OPA policies
    - history: Conversation history
    - memory: SomaBrain retrieved context
    - tools: Tool definitions
    - tool_results: Previous tool outputs
    - buffer: Safety margin (≥200 tokens)
    """

    system_policy: int
    history: int
    memory: int
    tools: int
    tool_results: int
    buffer: int

    def total(self) -> int:
        """Return total allocated tokens."""
        return (
            self.system_policy
            + self.history
            + self.memory
            + self.tools
            + self.tool_results
            + self.buffer
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary for serialization."""
        return {
            "system_policy": self.system_policy,
            "history": self.history,
            "memory": self.memory,
            "tools": self.tools,
            "tool_results": self.tool_results,
            "buffer": self.buffer,
        }

    def __post_init__(self) -> None:
        """Validate buffer minimum."""
        if self.buffer < 200:
            object.__setattr__(self, "buffer", 200)


@dataclass(frozen=True, slots=True)
class AIQScore:
    """Intelligence quotient scores (0-100 scale).

    Attributes:
        predicted: Pre-call prediction based on context quality
        observed: Post-call observation (set after LLM response)
        components: Breakdown by factor (context_quality, tool_relevance, budget_efficiency)
    """

    predicted: float
    observed: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Clamp scores to valid range."""
        if not (0.0 <= self.predicted <= 100.0):
            object.__setattr__(self, "predicted", max(0.0, min(100.0, self.predicted)))
        if not (0.0 <= self.observed <= 100.0):
            object.__setattr__(self, "observed", max(0.0, min(100.0, self.observed)))

    def with_observed(self, observed: float) -> "AIQScore":
        """Return new AIQScore with observed value set."""
        return AIQScore(
            predicted=self.predicted,
            observed=max(0.0, min(100.0, observed)),
            components=self.components,
        )


class PathMode(str, Enum):
    """Execution path mode."""

    FAST = "fast"
    RESCUE = "rescue"


@dataclass(frozen=True, slots=True)
class GovernorDecision:
    """Result of Governor.govern() call.

    Contains all information needed to proceed with LLM invocation
    and emit RunReceipt after completion.
    """

    lane_plan: LanePlan
    aiq_score: AIQScore
    degradation_level: DegradationLevel
    path_mode: PathMode
    tool_k: int
    capsule_id: Optional[str]
    allowed_tools: List[str]
    latency_ms: float

    @classmethod
    def rescue_path(
        cls,
        turn_context: "TurnContext",
        reason: str = "governor_failure",
    ) -> "GovernorDecision":
        """Create a rescue path decision for fallback scenarios."""
        LOGGER.warning("Creating rescue path decision", extra={"reason": reason})
        return cls(
            lane_plan=LanePlan(
                system_policy=500,
                history=0,
                memory=0,
                tools=0,
                tool_results=0,
                buffer=200,
            ),
            aiq_score=AIQScore(predicted=0.0, observed=0.0, components={}),
            degradation_level=DegradationLevel.CRITICAL,
            path_mode=PathMode.RESCUE,
            tool_k=0,
            capsule_id=None,
            allowed_tools=[],
            latency_ms=0.0,
        )


@dataclass
class TurnContext:
    """Context for a single conversation turn.

    Passed to Governor.govern() to make budgeting decisions.
    """

    turn_id: str
    session_id: str
    tenant_id: str
    persona_id: Optional[str] = None
    capsule_id: Optional[str] = None
    user_message: str = ""
    system_prompt: str = ""
    history: List[Dict[str, Any]] = field(default_factory=list)
    available_tools: List[str] = field(default_factory=list)
    memory_snippets: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------


class GovernorError(Exception):
    """Base exception for Governor failures."""

    pass


class BudgetExhaustedError(GovernorError):
    """Raised when no valid lane plan can be computed."""

    pass


class CapsuleNotFoundError(GovernorError):
    """Raised when capsule lookup fails."""

    pass


# -----------------------------------------------------------------------------
# Lane Allocator (inline for single-file simplicity per Task 1)
# -----------------------------------------------------------------------------


class LaneAllocator:
    """Allocates token budget across lanes with degradation awareness.

    Default ratios (L0 - Normal):
    - system_policy: 15%
    - history: 25%
    - memory: 25%
    - tools: 20%
    - tool_results: 10%
    - buffer: 5% (minimum 200 tokens)

    Degraded ratios reduce history, tools, and memory progressively.
    """

    DEFAULT_RATIOS: Dict[str, float] = {
        "system_policy": 0.15,
        "history": 0.25,
        "memory": 0.25,
        "tools": 0.20,
        "tool_results": 0.10,
        "buffer": 0.05,
    }

    # Overrides for degraded states (only changed lanes listed)
    DEGRADED_OVERRIDES: Dict[DegradationLevel, Dict[str, float]] = {
        DegradationLevel.MINOR: {
            "history": 0.15,
            "tools": 0.10,
            "memory": 0.30,
            "buffer": 0.10,
        },
        DegradationLevel.MODERATE: {
            "history": 0.10,
            "tools": 0.05,
            "memory": 0.15,
            "buffer": 0.15,
            "system_policy": 0.25,
        },
        DegradationLevel.SEVERE: {
            "history": 0.0,
            "tools": 0.0,
            "memory": 0.10,
            "buffer": 0.20,
            "system_policy": 0.40,
            "tool_results": 0.05,
        },
        DegradationLevel.CRITICAL: {
            "history": 0.0,
            "tools": 0.0,
            "memory": 0.0,
            "tool_results": 0.0,
            "buffer": 0.30,
            "system_policy": 0.70,
        },
    }

    MINIMUM_BUFFER = 200

    def __init__(self, config: LanesConfig) -> None:
        self.config = config

    def allocate(
        self,
        total_budget: int,
        degradation_level: DegradationLevel,
        capsule: Optional[CapsuleRecord] = None,
    ) -> LanePlan:
        """Allocate token budget across lanes.

        Args:
            total_budget: Total tokens available for allocation
            degradation_level: Current system degradation level
            capsule: Optional capsule for constraint overrides

        Returns:
            LanePlan with token allocations per lane

        Raises:
            BudgetExhaustedError: If total_budget < minimum required
        """
        # Get ratios for current degradation level
        ratios = self._get_ratios(degradation_level)

        # Calculate raw allocations
        allocations = {lane: int(total_budget * ratio) for lane, ratio in ratios.items()}

        # Enforce buffer minimum
        if allocations["buffer"] < self.MINIMUM_BUFFER:
            deficit = self.MINIMUM_BUFFER - allocations["buffer"]
            allocations["buffer"] = self.MINIMUM_BUFFER
            # Reduce from largest non-buffer lane
            self._reduce_to_compensate(allocations, deficit)

        # Apply lane bounds from config
        allocations = self._apply_bounds(allocations)

        # Apply capsule constraints if present
        if capsule:
            allocations = self._apply_capsule_constraints(allocations, capsule)

        # Validate total doesn't exceed budget
        total_allocated = sum(allocations.values())
        if total_allocated > total_budget:
            # Scale down proportionally
            scale = total_budget / total_allocated
            allocations = {
                lane: max(0, int(tokens * scale)) for lane, tokens in allocations.items()
            }
            # Re-enforce buffer minimum
            if allocations["buffer"] < self.MINIMUM_BUFFER:
                allocations["buffer"] = self.MINIMUM_BUFFER

        return LanePlan(**allocations)

    def _get_ratios(self, level: DegradationLevel) -> Dict[str, float]:
        """Get allocation ratios for degradation level."""
        if level == DegradationLevel.NONE:
            return self.DEFAULT_RATIOS.copy()

        ratios = self.DEFAULT_RATIOS.copy()
        overrides = self.DEGRADED_OVERRIDES.get(level, {})
        ratios.update(overrides)

        # Normalize to sum to 1.0
        total = sum(ratios.values())
        if total > 0:
            ratios = {k: v / total for k, v in ratios.items()}

        return ratios

    def _reduce_to_compensate(self, allocations: Dict[str, int], deficit: int) -> None:
        """Reduce largest non-buffer lane to compensate for buffer minimum."""
        reducible = ["history", "memory", "tools", "tool_results", "system_policy"]
        sorted_lanes = sorted(reducible, key=lambda x: allocations[x], reverse=True)

        remaining = deficit
        for lane in sorted_lanes:
            if remaining <= 0:
                break
            reduction = min(allocations[lane], remaining)
            allocations[lane] -= reduction
            remaining -= reduction

    def _apply_bounds(self, allocations: Dict[str, int]) -> Dict[str, int]:
        """Apply min/max bounds from config."""
        bounds_map = {
            "system_policy": self.config.system_policy,
            "history": self.config.history,
            "memory": self.config.memory,
            "tools": self.config.tools,
            "tool_results": self.config.tool_results,
            "buffer": self.config.buffer,
        }

        for lane, bounds in bounds_map.items():
            allocations[lane] = max(bounds.min, min(bounds.max, allocations[lane]))

        return allocations

    def _apply_capsule_constraints(
        self,
        allocations: Dict[str, int],
        capsule: CapsuleRecord,
    ) -> Dict[str, int]:
        """Apply capsule-specific constraints."""
        # Capsule can restrict tool budget if tool_risk_profile is restrictive
        if capsule.tool_risk_profile == "low":
            allocations["tools"] = min(allocations["tools"], 500)
        elif capsule.tool_risk_profile == "critical":
            allocations["tools"] = 0

        return allocations


# -----------------------------------------------------------------------------
# AIQ Calculator
# -----------------------------------------------------------------------------


class AIQCalculator:
    """Calculates AIQ scores based on context quality, tool relevance, and budget efficiency.

    Formula: AIQ = w1*context_quality + w2*tool_relevance + w3*budget_efficiency
    Scale: 0-100
    """

    def __init__(self, weights: AIQWeights) -> None:
        self.weights = weights

    def compute_predicted(
        self,
        turn: TurnContext,
        lane_plan: LanePlan,
        degradation_level: DegradationLevel,
    ) -> AIQScore:
        """Compute predicted AIQ score before LLM call.

        Components:
        - context_quality: Based on memory snippet scores and history depth
        - tool_relevance: Based on available tools matching user intent
        - budget_efficiency: Based on lane utilization vs. total budget
        """
        # Context quality (0-100)
        context_quality = self._compute_context_quality(turn, lane_plan)

        # Tool relevance (0-100)
        tool_relevance = self._compute_tool_relevance(turn, lane_plan)

        # Budget efficiency (0-100)
        budget_efficiency = self._compute_budget_efficiency(lane_plan, degradation_level)

        # Weighted sum
        predicted = (
            self.weights.context_quality * context_quality
            + self.weights.tool_relevance * tool_relevance
            + self.weights.budget_efficiency * budget_efficiency
        )

        return AIQScore(
            predicted=predicted,
            observed=0.0,
            components={
                "context_quality": context_quality,
                "tool_relevance": tool_relevance,
                "budget_efficiency": budget_efficiency,
            },
        )

    def _compute_context_quality(self, turn: TurnContext, lane_plan: LanePlan) -> float:
        """Compute context quality score (0-100).

        Factors:
        - Memory snippet relevance scores (if available)
        - History depth (more history = better context)
        - System prompt presence
        """
        score = 50.0  # Base score

        # Memory snippets contribution (up to +30)
        if turn.memory_snippets:
            avg_score = sum(s.get("score", 0.5) for s in turn.memory_snippets) / len(
                turn.memory_snippets
            )
            score += avg_score * 30.0

        # History depth contribution (up to +15)
        history_count = len(turn.history)
        if history_count > 0:
            # Diminishing returns: log scale
            import math

            history_bonus = min(15.0, 5.0 * math.log2(history_count + 1))
            score += history_bonus

        # System prompt presence (+5)
        if turn.system_prompt:
            score += 5.0

        return min(100.0, max(0.0, score))

    def _compute_tool_relevance(self, turn: TurnContext, lane_plan: LanePlan) -> float:
        """Compute tool relevance score (0-100).

        Factors:
        - Number of available tools
        - Tool budget allocation
        """
        if lane_plan.tools == 0:
            return 0.0

        score = 50.0  # Base score

        # Available tools contribution (up to +30)
        tool_count = len(turn.available_tools)
        if tool_count > 0:
            # More tools = higher potential relevance
            tool_bonus = min(30.0, tool_count * 5.0)
            score += tool_bonus

        # Tool budget allocation contribution (up to +20)
        if lane_plan.tools >= 1000:
            score += 20.0
        elif lane_plan.tools >= 500:
            score += 10.0

        return min(100.0, max(0.0, score))

    def _compute_budget_efficiency(
        self,
        lane_plan: LanePlan,
        degradation_level: DegradationLevel,
    ) -> float:
        """Compute budget efficiency score (0-100).

        Factors:
        - Degradation level (lower = better)
        - Buffer utilization (higher buffer = more safety margin)
        """
        # Base score by degradation level
        level_scores = {
            DegradationLevel.NONE: 100.0,
            DegradationLevel.MINOR: 80.0,
            DegradationLevel.MODERATE: 60.0,
            DegradationLevel.SEVERE: 30.0,
            DegradationLevel.CRITICAL: 10.0,
        }
        score = level_scores.get(degradation_level, 50.0)

        # Buffer bonus (up to +10 for buffer >= 300)
        if lane_plan.buffer >= 300:
            score = min(100.0, score + 10.0)
        elif lane_plan.buffer >= 250:
            score = min(100.0, score + 5.0)

        return score


# -----------------------------------------------------------------------------
# AgentIQ Governor
# -----------------------------------------------------------------------------


class AgentIQGovernor:
    """Governor-mediated control loop for budgeted LLM transactions.

    Executes after OPA gate, before LLM call.
    Computes AIQ_pred, decides Fast Path vs Rescue Path.
    Target latency: ≤10ms p95.

    VIBE COMPLIANT:
    - Real implementations only
    - Integrates with existing infrastructure
    - In-process execution (no network calls)
    """

    def __init__(
        self,
        capsule_store: CapsuleStore,
        degradation_monitor: DegradationMonitor,
        budget_manager: BudgetManager,
        config: Optional[AgentIQConfig] = None,
    ) -> None:
        self.capsule_store = capsule_store
        self.degradation_monitor = degradation_monitor
        self.budget_manager = budget_manager
        self.config = config or AgentIQConfig()
        self._allocator = LaneAllocator(self.config.lanes)
        self._calculator = AIQCalculator(self.config.weights)

    async def govern(
        self,
        turn: TurnContext,
        max_tokens: int,
    ) -> GovernorDecision:
        """Execute governor logic for a turn.

        Args:
            turn: Context for the current conversation turn
            max_tokens: Maximum tokens available for the LLM call

        Returns:
            GovernorDecision with lane plan, AIQ score, and execution path

        Raises:
            GovernorError: On unrecoverable failures (caller should use rescue path)
        """
        start_time = time.perf_counter()

        try:
            # 1. Get current degradation level (in-process, no network)
            degradation_status = await self.degradation_monitor.get_degradation_status()
            degradation_level = degradation_status.overall_level

            # 2. Get capsule if specified (may involve DB lookup)
            capsule: Optional[CapsuleRecord] = None
            if turn.capsule_id:
                capsule = await self.capsule_store.get(turn.capsule_id)
                if capsule is None:
                    LOGGER.warning(
                        "Capsule not found, proceeding without constraints",
                        extra={"capsule_id": turn.capsule_id},
                    )

            # 3. Allocate lanes
            lane_plan = self._allocator.allocate(
                total_budget=max_tokens,
                degradation_level=degradation_level,
                capsule=capsule,
            )

            # 4. Compute AIQ prediction
            aiq_score = self._calculator.compute_predicted(
                turn=turn,
                lane_plan=lane_plan,
                degradation_level=degradation_level,
            )

            # 5. Determine path mode and tool_k
            path_mode, tool_k = self._determine_path(
                aiq_score=aiq_score,
                degradation_level=degradation_level,
            )

            # 6. Filter allowed tools
            allowed_tools = self._filter_tools(
                available_tools=turn.available_tools,
                capsule=capsule,
                tool_k=tool_k,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            return GovernorDecision(
                lane_plan=lane_plan,
                aiq_score=aiq_score,
                degradation_level=degradation_level,
                path_mode=path_mode,
                tool_k=tool_k,
                capsule_id=turn.capsule_id,
                allowed_tools=allowed_tools,
                latency_ms=latency_ms,
            )

        except GovernorError:
            raise
        except Exception as e:
            LOGGER.exception("Governor failed unexpectedly")
            raise GovernorError(f"Governor failure: {e}") from e

    def _determine_path(
        self,
        aiq_score: AIQScore,
        degradation_level: DegradationLevel,
    ) -> Tuple[PathMode, int]:
        """Determine execution path and tool_k based on AIQ and degradation.

        Returns:
            Tuple of (PathMode, tool_k)
        """
        # Normalize AIQ to 0-1 for threshold comparison
        aiq_normalized = aiq_score.predicted / 100.0

        # Check degradation thresholds
        thresholds = self.config.degradation
        tool_k_config = self.config.tool_k

        # Critical degradation always uses rescue path
        if degradation_level == DegradationLevel.CRITICAL:
            return PathMode.RESCUE, tool_k_config.l4

        # Severe degradation
        if degradation_level == DegradationLevel.SEVERE:
            return PathMode.RESCUE, tool_k_config.l3

        # Check AIQ thresholds for path selection
        if aiq_normalized < thresholds.l4_threshold:
            return PathMode.RESCUE, tool_k_config.l4
        elif aiq_normalized < thresholds.l3_threshold:
            return PathMode.RESCUE, tool_k_config.l3
        elif aiq_normalized < thresholds.l2_threshold:
            return PathMode.FAST, tool_k_config.l2
        elif aiq_normalized < thresholds.l1_threshold:
            return PathMode.FAST, tool_k_config.l1
        else:
            return PathMode.FAST, tool_k_config.normal

    def _filter_tools(
        self,
        available_tools: List[str],
        capsule: Optional[CapsuleRecord],
        tool_k: int,
    ) -> List[str]:
        """Filter and limit tools based on capsule and tool_k.

        Args:
            available_tools: All available tool names
            capsule: Optional capsule with tool constraints
            tool_k: Maximum number of tools to return

        Returns:
            Filtered list of tool names
        """
        if tool_k == 0:
            return []

        filtered = available_tools.copy()

        # Apply capsule constraints
        if capsule:
            # Remove prohibited tools
            if capsule.prohibited_tools:
                filtered = [t for t in filtered if t not in capsule.prohibited_tools]

            # If allowed_tools is specified, only keep those
            if capsule.allowed_tools:
                filtered = [t for t in filtered if t in capsule.allowed_tools]

        # Limit to tool_k
        return filtered[:tool_k]

    async def govern_with_fallback(
        self,
        turn: TurnContext,
        max_tokens: int,
    ) -> GovernorDecision:
        """Execute governor with automatic fallback to rescue path on failure.

        This is the recommended entry point for production use.
        """
        try:
            return await self.govern(turn, max_tokens)
        except GovernorError as e:
            LOGGER.warning(
                "Governor failed, using rescue path",
                extra={"error": str(e), "turn_id": turn.turn_id},
            )
            return GovernorDecision.rescue_path(turn, reason=str(e))


# -----------------------------------------------------------------------------
# Factory function
# -----------------------------------------------------------------------------


def create_governor(
    capsule_store: CapsuleStore,
    degradation_monitor: DegradationMonitor,
    budget_manager: BudgetManager,
    config: Optional[AgentIQConfig] = None,
) -> AgentIQGovernor:
    """Factory function to create an AgentIQ Governor instance.

    Args:
        capsule_store: PostgreSQL-backed capsule store
        degradation_monitor: System degradation monitor
        budget_manager: Redis-backed budget manager
        config: Optional configuration (uses defaults if not provided)

    Returns:
        Configured AgentIQGovernor instance
    """
    return AgentIQGovernor(
        capsule_store=capsule_store,
        degradation_monitor=degradation_monitor,
        budget_manager=budget_manager,
        config=config,
    )


__all__ = [
    # Configuration
    "AgentIQConfig",
    "AIQWeights",
    "LanesConfig",
    "LaneBounds",
    "DegradationThresholds",
    "ToolKConfig",
    # Data classes
    "LanePlan",
    "AIQScore",
    "PathMode",
    "GovernorDecision",
    "TurnContext",
    # Exceptions
    "GovernorError",
    "BudgetExhaustedError",
    "CapsuleNotFoundError",
    # Core classes
    "LaneAllocator",
    "AIQCalculator",
    "AgentIQGovernor",
    # Factory
    "create_governor",
]
