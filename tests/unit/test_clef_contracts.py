"""Clef contracts unit tests — test doubles stay in test files only."""

from __future__ import annotations

import pytest

from services.common.decisions.contracts import (
    ClefAnswer,
    map_answers_to_signals,
    outcome_from_signals,
)


def test_noul_maps_to_p_safe_not_confidence() -> None:
    answers = {
        "p_safe": ClefAnswer(type="noul", noul=0.42),
        "risk": ClefAnswer(
            type="score", score=1.5, confidence=0.77, probabilities={"0": 0.2, "1": 0.5, "2": 0.3}
        ),
    }
    sig = map_answers_to_signals(answers)
    assert sig.p_safe == pytest.approx(0.42)
    assert sig.confidence == pytest.approx(0.77)
    assert sig.risk == pytest.approx(1.5)
    assert sig.p_safe != sig.confidence


def test_missing_p_safe_fails_closed_tier3() -> None:
    sig = map_answers_to_signals({})
    assert outcome_from_signals(sig, tier=3) == "denied"


def test_tier3_never_allow() -> None:
    sig = map_answers_to_signals({"p_safe": ClefAnswer(type="noul", noul=0.99)})
    assert outcome_from_signals(sig, tier=3) == "approval_required"


def test_low_p_safe_denied_or_approval() -> None:
    sig = map_answers_to_signals({"p_safe": ClefAnswer(type="noul", noul=0.1)})
    assert outcome_from_signals(sig, tier=1) in ("approval_required", "denied")
