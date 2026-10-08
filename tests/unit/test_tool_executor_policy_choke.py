"""Kafka tool path passes the same choke as the chat loop (SOMA §11.1).

``services/tool_executor/request_handler.py`` no longer authorizes on OPA
alone:

1. ``decide_and_authorize_tool`` decides first — capsule ``tool_policy``,
   egress, RBAC → OPA → SpiceDB → capsule scope — and a decision other than
   ``auto_execute`` blocks the request (this path has no approval channel).
2. The rego tool policy is then read with the action ``policy/tool_policy.rego``
   actually matches (``tool.request``). The old ``tool.execute`` literal
   matched no rule, so the rego could only deny.

Identity comes from the event only as far as it can be trusted: the principal
is ``metadata.user_id`` with roles resolved server-side, the capsule is
``persona_id`` scoped to the event tenant, and anything absent fails closed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from admin.common.messages import ErrorCode, get_message
from services.tool_executor import request_handler as rh
from services.tool_executor.request_handler import RequestHandler

REPO_ROOT = Path(__file__).resolve().parents[2]
REGO = REPO_ROOT / "policy" / "tool_policy.rego"


class _FakePolicy:
    def __init__(self, *, configured: bool, allowed: bool) -> None:
        self.is_configured = configured
        self._allowed = allowed
        self.seen: list = []

    async def evaluate(self, request):
        self.seen.append(request)
        return self._allowed


class _FakeRequeue:
    def __init__(self) -> None:
        self.items: list = []

    async def add(self, identifier, payload) -> None:
        self.items.append((identifier, payload))


class _FakeExecutor:
    def __init__(self, policy: _FakePolicy) -> None:
        self.policy = policy
        self.requeue = _FakeRequeue()
        self.results: list = []

    async def publish_result(self, event, status, payload, *, execution_time, metadata=None):
        self.results.append({"status": status, "payload": payload})

    def get_audit_store(self):
        return object()  # log_tool_event is best-effort and swallows failures


def _event() -> dict:
    return {
        "event_id": "evt-1",
        "session_id": "sess-1",
        "tool_name": "timestamp",
        "args": {"format": "iso"},
        "metadata": {"tenant": "tenant-1", "user_id": "user-1"},
    }


async def _check(
    monkeypatch,
    *,
    decision: str = "auto_execute",
    configured: bool = False,
    opa_allowed: bool = False,
    event: dict | None = None,
):
    """Drive ``_check_policy`` with the choke inputs stubbed (no DB)."""
    policy = _FakePolicy(configured=configured, allowed=opa_allowed)
    handler = RequestHandler(_FakeExecutor(policy))

    async def _inputs(self, tenant, persona_id, metadata):
        return ("subject", "capsule", "iq")

    async def _decide(subject, capsule, tool_name, args, iq):
        return decision

    monkeypatch.setattr(RequestHandler, "_choke_inputs", _inputs)
    monkeypatch.setattr(rh, "decide_and_authorize_tool", _decide)

    evt = event or _event()
    status = await handler._check_policy(
        tenant="tenant-1",
        persona_id="capsule-1",
        tool_name="timestamp",
        tool_label="timestamp",
        event=evt,
        metadata=dict(evt["metadata"]),
        session_id="sess-1",
        trace_id_hex=None,
    )
    return status, handler, policy


# ---------------------------------------------------------------------------
# Action name must match policy/*.rego
# ---------------------------------------------------------------------------


def test_rego_still_matches_tool_request():
    """The rego the OPA layer reads allows ``tool.request`` — guard the pairing."""
    source = REGO.read_text(encoding="utf-8")
    assert 'input.action == "tool.request"' in source


@pytest.mark.asyncio
async def test_opa_request_uses_the_action_the_rego_matches(monkeypatch):
    status, handler, policy = await _check(monkeypatch, configured=True, opa_allowed=True)
    assert status is None
    assert len(policy.seen) == 1
    request = policy.seen[0]
    assert request.action == "tool.request"
    assert request.action != "tool.execute"
    assert request.resource == "timestamp"


# ---------------------------------------------------------------------------
# The choke decides before OPA; anything but auto_execute blocks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_choke_denied_blocks_the_request(monkeypatch):
    status, handler, policy = await _check(monkeypatch, decision="denied")
    assert status == "blocked"
    assert handler._executor.results[0]["status"] == "blocked"
    assert handler._executor.results[0]["payload"]["message"] == get_message(
        ErrorCode.TOOL_POLICY_DENIED
    )
    # Never reaches the rego layer: the choke already said no.
    assert policy.seen == []
    # Denied events stay replayable for an operator who changes the policy.
    assert len(handler._executor.requeue.items) == 1


@pytest.mark.asyncio
async def test_choke_approval_required_blocks_without_a_channel(monkeypatch):
    """No approval channel on the Kafka path: approval_required must not run."""
    status, handler, _ = await _check(monkeypatch, decision="approval_required")
    assert status == "blocked"
    assert handler._executor.results[0]["payload"]["message"] == get_message(
        ErrorCode.TOOL_EXECUTION_DENIED
    )


@pytest.mark.asyncio
async def test_choke_exception_fails_closed(monkeypatch):
    handler = RequestHandler(_FakeExecutor(_FakePolicy(configured=False, allowed=False)))

    async def _inputs(self, tenant, persona_id, metadata):
        raise RuntimeError("boom")

    monkeypatch.setattr(RequestHandler, "_choke_inputs", _inputs)
    evt = _event()
    status = await handler._check_policy(
        tenant="tenant-1",
        persona_id="capsule-1",
        tool_name="timestamp",
        tool_label="timestamp",
        event=evt,
        metadata=dict(evt["metadata"]),
        session_id="sess-1",
        trace_id_hex=None,
    )
    assert status == "error"
    assert handler._executor.results[0]["payload"]["message"] == get_message(
        ErrorCode.TOOL_POLICY_EVALUATION_FAILED
    )
    # An evaluation failure is not a denial to replay.
    assert handler._executor.requeue.items == []


# ---------------------------------------------------------------------------
# OPA narrows only when an engine is attached (UnifiedGate semantics)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_absent_engine_narrows_nothing_and_choke_already_decided(monkeypatch):
    status, handler, policy = await _check(monkeypatch, configured=False)
    assert status is None
    assert policy.seen == []


@pytest.mark.asyncio
async def test_opa_denial_blocks(monkeypatch):
    status, handler, _ = await _check(monkeypatch, configured=True, opa_allowed=False)
    assert status == "blocked"
    assert handler._executor.results[0]["payload"]["message"] == get_message(
        ErrorCode.TOOL_POLICY_DENIED
    )
    assert len(handler._executor.requeue.items) == 1
