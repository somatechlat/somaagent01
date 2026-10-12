"""Typed decision contracts for Cloudflare Clef (Jev-compatible System One).

Signal split (BINDING):
    noul -> p_safe · score -> risk · confidence -> entropy confidence
Decision-facts go to THE BRAIN only (T-1). No local store.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, UTC
from typing import Any, Literal

from pydantic import BaseModel, Field

Caller = Literal["v3", "conversation_worker", "temporal"]
DecisionCategory = Literal["guardrail", "router", "triage", "escalation"]
DecisionOutcome = Literal["allow", "approval_required", "denied", "advisory"]
Mode = Literal["noul", "score", "choice"]


class ClefConfigurationError(RuntimeError):
    """Required Clef seam setting or credential is missing (fail-closed)."""


class ClefDisabledError(RuntimeError):
    """Feature flag off. Callers must not pretend a decision was made."""


class ClefDecisionError(RuntimeError):
    """Clef could not produce a validated answer (down / timeout / schema break)."""


def caller_values() -> tuple[str, ...]:
    return ("v3", "conversation_worker", "temporal")


def decision_fact_namespace(category: DecisionCategory) -> str:
    return f"clef.decisions.{category}"


def input_state_digest(state: Any) -> str:
    raw = json.dumps(state, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


class DecisionPayload(BaseModel):
    choice: str | None = None
    score: float | None = None
    noul: float | None = None
    probabilities: dict[str, float] | None = None
    confidence: float | None = None


class DecisionSignals(BaseModel):
    """Split signals. p_safe is NEVER confidence (C-1)."""

    p_safe: float | None = None
    risk: float | None = None
    confidence: float | None = None
    choice: str | None = None
    choice_probabilities: dict[str, float] | None = None
    score_probabilities: dict[str, float] | None = None


class DecisionFact(BaseModel):
    """One decision that must survive in THE BRAIN."""

    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    trace_id: str | None = None
    mode: Mode
    question_id: str
    payload: DecisionPayload
    input_state_digest: str
    caller: Caller
    model_id: str
    latency_ms: float
    outcome: DecisionOutcome
    opa_decision_ref: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ClefAnswer(BaseModel):
    """One Clef/Jev answer. Extra provider fields are ignored."""

    type: Literal["noul", "score", "choice"]
    noul: float | None = None
    score: float | None = None
    choice: str | None = None
    probabilities: dict[str, float] | None = None
    confidence: float | None = None
    legend: dict[str, str] | None = None


class ClefResponse(BaseModel):
    model: str = ""
    answers: dict[str, ClefAnswer] = Field(default_factory=dict)
    latency_ms: float | None = None
    usage: dict[str, Any] | None = None


def map_answers_to_signals(answers: dict[str, Any]) -> DecisionSignals:
    """Map Clef/Jev answers to split signals (noul != confidence)."""
    p_safe = risk = confidence = choice = None
    choice_probs = score_probs = None
    for ans in answers.values():
        if isinstance(ans, ClefAnswer):
            kind = ans.type
            if kind == "noul" and ans.noul is not None:
                p_safe = float(ans.noul)
            elif kind == "score":
                if ans.score is not None:
                    risk = float(ans.score)
                score_probs = ans.probabilities
                if ans.confidence is not None:
                    confidence = float(ans.confidence)
            elif kind == "choice":
                choice = ans.choice
                choice_probs = ans.probabilities
                if ans.confidence is not None and confidence is None:
                    confidence = float(ans.confidence)
        elif isinstance(ans, dict):
            kind = str(ans.get("type") or "")
            if kind == "noul" and ans.get("noul") is not None:
                p_safe = float(ans["noul"])
            elif kind == "score":
                if ans.get("score") is not None:
                    risk = float(ans["score"])
                score_probs = ans.get("probabilities")
                if ans.get("confidence") is not None:
                    confidence = float(ans["confidence"])
            elif kind == "choice":
                choice = ans.get("choice")
                choice_probs = ans.get("probabilities")
                if ans.get("confidence") is not None and confidence is None:
                    confidence = float(ans["confidence"])
    return DecisionSignals(
        p_safe=p_safe,
        risk=risk,
        confidence=confidence,
        choice=choice,
        choice_probabilities=choice_probs,
        score_probabilities=score_probs,
    )


def outcome_from_signals(
    signals: DecisionSignals, *, tier: int
) -> DecisionOutcome:
    """First-ship thresholds (fail-closed; tier-3 never auto-allow)."""
    if signals.p_safe is None:
        return "denied" if tier >= 3 else "approval_required"
    if tier >= 3:
        return "approval_required"
    if signals.risk is not None and signals.risk >= 2:
        return "approval_required"
    if signals.p_safe < 0.30:
        return "denied" if tier >= 3 else "approval_required"
    if signals.p_safe < 0.70:
        return "approval_required"
    return "allow"


def should_flag(signals: DecisionSignals, *, min_acceptance: float = 0.5) -> bool:
    if signals.confidence is None:
        return signals.p_safe is None
    return signals.confidence < min_acceptance


__all__ = [
    "ClefAnswer",
    "ClefConfigurationError",
    "ClefDecisionError",
    "ClefDisabledError",
    "ClefResponse",
    "DecisionCategory",
    "DecisionFact",
    "DecisionOutcome",
    "DecisionPayload",
    "DecisionSignals",
    "caller_values",
    "decision_fact_namespace",
    "input_state_digest",
    "map_answers_to_signals",
    "outcome_from_signals",
    "should_flag",
]
