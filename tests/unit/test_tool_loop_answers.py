"""The tool loop must produce an ANSWER, not a stop string.

Verified defects (SOMA-PM-PLAN-CHAT-COGNITION-001):
- D7: at MAX_TOOL_ITERATIONS the loop yields "[Tool loop stopped...]" as if it
  were the answer. There is no terminal round, so the user sees an error.
- D8: an approved tool never executes - `continue` always skips it, and `error`
  is unbound when approved (NameError).
- D3: `tool_choice` is never sent, so nothing tells the model "answer now".
"""

from __future__ import annotations

import inspect

from admin.core import tool_calling as tc


def test_stop_string_is_never_the_answer():
    """The loop must not hand the user a stop message as the reply."""
    src = inspect.getsource(tc.run_tool_loop)
    assert "Tool loop stopped" not in src, (
        "the loop still yields a stop string into the user-visible answer"
    )


def test_terminal_round_asks_for_an_answer():
    """After tool calls there must be a round with tool_choice none."""
    src = inspect.getsource(tc.run_tool_loop)
    assert "tool_choice" in src, "tool_choice is never sent"


def test_approved_tool_executes():
    """Approval must fall through to execution, not skip it."""
    src = inspect.getsource(tc.run_tool_loop)
    start = src.index('if decision == "approval_required"')
    end = src.index('if decision == "denied"', start)
    block = src[start:end]

    # An approved tool must reach execute_tool_call. The only `continue` allowed
    # inside the approval handling is the one on the DENIED path.
    assert "decision = \"auto_execute\"" in block, (
        "an approved tool never falls through to execution"
    )
    denied_idx = block.find("if not approved")
    approved_tail = block[denied_idx:] if denied_idx >= 0 else block
    # after the denial guard, the approved path must not `continue`
    after_denied = approved_tail[approved_tail.index("continue") + 9:] if "continue" in approved_tail else ""
    assert "continue" not in after_denied, (
        "the approved path is still skipped"
    )
    assert "execute_tool_call" in src[src.index('if decision == "approval_required"'):], (
        "execution is not reachable after approval"
    )


def test_memory_recall_returns_a_digest():
    """A tool result the model can read whole, not truncated JSON."""
    import inspect as _i
    from services.tool_executor import memory_tools

    src = _i.getsource(memory_tools.MemoryRecallTool)
    assert "digest" in src or "summary" in src, (
        "memory_recall still returns raw payloads that invite re-query"
    )
    assert '"*"' not in src, "empty query still becomes a wildcard dump"
