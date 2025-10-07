import pytest

from services.common.escalation import decide_escalation
from services.common.model_costs import estimate_escalation_cost


@pytest.mark.parametrize(
    "metadata,expected",
    [
        ({"escalate": True}, True),
        ({"risk_level": "high"}, True),
        ({"priority": "urgent", "complexity": "baseline"}, False),
    ],
)
def test_decide_escalation_basic(metadata, expected):
    decision = decide_escalation(
        message="Please fix the production outage in kubernetes cluster.",
        analysis={
            "intent": "problem_report",
            "sentiment": "negative",
            "tags": ["infrastructure"],
        },
        event_metadata=metadata,
        fallback_enabled=False,
    )
    assert decision.should_escalate is expected


def test_decide_escalation_complexity_tags():
    decision = decide_escalation(
        message="""We need a step-by-step migration plan for this legacy service.
        The task touches infrastructure, networking, and compliance requirements.
        Provide thorough reasoning.""",
        analysis={
            "intent": "action_request",
            "sentiment": "neutral",
            "tags": ["infrastructure", "code", "testing"],
        },
        event_metadata={"complexity": "advanced"},
        fallback_enabled=False,
    )
    assert decision.should_escalate is True
    assert decision.reason == "complexity_high_tag_signal"


def test_decide_escalation_fallback():
    decision = decide_escalation(
        message="Lorem ipsum " * 200,
        analysis={"intent": "statement", "sentiment": "neutral", "tags": []},
        event_metadata={},
        fallback_enabled=True,
    )
    assert decision.should_escalate is True
    assert decision.reason == "fallback_length_trigger"


def test_estimate_escalation_cost_known_model():
    cost = estimate_escalation_cost(
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        input_tokens=1000,
        output_tokens=500,
    )
    assert cost == pytest.approx(0.9, rel=1e-3)


def test_estimate_escalation_cost_unknown_model():
    assert (
        estimate_escalation_cost("unknown/model", input_tokens=100, output_tokens=100)
        is None
    )
