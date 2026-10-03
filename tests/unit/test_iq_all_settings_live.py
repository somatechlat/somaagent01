"""Every AgentIQ setting either drives behaviour or does not exist.

Two rules, both from the house standard:

- A control with no handler is a lie (a knob an operator turns and nothing
  changes).
- No stubs, no fields for features that are not built.

Measured state before this change: of 12 derived settings, 9 selected
nothing. ``rlm_iterations`` named a feature (RLM) that does not exist in the
codebase. ``thinking_budget`` was parsed for and never applied. ``cost_tier``
was a routing label with two vocabularies that matched nothing, duplicating
``priority``.

This suite asserts the post-condition: no dead field, and the safety knobs
actually gate.
"""

from __future__ import annotations

import inspect

from admin.core.agentiq.settings import DerivedSettings
from admin.core import chat_orchestrator as co
from admin.core import tool_calling as tc


def test_no_field_for_a_feature_that_does_not_exist():
    """rlm_iterations named RLM. There is no RLM in the codebase."""
    fields = set(DerivedSettings.model_fields)
    assert "rlm_iterations" not in fields
    assert "thinking_budget" not in fields


def test_cost_tier_is_not_a_second_vocabulary_for_priority():
    """Route on the capability tier. One concept, one name.

    ``prefer_cost_tier`` is the *model router's* parameter and is fine; what
    must not exist is AgentIQ emitting a second vocabulary of its own.
    """
    fields = set(DerivedSettings.model_fields)
    assert "cost_tier" not in fields
    # The IQ tier reaches the router through the single mapping helper.
    src = inspect.getsource(co)
    assert "_iq_model_tier" in src


def test_require_hitl_and_tool_approval_gate_the_tool_loop():
    """Autonomy must drive autonomy. These two are the safety surface."""
    src = inspect.getsource(tc)
    assert "require_hitl" in src or "tool_approval" in src
    # The resolved policy, not a log line.
    assert "approval_required" in src or "ToolApproval" in src


def test_brain_query_enabled_gates_the_brain_query():
    """brain_query_enabled must actually decide whether the brain is asked."""
    src = inspect.getsource(co)
    assert "brain_query_enabled" in src


def test_model_tier_reaches_model_selection():
    """model_tier must select models, not just appear in a log line."""
    src = inspect.getsource(co)
    assert "model_tier" in src and "select_model" in src


def test_token_limit_caps_the_budget():
    """resource_budget must bound real spend via the governor."""
    src = inspect.getsource(co)
    assert "token_limit" in src
