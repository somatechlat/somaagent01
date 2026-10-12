"""Clef tool-guardrail choke (D-1/D-2) — p_safe + risk on one tool boundary.

Used by chat AND Kafka AND Temporal via ONE helper. JEV-shaped questions to
Clef; signals split (noul=p_safe). JEV/Clef may only tighten. Flag off/unset
tightens tier-3 to approval_required — never legacy allow.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from services.common.decisions.contracts import (
    ClefConfigurationError,
    ClefDecisionError,
    ClefDisabledError,
    DecisionSignals,
    should_flag,
)
from services.common.decisions.decision_client import (
    DecisionClient,
    clef_flag_enabled,
    get_decision_client,
)

LOGGER = logging.getLogger(__name__)

TIER3_TOOLS: frozenset[str] = frozenset(
    {"packages_ensure", "os_packages_ensure", "code_execute", "shell_exec"}
)
TIER2_TOOLS: frozenset[str] = frozenset(
    {
        "file_write",
        "file_patch",
        "file_build",
        "document_query",
        "document_ingest",
        "research_report",
        "artifact_create",
        "artifact_edit",
        "chart_render",
        "http_fetch",
        "web_search",
        "memory_forget",
    }
)
TIER1_TOOLS: frozenset[str] = frozenset(
    {"timestamp", "memory_recall", "memory_get", "memory_save", "memory_proximity", "packages_list"}
)

ChokeOutcome = str  # auto_execute | approval_required | denied


def tool_risk_tier(tool_name: str) -> int:
    if tool_name in TIER3_TOOLS:
        return 3
    if tool_name in TIER2_TOOLS:
        return 2
    if tool_name in TIER1_TOOLS:
        return 1
    return 2


def args_digest(args: Any) -> str:
    raw = json.dumps(args, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def build_guardrail_state(
    *, tool_name: str, args: Any, risk_class: str, tenant: str
) -> dict[str, Any]:
    return {
        "tool": tool_name,
        "args_digest": args_digest(args),
        "risk_class": risk_class,
        "tenant": tenant,
    }


def build_guardrail_questions() -> dict[str, Any]:
    return {
        "p_safe": {
            "type": "noul",
            "instructions": "Would a careful operator run this tool now?",
        },
        "risk": {
            "type": "score",
            "instructions": "How risky is this execution?",
            "criteria": ["safe", "caution", "risky", "critical"],
        },
    }


def _tighten(current: ChokeOutcome, new: ChokeOutcome) -> ChokeOutcome:
    rank = {"auto_execute": 0, "approval_required": 1, "denied": 2}
    return current if rank[current] >= rank[new] else new


def _choke_from_outcome(outcome: str, *, tier: int) -> ChokeOutcome:
    if outcome == "denied":
        return "denied"
    if outcome == "approval_required":
        return "approval_required"
    return "approval_required" if tier >= 3 else "auto_execute"


async def choke_tool_call(
    *,
    tool_name: str,
    args: Any,
    tenant: str,
    caller: str,
    risk_class: str | None = None,
    trace_id: str | None = None,
    current_decision: ChokeOutcome = "auto_execute",
    client: DecisionClient | None = None,
) -> ChokeOutcome:
    """ONE guardrail choke. Only ever tightens ``current_decision``."""
    tier = tool_risk_tier(tool_name)
    risk = risk_class or (f"tier-{tier}")

    if not clef_flag_enabled("clef_guardrail"):
        LOGGER.info("clef_guardrail off/unset — tier-%s %s approval_required", tier, tool_name)
        return _tighten(current_decision, "approval_required" if tier >= 3 else current_decision)

    state = build_guardrail_state(
        tool_name=tool_name, args=args, risk_class=risk, tenant=tenant
    )
    questions = build_guardrail_questions()

    try:
        decider = client or get_decision_client()
        result = await decider.decide(
            state=state,
            questions=questions,
            tenant_id=tenant,
            caller=caller,
            category="guardrail",
            tier=tier,
            trace_id=trace_id,
        )
    except ClefDisabledError:
        return _tighten(current_decision, "denied" if tier >= 3 else "approval_required")
    except (ClefConfigurationError, ClefDecisionError) as exc:
        LOGGER.warning("Clef guardrail unavailable for %s: %s", tool_name, exc)
        return _tighten(current_decision, "denied" if tier >= 3 else "approval_required")
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Clef guardrail error for %s: %s", tool_name, exc)
        return _tighten(current_decision, "denied" if tier >= 3 else "approval_required")

    if not result.fact_persisted:
        LOGGER.error("Clef fact not in brain — fail-closed for %s", tool_name)
        return _tighten(current_decision, "denied" if tier >= 3 else "approval_required")

    if should_flag(result.signals):
        LOGGER.info("Clef low confidence for %s", tool_name)

    return _tighten(current_decision, _choke_from_outcome(result.outcome, tier=tier))


def opa_input_from_signals(
    signals: DecisionSignals,
    *,
    tier: int,
    tenant: str,
    resource: str,
    clef_decision_id: str | None = None,
) -> dict[str, Any]:
    return {
        "action": "tool.request",
        "tenant": tenant,
        "resource": resource,
        "confidence_enabled": True,
        "treat_null_as_low": True,
        "min_acceptance": 0.5,
        "p_safe": signals.p_safe,
        "risk": signals.risk,
        "confidence": signals.confidence,
        "decision_guard": True,
        "tier": str(tier),
        "clef_present": signals.p_safe is not None,
        "clef_decision_id": clef_decision_id,
    }


__all__ = [
    "TIER1_TOOLS",
    "TIER2_TOOLS",
    "TIER3_TOOLS",
    "args_digest",
    "build_guardrail_questions",
    "build_guardrail_state",
    "choke_tool_call",
    "opa_input_from_signals",
    "tool_risk_tier",
]
