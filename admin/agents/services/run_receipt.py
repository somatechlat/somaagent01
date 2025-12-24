"""RunReceipt - Immutable audit record for governed LLM transactions.

Production-grade receipt model for tracking AIQ scores, lane budgets,
and confidence metrics per turn.

VIBE COMPLIANT:
- Real implementations only (no mocks, no placeholders)
- Immutable dataclass for audit integrity
- No PII in receipt fields
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from admin.agents.services.agentiq_governor import GovernorDecision, TurnContext


# -----------------------------------------------------------------------------
# RunReceipt Model
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class RunReceipt:
    """Immutable record of a governed turn execution.
    
    Contains all information needed for audit, analytics, and debugging.
    No PII is stored in this record.
    
    Attributes:
        turn_id: Unique identifier for this turn
        session_id: Session this turn belongs to
        tenant_id: Tenant identifier
        capsule_id: Capsule used (if any)
        aiq_pred: Predicted AIQ score (0-100)
        aiq_obs: Observed AIQ score (0-100)
        confidence: LLM response confidence (0.0-1.0 or None)
        lane_budgets: Token budget per lane (planned)
        lane_actual: Actual tokens used per lane
        degradation_level: System degradation level at execution
        path_mode: Execution path (fast/rescue)
        tool_k: Number of tools allowed
        latency_ms: Governor overhead in milliseconds
        timestamp: Unix timestamp of execution
    """
    turn_id: str
    session_id: str
    tenant_id: str
    capsule_id: Optional[str]
    aiq_pred: float
    aiq_obs: float
    confidence: Optional[float]
    lane_budgets: Dict[str, int]
    lane_actual: Dict[str, int]
    degradation_level: str
    path_mode: str
    tool_k: int
    latency_ms: float
    timestamp: float

    def to_audit_event(self) -> Dict[str, Any]:
        """Convert to audit event dictionary for persistence.
        
        Returns:
            Dictionary suitable for JSON serialization and database storage.
        """
        return {
            "event_type": "run_receipt",
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "capsule_id": self.capsule_id,
            "aiq_pred": self.aiq_pred,
            "aiq_obs": self.aiq_obs,
            "confidence": self.confidence,
            "lane_budgets": self.lane_budgets,
            "lane_actual": self.lane_actual,
            "degradation_level": self.degradation_level,
            "path_mode": self.path_mode,
            "tool_k": self.tool_k,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for general serialization."""
        return {
            "turn_id": self.turn_id,
            "session_id": self.session_id,
            "tenant_id": self.tenant_id,
            "capsule_id": self.capsule_id,
            "aiq_pred": self.aiq_pred,
            "aiq_obs": self.aiq_obs,
            "confidence": self.confidence,
            "lane_budgets": self.lane_budgets,
            "lane_actual": self.lane_actual,
            "degradation_level": self.degradation_level,
            "path_mode": self.path_mode,
            "tool_k": self.tool_k,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RunReceipt":
        """Create RunReceipt from dictionary.
        
        Args:
            data: Dictionary with receipt fields
            
        Returns:
            RunReceipt instance
        """
        return cls(
            turn_id=data["turn_id"],
            session_id=data["session_id"],
            tenant_id=data["tenant_id"],
            capsule_id=data.get("capsule_id"),
            aiq_pred=float(data["aiq_pred"]),
            aiq_obs=float(data["aiq_obs"]),
            confidence=data.get("confidence"),
            lane_budgets=data["lane_budgets"],
            lane_actual=data["lane_actual"],
            degradation_level=data["degradation_level"],
            path_mode=data["path_mode"],
            tool_k=int(data["tool_k"]),
            latency_ms=float(data["latency_ms"]),
            timestamp=float(data["timestamp"]),
        )


# -----------------------------------------------------------------------------
# RunReceipt Builder
# -----------------------------------------------------------------------------

class RunReceiptBuilder:
    """Builder for creating RunReceipt instances.
    
    Provides a fluent interface for constructing receipts with
    validation and default values.
    """

    def __init__(self) -> None:
        self._turn_id: Optional[str] = None
        self._session_id: Optional[str] = None
        self._tenant_id: Optional[str] = None
        self._capsule_id: Optional[str] = None
        self._aiq_pred: float = 0.0
        self._aiq_obs: float = 0.0
        self._confidence: Optional[float] = None
        self._lane_budgets: Dict[str, int] = {}
        self._lane_actual: Dict[str, int] = {}
        self._degradation_level: str = "none"
        self._path_mode: str = "fast"
        self._tool_k: int = 0
        self._latency_ms: float = 0.0
        self._timestamp: Optional[float] = None

    def turn_id(self, value: str) -> "RunReceiptBuilder":
        """Set turn ID."""
        self._turn_id = value
        return self

    def session_id(self, value: str) -> "RunReceiptBuilder":
        """Set session ID."""
        self._session_id = value
        return self

    def tenant_id(self, value: str) -> "RunReceiptBuilder":
        """Set tenant ID."""
        self._tenant_id = value
        return self

    def capsule_id(self, value: Optional[str]) -> "RunReceiptBuilder":
        """Set capsule ID."""
        self._capsule_id = value
        return self

    def aiq_pred(self, value: float) -> "RunReceiptBuilder":
        """Set predicted AIQ score."""
        self._aiq_pred = max(0.0, min(100.0, value))
        return self

    def aiq_obs(self, value: float) -> "RunReceiptBuilder":
        """Set observed AIQ score."""
        self._aiq_obs = max(0.0, min(100.0, value))
        return self

    def confidence(self, value: Optional[float]) -> "RunReceiptBuilder":
        """Set confidence score."""
        if value is not None:
            self._confidence = max(0.0, min(1.0, value))
        else:
            self._confidence = None
        return self

    def lane_budgets(self, value: Dict[str, int]) -> "RunReceiptBuilder":
        """Set lane budgets."""
        self._lane_budgets = value.copy()
        return self

    def lane_actual(self, value: Dict[str, int]) -> "RunReceiptBuilder":
        """Set actual lane usage."""
        self._lane_actual = value.copy()
        return self

    def degradation_level(self, value: str) -> "RunReceiptBuilder":
        """Set degradation level."""
        self._degradation_level = value
        return self

    def path_mode(self, value: str) -> "RunReceiptBuilder":
        """Set path mode."""
        self._path_mode = value
        return self

    def tool_k(self, value: int) -> "RunReceiptBuilder":
        """Set tool_k."""
        self._tool_k = max(0, value)
        return self

    def latency_ms(self, value: float) -> "RunReceiptBuilder":
        """Set latency in milliseconds."""
        self._latency_ms = max(0.0, value)
        return self

    def timestamp(self, value: float) -> "RunReceiptBuilder":
        """Set timestamp."""
        self._timestamp = value
        return self

    def build(self) -> RunReceipt:
        """Build the RunReceipt instance.
        
        Returns:
            Immutable RunReceipt
            
        Raises:
            ValueError: If required fields are missing
        """
        # Generate defaults for missing required fields
        if self._turn_id is None:
            self._turn_id = str(uuid.uuid4())
        if self._session_id is None:
            raise ValueError("session_id is required")
        if self._tenant_id is None:
            raise ValueError("tenant_id is required")
        if self._timestamp is None:
            self._timestamp = time.time()

        return RunReceipt(
            turn_id=self._turn_id,
            session_id=self._session_id,
            tenant_id=self._tenant_id,
            capsule_id=self._capsule_id,
            aiq_pred=self._aiq_pred,
            aiq_obs=self._aiq_obs,
            confidence=self._confidence,
            lane_budgets=self._lane_budgets,
            lane_actual=self._lane_actual,
            degradation_level=self._degradation_level,
            path_mode=self._path_mode,
            tool_k=self._tool_k,
            latency_ms=self._latency_ms,
            timestamp=self._timestamp,
        )


# -----------------------------------------------------------------------------
# Factory function
# -----------------------------------------------------------------------------

def create_receipt_from_decision(
    decision: "GovernorDecision",
    turn_context: "TurnContext",
    lane_actual: Dict[str, int],
    confidence: Optional[float] = None,
    aiq_obs: float = 0.0,
) -> RunReceipt:
    """Create RunReceipt from GovernorDecision and execution results.
    
    Args:
        decision: GovernorDecision from govern() call
        turn_context: TurnContext used for the turn
        lane_actual: Actual token usage per lane
        confidence: LLM response confidence (if available)
        aiq_obs: Observed AIQ score (post-execution)
        
    Returns:
        RunReceipt for audit
    """
    return RunReceipt(
        turn_id=turn_context.turn_id,
        session_id=turn_context.session_id,
        tenant_id=turn_context.tenant_id,
        capsule_id=decision.capsule_id,
        aiq_pred=decision.aiq_score.predicted,
        aiq_obs=aiq_obs,
        confidence=confidence,
        lane_budgets=decision.lane_plan.to_dict(),
        lane_actual=lane_actual,
        degradation_level=decision.degradation_level.value,
        path_mode=decision.path_mode.value,
        tool_k=decision.tool_k,
        latency_ms=decision.latency_ms,
        timestamp=time.time(),
    )


__all__ = [
    "RunReceipt",
    "RunReceiptBuilder",
    "create_receipt_from_decision",
]
