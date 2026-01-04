"""Escalation heuristics and helpers for SomaAgent 01."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping


@dataclass
class EscalationDecision:
    """Escalationdecision class implementation."""

    should_escalate: bool
    reason: str
    metadata: Dict[str, Any]


HIGH_RISK_LEVELS = {"high", "critical"}
HIGH_COMPLEXITY = {"advanced", "severe"}
DEFAULT_TAG_WEIGHT = {"code": 0.4, "infrastructure": 0.4, "testing": 0.2}


def _score_from_tags(tags: list[str]) -> float:
    """Execute score from tags.

        Args:
            tags: The tags.
        """

    score = 0.0
    for tag in tags:
        score += DEFAULT_TAG_WEIGHT.get(tag, 0.1)
    return score


def should_escalate(
    message: str,
    analysis: Mapping[str, Any],
    event_metadata: Mapping[str, Any],
) -> EscalationDecision:
    """Return whether the message should be escalated to the LLM tier.

    The heuristic balances explicit metadata flags with lightweight semantic
    signals from the conversation pre-processor.  It is intentionally
    conservative—the default behaviour keeps the request on the baseline tier unless
    multiple indicators point to higher risk/complexity.
    """

    override = event_metadata.get("escalate")
    if isinstance(override, bool):
        return EscalationDecision(
            should_escalate=override,
            reason="metadata_override_true" if override else "metadata_override_false",
            metadata={"source": "metadata", "override": override},
        )

    priority = str(event_metadata.get("priority", "")).lower() or "normal"
    risk = str(event_metadata.get("risk_level", "")).lower() or "low"
    complexity = str(event_metadata.get("complexity", "")).lower() or "baseline"

    intent = str(analysis.get("intent", "")).lower()
    sentiment = str(analysis.get("sentiment", "")).lower()
    tags = list(analysis.get("tags", []))
    tag_score = _score_from_tags(tags)

    length = len(message or "")
    factors: dict[str, Any] = {
        "priority": priority,
        "risk_level": risk,
        "complexity": complexity,
        "intent": intent,
        "sentiment": sentiment,
        "tags": tags,
        "message_length": length,
        "tag_score": tag_score,
    }

    if risk in HIGH_RISK_LEVELS:
        return EscalationDecision(
            should_escalate=True,
            reason="risk_level_high",
            metadata=factors,
        )

    if complexity in HIGH_COMPLEXITY and tag_score >= 0.5:
        return EscalationDecision(
            should_escalate=True,
            reason="complexity_high_tag_signal",
            metadata=factors,
        )

    if priority == "urgent" and (tag_score >= 0.6 or length > 750):
        return EscalationDecision(
            should_escalate=True,
            reason="priority_urgent_long_content",
            metadata=factors,
        )

    if intent in {"action_request", "problem_report"} and tag_score >= 0.8 and length > 600:
        return EscalationDecision(
            should_escalate=True,
            reason="intent_complex_high_tag",
            metadata=factors,
        )

    # Production uses explicit escalation criteria only

    return EscalationDecision(
        should_escalate=False,
        reason="baseline_handled",
        metadata=factors,
    )