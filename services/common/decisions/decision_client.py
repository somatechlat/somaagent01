"""Shared Clef decision client — SOLE caller of the Workers AI decision model.

Product law: every decision is a decision-fact in THE BRAIN
(MemoryGateway.remember -> SomaBrain) or it did not happen. No local store,
no SFM client (T-1), no secrets in state payloads.
"""

from __future__ import annotations

import logging
from typing import Any

from services.common.decisions.clef_client import ClefClient
from services.common.decisions.contracts import (
    ClefConfigurationError,
    ClefDecisionError,
    ClefDisabledError,
    DecisionCategory,
    DecisionFact,
    DecisionOutcome,
    DecisionPayload,
    DecisionSignals,
    caller_values,
    decision_fact_namespace,
    input_state_digest,
    map_answers_to_signals,
    outcome_from_signals,
)

LOGGER = logging.getLogger(__name__)


def clef_flag_enabled(flag: str) -> bool:
    """Feature flag via the one registry. Unset/error = False (fail-closed).

    A registry/config failure must not open a dangerous path; it is treated as
    the flag being off so the choke tightens tier-3 instead of allowing.
    """
    try:
        from admin.core.config.registry import get_feature_flag

        return bool(get_feature_flag(flag, False))
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("feature flag %s unreadable (%s) — treating as off", flag, exc)
        return False


class DecisionResult:
    __slots__ = (
        "decision_id",
        "signals",
        "outcome",
        "answers",
        "model_id",
        "latency_ms",
        "fact_persisted",
    )

    def __init__(
        self,
        *,
        decision_id: str,
        signals: DecisionSignals,
        outcome: DecisionOutcome,
        answers: dict[str, Any],
        model_id: str,
        latency_ms: float,
        fact_persisted: bool,
    ) -> None:
        self.decision_id = decision_id
        self.signals = signals
        self.outcome = outcome
        self.answers = answers
        self.model_id = model_id
        self.latency_ms = latency_ms
        self.fact_persisted = fact_persisted


class DecisionClient:
    """Sole Clef caller. Builds request, persists decision-fact through brain."""

    def __init__(
        self,
        *,
        client: ClefClient | None = None,
        memory_gateway: Any | None = None,
    ) -> None:
        self._client = client
        self._memory = memory_gateway

    def _engine(self) -> ClefClient:
        if self._client is None:
            self._client = ClefClient()
        return self._client

    async def _persist_fact(self, fact: DecisionFact, *, category: DecisionCategory) -> bool:
        """Brain is system of record. Returns True only when SomaBrain acked."""
        if self._memory is None:
            from services.common.memory_gateway import get_memory_gateway

            self._memory = get_memory_gateway()
        from services.common.memory_contract import MemoryWrite, make_coord

        text = fact.model_dump_json()
        namespace = decision_fact_namespace(category)
        try:
            coord = make_coord(fact.tenant_id, "episodic", fact.created_at, text)
            write = MemoryWrite(
                text=text,
                kind="episodic",
                tenant_id=fact.tenant_id,
                session_id=fact.trace_id,
                coord=coord,
                salience=0.9,
                source=namespace,
            )
            acks = await self._memory.remember(write)
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Clef decision-fact write failed for %s: %s", fact.decision_id, exc)
            return False
        ok = bool(acks) and all(getattr(a, "ok", False) for a in acks)
        if not ok:
            LOGGER.warning("Clef decision-fact not persisted for %s", fact.decision_id)
        return ok

    async def decide(
        self,
        *,
        state: Any,
        questions: dict[str, Any],
        tenant_id: str,
        caller: str,
        category: DecisionCategory = "guardrail",
        tier: int = 1,
        trace_id: str | None = None,
        outcome: DecisionOutcome | None = None,
        opa_decision_ref: str | None = None,
    ) -> DecisionResult:
        if caller not in caller_values():
            raise ClefConfigurationError(f"caller must be one of {caller_values()}, got {caller!r}")
        if not questions:
            raise ClefConfigurationError("decide() requires at least one question")
        if not str(tenant_id).strip():
            raise ClefConfigurationError("decide() requires a tenant_id")
        if not clef_flag_enabled("clef_decide"):
            raise ClefDisabledError("clef_decide is not enabled (fail-closed).")

        engine = self._engine()
        response = await engine.decide(state=state, questions=questions)
        signals = map_answers_to_signals(response.answers)
        resolved = outcome or outcome_from_signals(signals, tier=tier)

        primary_mode = "noul"
        for ans in response.answers.values():
            if getattr(ans, "type", None) == "noul":
                primary_mode = "noul"
                break
            primary_mode = getattr(ans, "type", "noul")

        first_qid = next(iter(response.answers), "")
        first_ans = response.answers.get(first_qid)
        payload = DecisionPayload(
            choice=getattr(first_ans, "choice", None),
            score=getattr(first_ans, "score", None),
            noul=getattr(first_ans, "noul", None),
            probabilities=getattr(first_ans, "probabilities", None),
            confidence=getattr(first_ans, "confidence", None),
        )
        fact = DecisionFact(
            tenant_id=str(tenant_id),
            trace_id=trace_id,
            mode=primary_mode,  # type: ignore[arg-type]
            question_id=first_qid,
            payload=payload,
            input_state_digest=input_state_digest(state),
            caller=caller,  # type: ignore[arg-type]
            model_id=str(response.model or engine.model_id),
            latency_ms=round(float(response.latency_ms or 0.0), 3),
            outcome=resolved,
            opa_decision_ref=opa_decision_ref,
        )
        persisted = await self._persist_fact(fact, category=category)
        if not persisted:
            LOGGER.error(
                "Clef decision %s NOT in THE BRAIN (outcome=%s)", fact.decision_id, resolved
            )

        return DecisionResult(
            decision_id=fact.decision_id,
            signals=signals,
            outcome=resolved,
            answers=dict(response.answers),
            model_id=fact.model_id,
            latency_ms=fact.latency_ms,
            fact_persisted=persisted,
        )


_CLIENT: DecisionClient | None = None


def get_decision_client() -> DecisionClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = DecisionClient()
    return _CLIENT


__all__ = [
    "DecisionClient",
    "DecisionResult",
    "clef_flag_enabled",
    "get_decision_client",
]
