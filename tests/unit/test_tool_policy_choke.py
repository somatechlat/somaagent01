"""One policy choke for every tool in the chat loop (SOMA-ARCH-TOOLS-001 §11).

``decide_and_authorize_tool`` is the single authority between a model tool
call and ``execute_tool_call``:

1. Capsule ``tool_policy`` — unlisted = ``approval_required``, ``denied``
   wins over any listing.
2. Egress — a network tool with AgentIQ egress denied is ``denied`` even
   when the policy lists it ``auto_execute``.
3. UnifiedGate — RBAC role floor → OPA → SpiceDB → capsule scope
   (``resource:tool_execute`` against the tool name), fail-closed.

And the loop contract the choke must preserve: an ``auto_execute`` tool
actually runs, an unlisted tool asks for approval (no channel = deny),
and a denied tool never reaches the registry.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from admin.common.messages import ErrorCode, get_message
from admin.core.agentiq import UnifiedGate
from admin.core.tool_calling import (
    decide_and_authorize_tool,
    run_tool_loop,
    TOOL_EVENT_APPROVAL,
    TOOL_EVENT_DONE,
    ToolStreamEvent,
    ToolSubject,
)
from admin.llm.services.litellm_schemas import AssembledToolCall, ToolCallsChunk

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


def _capsule(*, auto=(), approval=(), denied=(), capabilities=None):
    """Capsule stub: model field for policy, cached body for gate scope."""
    tool_policy = {
        "auto_execute": list(auto),
        "approval_required": list(approval),
        "denied": list(denied),
    }
    if capabilities is None:
        capabilities = sorted(set(auto) | set(approval) | set(denied))
    body = {
        "persona": {
            "tools": {
                "enabled_capabilities": list(capabilities),
                "tool_policy": tool_policy,
            }
        }
    }
    return SimpleNamespace(
        tool_policy=tool_policy, _cached_body=body, id="capsule-1", tenant_id="tenant-1"
    )


def _iq(*, egress="none"):
    return SimpleNamespace(tool_approval="", require_hitl=False, egress_allowed=egress)


def _subject(*, roles=("agent_owner",), gate=None):
    return ToolSubject(
        user_id="user-1",
        tenant_id="tenant-1",
        roles=list(roles) if roles is not None else None,
        gate=gate if gate is not None else UnifiedGate(),
    )


class _ExplodingGate:
    async def check(self, *args, **kwargs):
        raise RuntimeError("gate boom")


class _RecordingRegistry:
    """Registry that records which tools actually reached execution."""

    def __init__(self, names):
        self._names = set(names)
        self.ran = []

    def get(self, name):
        if name not in self._names:
            return None
        return _RecordingDefinition(self, name)


class _RecordingDefinition:
    def __init__(self, registry, name):
        self.name = name
        self._registry = registry

    async def run(self, args):
        self._registry.ran.append(self.name)
        return {"ran": self.name}


class _ScriptedLLM:
    """Round 1 emits the scripted tool calls; later rounds answer with text."""

    def __init__(self, tool_calls):
        self._tool_calls = list(tool_calls)
        self.rounds = 0

    async def _astream(self, messages, tools=None, **kwargs):
        self.rounds += 1
        if self.rounds == 1 and self._tool_calls:
            yield ToolCallsChunk(tool_calls=list(self._tool_calls))
        else:
            yield "ok"


class _TimeoutApprovalGate:
    """Approval channel whose wait times out — timeout must mean deny."""

    async def wait(self, tool_call_id, timeout_s):
        raise asyncio.TimeoutError()


async def _run_loop(*, capsule, subject, registry, tool_names, iq=None, approval_gate=None):
    """Drive run_tool_loop for one scripted tool round; return events."""
    tool_calls = [
        AssembledToolCall(id=f"call-{i}", name=name, arguments={})
        for i, name in enumerate(tool_names)
    ]
    llm = _ScriptedLLM(tool_calls)
    events = []
    async for item in run_tool_loop(
        llm=llm,
        messages=[],
        tools_for_llm=[],
        tool_registry=registry,
        capsule=capsule,
        iq=iq if iq is not None else _iq(),
        approval_gate=approval_gate,
        subject=subject,
        max_iterations=4,
    ):
        if isinstance(item, ToolStreamEvent):
            events.append(item)
    return events


def _done(events, name):
    return [e for e in events if e.type == TOOL_EVENT_DONE and e.payload.get("name") == name]


# ---------------------------------------------------------------------------
# Choke: policy → egress → UnifiedGate, fail-closed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unlisted_tool_requires_approval():
    """Unlisted non-memory tools = approval_required, never auto_execute."""
    capsule = _capsule(auto=("timestamp",), capabilities=["timestamp", "file_write"])
    decision = await decide_and_authorize_tool(_subject(), capsule, "file_write", {}, _iq())
    assert decision == "approval_required"


@pytest.mark.asyncio
async def test_memory_kit_auto_executes_without_listing():
    """Memory base kit never requires HITL unless denied — product core."""
    capsule = _capsule(
        auto=("timestamp",),
        denied=(),
        capabilities=["timestamp", "memory_save", "memory_recall"],
    )
    assert (
        await decide_and_authorize_tool(_subject(), capsule, "memory_recall", {}, _iq())
        == "auto_execute"
    )
    assert (
        await decide_and_authorize_tool(_subject(), capsule, "memory_save", {}, _iq())
        == "auto_execute"
    )
    # Denied still wins
    capsule_deny = _capsule(auto=(), denied=("memory_forget",), capabilities=["memory_forget"])
    assert (
        await decide_and_authorize_tool(_subject(), capsule_deny, "memory_forget", {}, _iq())
        == "denied"
    )


@pytest.mark.asyncio
async def test_denied_list_wins_over_auto_execute():
    """denied beats auto_execute — the strictest listing is the answer."""
    capsule = _capsule(auto=("shell_exec",), denied=("shell_exec",))
    decision = await decide_and_authorize_tool(_subject(), capsule, "shell_exec", {}, _iq())
    assert decision == "denied"


@pytest.mark.asyncio
async def test_auto_execute_list_runs_through_the_choke():
    """A deliberately listed tool with an authorized subject is allowed."""
    capsule = _capsule(auto=("timestamp",))
    decision = await decide_and_authorize_tool(_subject(), capsule, "timestamp", {}, _iq())
    assert decision == "auto_execute"


@pytest.mark.asyncio
async def test_network_tool_denied_without_egress():
    """Egress is its own axis: auto_execute cannot buy back the network."""
    capsule = _capsule(auto=("http_fetch",))
    decision = await decide_and_authorize_tool(
        _subject(), capsule, "http_fetch", {}, _iq(egress="none")
    )
    assert decision == "denied"


@pytest.mark.asyncio
async def test_missing_subject_fails_closed():
    """No principal, no authority — a missing subject is denial."""
    capsule = _capsule(auto=("timestamp",))
    assert await decide_and_authorize_tool(None, capsule, "timestamp", {}, _iq()) == "denied"


@pytest.mark.asyncio
async def test_gate_exception_fails_closed():
    """Any error inside the choke is denial, never a default grant (§11.1)."""
    capsule = _capsule(auto=("timestamp",))
    decision = await decide_and_authorize_tool(
        _subject(gate=_ExplodingGate()), capsule, "timestamp", {}, _iq()
    )
    assert decision == "denied"


@pytest.mark.asyncio
async def test_capsule_scope_miss_denies_the_tool():
    """UnifiedGate _check_scope: tool not in enabled_capabilities = deny."""
    capsule = _capsule(auto=("timestamp",), capabilities=["timestamp"])
    decision = await decide_and_authorize_tool(_subject(), capsule, "file_write", {}, _iq())
    assert decision == "denied"


@pytest.mark.asyncio
async def test_role_floor_denies_a_subject_without_tool_execute():
    """RBAC floor: `member` holds no resource:tool_execute, so no tool runs."""
    capsule = _capsule(auto=("timestamp",))
    decision = await decide_and_authorize_tool(
        _subject(roles=("member",)), capsule, "timestamp", {}, _iq()
    )
    assert decision == "denied"


@pytest.mark.asyncio
async def test_sysadmin_tool_call_clears_floor_and_scope():
    """A sysadmin runs tools end to end through the choke (§11.1 layer 1+4).

    Regression for the role floor: sysadmin administers agents, so its
    explicit ``resource:tool_execute`` grant must carry an ``auto_execute``
    tool all the way through — denied here would mean the operator cannot
    operate what they configure.
    """
    capsule = _capsule(auto=("timestamp",))
    decision = await decide_and_authorize_tool(
        _subject(roles=("sysadmin",)), capsule, "timestamp", {}, _iq()
    )
    assert decision == "auto_execute"


# ---------------------------------------------------------------------------
# run_tool_loop: choke runs per tool BEFORE execute; approval semantics
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auto_execute_list_runs_in_the_loop():
    """An auto_execute tool reaches the registry and executes."""
    capsule = _capsule(auto=("timestamp",))
    registry = _RecordingRegistry({"timestamp"})
    events = await _run_loop(
        capsule=capsule, subject=_subject(), registry=registry, tool_names=["timestamp"]
    )
    assert registry.ran == ["timestamp"]
    done = _done(events, "timestamp")
    assert done and done[-1].payload["ok"] is True
    assert done[-1].payload["status"] == "executed"


@pytest.mark.asyncio
async def test_denied_tool_never_reaches_the_registry():
    """Denied is terminal: no approval round, no execution."""
    capsule = _capsule(auto=("timestamp",), denied=("timestamp",))
    registry = _RecordingRegistry({"timestamp"})
    events = await _run_loop(
        capsule=capsule, subject=_subject(), registry=registry, tool_names=["timestamp"]
    )
    assert registry.ran == []
    assert not [e for e in events if e.type == TOOL_EVENT_APPROVAL]
    done = _done(events, "timestamp")
    assert done and done[-1].payload["ok"] is False
    assert done[-1].payload["error"] == get_message(ErrorCode.TOOL_POLICY_DENIED)


@pytest.mark.asyncio
async def test_unlisted_tool_without_approval_channel_is_denied():
    """Unlisted asks first; with nobody to ask the answer is no (fail closed)."""
    capsule = _capsule(auto=("timestamp",), capabilities=["timestamp", "file_write"])
    registry = _RecordingRegistry({"file_write"})
    events = await _run_loop(
        capsule=capsule, subject=_subject(), registry=registry, tool_names=["file_write"]
    )
    approvals = [e for e in events if e.type == TOOL_EVENT_APPROVAL]
    assert approvals and approvals[0].payload["name"] == "file_write"
    assert registry.ran == []
    done = _done(events, "file_write")
    assert done and done[-1].payload["ok"] is False
    assert done[-1].payload["status"] == "denied"


@pytest.mark.asyncio
async def test_approval_timeout_denies():
    """Timeout on the approval round-trip means deny, never execute."""
    capsule = _capsule(auto=("timestamp",), capabilities=["timestamp", "file_write"])
    registry = _RecordingRegistry({"file_write"})
    events = await _run_loop(
        capsule=capsule,
        subject=_subject(),
        registry=registry,
        tool_names=["file_write"],
        approval_gate=_TimeoutApprovalGate(),
    )
    assert registry.ran == []
    done = _done(events, "file_write")
    assert done and done[-1].payload["ok"] is False
    assert done[-1].payload["error"] == get_message(ErrorCode.TOOL_EXECUTION_DENIED)


@pytest.mark.asyncio
async def test_choke_denies_before_execute_when_gate_refuses():
    """The choke runs per tool BEFORE execute: a refusing gate blocks run()."""
    capsule = _capsule(auto=("timestamp",))
    registry = _RecordingRegistry({"timestamp"})
    events = await _run_loop(
        capsule=capsule,
        subject=_subject(gate=_ExplodingGate()),
        registry=registry,
        tool_names=["timestamp"],
    )
    assert registry.ran == []
    done = _done(events, "timestamp")
    assert done and done[-1].payload["ok"] is False
    assert done[-1].payload["status"] == "denied"
