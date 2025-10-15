import pytest

from services.common.escalation import should_escalate
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
    decision = should_escalate(
        message="Please fix the production outage in kubernetes cluster.",
        analysis={
            "intent": "problem_report",
            "sentiment": "negative",
            "tags": ["infrastructure"],
        },
        event_metadata=metadata,
    )
    assert decision.should_escalate is expected


def test_decide_escalation_complexity_tags():
    decision = should_escalate(
        message="""We need a step-by-step migration plan for this legacy service.
        The task touches infrastructure, networking, and compliance requirements.
        Provide thorough reasoning.""",
        analysis={
            "intent": "action_request",
            "sentiment": "neutral",
            "tags": ["infrastructure", "code", "testing"],
        },
        event_metadata={"complexity": "advanced"},
    )
    assert decision.should_escalate is True
    assert decision.reason == "complexity_high_tag_signal"


def test_decide_escalation_no_fallbacks():
    """Verify we removed fallback logic - production uses proper escalation criteria only."""
    decision = should_escalate(
        message="Lorem ipsum " * 200,
        analysis={"intent": "statement", "sentiment": "neutral", "tags": []},
        event_metadata={},
    )
    # Should NOT escalate based on length alone - no fallback logic
    assert decision.should_escalate is False
    assert decision.reason == "slm_handled"


def test_estimate_escalation_cost_known_model():
    cost = estimate_escalation_cost(
        "mistralai/Mixtral-8x7B-Instruct-v0.1",
        input_tokens=1000,
        output_tokens=500,
    )
    assert cost == pytest.approx(0.9, rel=1e-3)


def test_estimate_escalation_cost_unknown_model():
    assert estimate_escalation_cost("unknown/model", input_tokens=100, output_tokens=100) is None
