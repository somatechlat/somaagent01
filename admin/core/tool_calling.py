"""Native function-calling loop — Phase 9 tool execution (work package C1).

Wires model ``tool_calls`` to the real ToolRegistry runtime (Echo, Timestamp,
CodeExecution, FileRead, HttpFetch, CanvasAppend, IngestDocument) and surfaces
a tool timeline for the chat stream.

VIBE COMPLIANT:
- Native function-calling API only — tool calls are NEVER regex-parsed
  out of model text.
- Capsule ``tool_policy`` (auto_execute / approval_required / denied) is
  honoured on every call; approval_required fails closed until an approval
  channel exists.
- Real ToolRegistry execution with bounded per-tool timeout.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from admin.common.messages import ErrorCode, get_message

logger = logging.getLogger(__name__)

def _tool_setting(name: str, default):
    """Resolve one runtime knob through the real chain.

    Capsule -> AgentSetting -> SettingsModel -> schema default
    (``admin.core.helpers.settings.get_settings``). The declared value lives on
    ``SettingsModel``; the ``default`` here is only the last-resort fallback if
    a name is ever removed from the model.
    """
    from admin.core.helpers.settings import get_settings

    model = get_settings()
    value = getattr(model, name.lower(), None)
    return default if value is None else value



# Tools that reach the network. Gated by IQ egress_allowed: an operator who
# turns autonomy down must not get outbound calls from an auto-executed tool.
_NETWORK_TOOLS = frozenset({"http_fetch", "document_ingest", "canvas_append"})

# Cap the model->tool->model loop so a runaway tool chain cannot pin a turn
# forever. Each of these is a declared setting, not a literal.
MAX_TOOL_ITERATIONS = int(_tool_setting("TOOL_MAX_ITERATIONS", 8))
TOOL_EXEC_TIMEOUT_S = float(_tool_setting("TOOL_EXEC_TIMEOUT_S", 30.0))
TOOL_APPROVAL_TIMEOUT_S = float(_tool_setting("TOOL_APPROVAL_TIMEOUT_S", 120.0))
_TOOL_RESULT_MAX_CHARS = int(_tool_setting("TOOL_RESULT_MAX_CHARS", 12000))

# Tool timeline event types — mirrored by the WS chat protocol
# (services/gateway/consumers/chat.py) so the UI can render a tool timeline.
TOOL_EVENT_CALL = "tool.call"
TOOL_EVENT_DELTA = "tool.delta"
TOOL_EVENT_DONE = "tool.done"
TOOL_EVENT_APPROVAL = "tool.approval_request"


@dataclass
class ToolStreamEvent:
    """Tool-calling timeline event yielded by the chat stream.

    Consumers forward these as ``tool.*`` WebSocket messages (CH-11).
    """

    type: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class ToolPolicy:
    """Capsule ``tool_policy`` snapshot: auto_execute / approval_required / denied."""

    auto_execute: Tuple[str, ...] = ()
    approval_required: Tuple[str, ...] = ()
    denied: Tuple[str, ...] = ()

    def decision(self, tool_name: str) -> str:
        """Return the execution decision for ``tool_name``.

        SOMA-ARCH-TOOLS-001:
        * **denied** always wins.
        * **Non-disableable memory kit** (recall/save/forget/proximity/get)
          auto-executes unless denied — memory is the product core; HITL
          on every recall is a defect, not safety.
        * **auto_execute** list still wins for other tools.
        * **Unlisted** dangerous/new tools (file_write, shell_exec,
          research_report, …) require approval — never silent auto-run.
        """
        if tool_name in self.denied:
            return "denied"
        # Memory lane: always on (base kit), unless explicitly denied above.
        from services.tool_executor.default_tools import NON_DISABLEABLE_TOOLS

        if tool_name in NON_DISABLEABLE_TOOLS:
            return "auto_execute"
        if tool_name in self.auto_execute:
            return "auto_execute"
        # Unlisted and approval_required both require a human (or IQ floor
        # that later moves them). Fail-closed default for non-memory tools.
        return "approval_required"


def resolve_tool_policy(capsule: Any, iq: Any = None) -> ToolPolicy:
    """Read the capsule tool_policy JSON (model field, body fallback).

    AgentIQ's autonomy knobs are a **floor on restrictiveness** on top of the
    capsule policy: an operator who turns autonomy down gets a safer agent
    whatever the capsule says. IQ can only tighten, never loosen.

    The knobs used to be derived and then ignored - ``tool_approval`` and
    ``require_hitl`` appeared in a log line while the capsule policy alone
    decided. A knob named after safety that does not gate is a lie.
    """
    policy = getattr(capsule, "tool_policy", None)
    if not isinstance(policy, dict):
        policy = {}
    if not policy:
        body = getattr(capsule, "_cached_body", None) or {}
        if isinstance(body, dict):
            nested = body.get("persona", {}).get("tools", {}).get("tool_policy", {})
            if isinstance(nested, dict):
                policy = nested

    def _names(key: str) -> Tuple[str, ...]:
        raw = policy.get(key) or []
        if not isinstance(raw, (list, tuple)):
            return ()
        return tuple(str(name) for name in raw)

    policy = ToolPolicy(
        auto_execute=_names("auto_execute"),
        approval_required=_names("approval_required"),
        denied=_names("denied"),
    )
    return _apply_autonomy_floor(policy, iq)


def _apply_autonomy_floor(policy: ToolPolicy, iq: Any) -> ToolPolicy:
    """Tighten a capsule policy to the AgentIQ autonomy level.

    Fail-safe direction only. Unknown IQ values produce the strictest floor.
    """
    if iq is None:
        return policy

    approval = str(getattr(iq, "tool_approval", "") or "").lower()
    require_hitl = bool(getattr(iq, "require_hitl", False))

    # require_hitl is the strictest: nothing runs without a human.
    if require_hitl or approval == "all":
        return ToolPolicy(
            auto_execute=(),
            approval_required=policy.approval_required + policy.auto_execute,
            denied=policy.denied,
        )

    # "dangerous": tools the operator flagged as needing a human stay gated.
    if approval == "dangerous":
        return ToolPolicy(
            auto_execute=policy.auto_execute,
            approval_required=policy.approval_required,
            denied=policy.denied,
        )

    # "none" (or unknown): the capsule policy stands unchanged. Unknown is not
    # a licence to loosen - it changes nothing, which is the safe reading.
    return policy


def egress_permitted(iq: Any) -> bool:
    """Whether this turn may reach the network at all.

    ``egress_allowed`` was derived and enforced by nothing. Network tools
    (http_fetch and anything that calls out) consult this; with no IQ present
    the answer is the strict one.
    """
    if iq is None:
        return False
    level = str(getattr(iq, "egress_allowed", "") or "").lower()
    # NONE denies. WHITELIST/EXPANDED/UNRESTRICTED allow the call to proceed;
    # per-host allow-lists are the next narrowing step and are not yet built,
    # so this is a real gate on "may egress at all", not a pretend policy.
    return level in {"whitelist", "expanded", "unrestricted"}


@dataclass(frozen=True)
class ToolSubject:
    """The authenticated principal behind one tool call (SOMA-ARCH-TOOLS-001 §11.1).

    ``roles`` follows the UnifiedGate contract exactly: ``None`` means
    "resolve the membership record", an empty sequence means "this subject
    holds nothing" and denies. ``gate`` is the UnifiedGate-compatible
    authority to judge layered authorization; ``None`` uses the process-wide
    shared gate so every caller talks to one instance (its policy clients
    cache on it).
    """

    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    roles: Optional[Any] = None
    gate: Any = None


_SHARED_GATE: Any = None


def _shared_gate() -> Any:
    """Return the process-wide UnifiedGate, created on first use."""
    global _SHARED_GATE
    if _SHARED_GATE is None:
        from admin.core.agentiq import UnifiedGate

        _SHARED_GATE = UnifiedGate()
    return _SHARED_GATE


async def decide_and_authorize_tool(
    subject: Any,
    capsule: Any,
    tool_name: str,
    args: Any,
    iq: Any,
) -> str:
    """The one policy choke every chat-loop tool call passes **before** it runs.

    SOMA-ARCH-TOOLS-001 §11.1, fail-closed, cheapest layer first:

    1. Capsule ``tool_policy`` (``ToolPolicy.decision``) — ``denied`` wins,
       ``auto_execute`` only when deliberately listed, everything else
       including unlisted tools is ``approval_required``.
    2. Egress — a network tool (``_NETWORK_TOOLS``) with AgentIQ egress
       denied is ``denied``. A policy listing cannot buy back the network.
    3. UnifiedGate — RBAC role floor → OPA → SpiceDB → capsule scope
       (``action="resource:tool_execute"``, ``resource=tool_name``), the same
       layered check the rest of the product uses (§11.3 "one choke").

    Returns ``"auto_execute" | "approval_required" | "denied"``. Any
    exception — and a missing subject — returns ``denied``: fail-closed is
    the contract, never a default grant.

    ``args`` rides along for the shared contract with the Kafka executor
    (path-scoped effects belong to PathGuard/OPA context there); this layer
    decides on subject + capsule + tool name and never invents hosts or
    setting names.
    """
    if subject is None:
        logger.warning("tool choke: no subject for %s (FAIL-CLOSED)", tool_name)
        return "denied"
    try:
        decision = resolve_tool_policy(capsule, iq).decision(tool_name)
        if decision == "denied":
            return "denied"

        if tool_name in _NETWORK_TOOLS and not egress_permitted(iq):
            return "denied"

        gate = getattr(subject, "gate", None) or _shared_gate()
        allowed = await gate.check(
            capsule,
            action="resource:tool_execute",
            resource=tool_name,
            user_id=getattr(subject, "user_id", None),
            tenant_id=getattr(subject, "tenant_id", None),
            roles=getattr(subject, "roles", None),
        )
        if not allowed:
            return "denied"
        return decision
    except Exception as exc:  # noqa: BLE001 — fail-closed by contract
        logger.warning("tool choke fail-closed for %s: %s", tool_name, exc)
        return "denied"


def _truncate_result(text: str, limit: int = _TOOL_RESULT_MAX_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[truncated {len(text) - limit} chars]"


def build_assistant_tool_message(tool_calls: List[Any]) -> Any:
    """Build the assistant message carrying the model's native tool_calls."""
    from langchain_core.messages import AIMessage

    calls = []
    for tc in tool_calls:
        args = tc.arguments if isinstance(tc.arguments, dict) else {}
        calls.append({"id": tc.id, "name": tc.name, "args": args, "type": "tool_call"})
    return AIMessage(content="", tool_calls=calls)


def build_tool_result_message(
    tool_call_id: str,
    result: Dict[str, Any],
    ok: bool,
    error: Optional[str] = None,
) -> Any:
    """Build the tool result message bound to ``tool_call_id``."""
    from langchain_core.messages import ToolMessage

    payload: Dict[str, Any] = {"ok": ok, "result": result}
    if error:
        payload["error"] = error
    return ToolMessage(
        content=_truncate_result(json.dumps(payload, default=str)),
        tool_call_id=tool_call_id,
    )


async def execute_tool_call(
    tool_registry: Any,
    name: str,
    arguments: Dict[str, Any],
    *,
    timeout_s: float = TOOL_EXEC_TIMEOUT_S,
) -> Tuple[Dict[str, Any], bool, Optional[str]]:
    """Execute one tool call via the per-capsule ToolRegistry.

    Returns ``(result, ok, error)``. Unknown tools and argument-shape errors
    fail closed with a model-visible error instead of raising.
    """
    definition = tool_registry.get(name) if tool_registry else None
    if definition is None:
        return {}, False, get_message(ErrorCode.TOOL_NOT_FOUND, name=name)
    if not isinstance(arguments, dict):
        return {}, False, get_message(ErrorCode.TOOL_INVALID_ARGUMENT, arg="arguments")
    try:
        result = await asyncio.wait_for(definition.run(arguments), timeout=timeout_s)
    except asyncio.TimeoutError:
        logger.warning("Tool %s timed out after %.1fs", name, timeout_s)
        return {}, False, get_message(ErrorCode.TOOL_EXECUTION_TIMEOUT)
    except Exception as exc:
        logger.warning("Tool %s failed: %s", name, exc)
        return {}, False, get_message(ErrorCode.TOOL_EXECUTION_FAILED, name=name, error=str(exc))
    return result if isinstance(result, dict) else {"result": result}, True, None


def _chunk_text(chunk: Any) -> str:
    """Extract text from a stream chunk (ChatGenerationChunk / ChatChunk / str)."""
    if isinstance(chunk, str):
        return chunk
    if hasattr(chunk, "response_delta"):
        return chunk.response_delta or ""
    if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
        content = chunk.message.content
        return content if isinstance(content, str) else str(content or "")
    if hasattr(chunk, "content"):
        content = chunk.content
        return content if isinstance(content, str) else str(content or "")
    return str(chunk) if chunk else ""


async def run_tool_loop(
    *,
    llm: Any,
    messages: List[Any],
    tools_for_llm: List[Dict[str, Any]],
    tool_registry: Any,
    capsule: Any,
    iq: Any = None,
    approval_gate: Any = None,
    subject: Any = None,
    max_iterations: int = MAX_TOOL_ITERATIONS,
    usage: Any = None,
) -> AsyncIterator[Union[str, ToolStreamEvent]]:
    """Run the native function-calling loop until a final response (or cap).

    Yields text tokens and ToolStreamEvent items. ``messages`` is mutated in
    place (assistant tool_calls + tool results appended) so the caller's
    conversation trace reflects the full tool timeline.

    Every LLM round passes ``tools=tools_for_llm`` through to LiteLLM —
    native function calling only, never regex parsing.

    ``subject`` is the ``ToolSubject`` (user/tenant/roles/gate) every tool
    call is authorized under — SOMA-ARCH-TOOLS-001 §11. No subject means no
    principal, and ``decide_and_authorize_tool`` fails closed to ``denied``.

    ``usage`` is an optional sink with ``.absorb(dict | None)`` (see
    ``TurnUsage``). After each LLM round the wrapper's provider-reported
    token counts are folded into it. The provider may report none — the
    sink stays unknown rather than inventing a count.
    """
    from admin.llm.services.litellm_schemas import (
        ToolCallDeltasChunk,
        ToolCallsChunk,
    )

    def _drain_llm_usage() -> None:
        if usage is None:
            return
        pop = getattr(llm, "pop_usage", None)
        if callable(pop):
            usage.absorb(pop())

    for iteration in range(1, max_iterations + 1):
        response_text: List[str] = []
        pending_tool_calls: List[Any] = []
        seen_call_keys: set[str] = set()

        # tool_choice is only legal alongside tools; sending it with none is a
        # provider error.
        _tools = tools_for_llm or None
        _kwargs = {"tool_choice": "auto"} if _tools else {}
        stream = llm._astream(messages=messages, tools=_tools, **_kwargs)
        async for chunk in stream:
            if isinstance(chunk, ToolCallsChunk):
                pending_tool_calls = list(chunk.tool_calls)
                continue
            if isinstance(chunk, ToolCallDeltasChunk):
                for delta in chunk.deltas:
                    # Index is the stable assembly key (matches
                    # ToolCallAccumulator); id may be absent on arg fragments.
                    key = f"idx:{delta.index}"
                    if key not in seen_call_keys:
                        seen_call_keys.add(key)
                        yield ToolStreamEvent(
                            type=TOOL_EVENT_CALL,
                            payload={
                                "iteration": iteration,
                                "index": delta.index,
                                "tool_call_id": delta.id,
                                "name": delta.name,
                            },
                        )
                    if delta.arguments:
                        yield ToolStreamEvent(
                            type=TOOL_EVENT_DELTA,
                            payload={
                                "iteration": iteration,
                                "index": delta.index,
                                "tool_call_id": delta.id,
                                "arguments_delta": delta.arguments,
                            },
                        )
                continue
            token = _chunk_text(chunk)
            if token:
                response_text.append(token)
                yield token

        _drain_llm_usage()

        if not pending_tool_calls:
            # Final response — the model is done.
            return

        # Phase 9: real tool execution against the capsule ToolRegistry.
        messages.append(build_assistant_tool_message(pending_tool_calls))
        for tc in pending_tool_calls:
            name = tc.name
            args = tc.arguments if isinstance(tc.arguments, dict) else {}
            # Memory tools: ALWAYS use the Capsule tenant. Never accept LLM
            # "default" / empty — that is cross-tenant mixing (T-5).
            if name.startswith("memory_") and isinstance(args, dict):
                cap_tenant = getattr(capsule, "tenant_id", None)
                if cap_tenant:
                    args = {**args, "tenant_id": str(cap_tenant)}
                elif str(args.get("tenant_id") or "").strip().lower() in (
                    "",
                    "default",
                    "standalone",
                    "none",
                ):
                    args = {**args, "tenant_id": ""}  # tool raises fail-closed
            # Durable jobs: identity comes from the capsule, never the model
            # (T-5). research_report starts a Temporal workflow under this
            # tenant; an empty tenant makes the tool fail closed.
            if name == "research_report" and isinstance(args, dict):
                cap_tenant = getattr(capsule, "tenant_id", None)
                cap_id = getattr(capsule, "id", None)
                args = {
                    **args,
                    "tenant_id": str(cap_tenant or ""),
                    "capsule_id": str(cap_id or ""),
                }
            started = time.perf_counter()
            # ONE policy choke before anything executes (SOMA-ARCH-TOOLS-001
            # §11): capsule tool_policy (unlisted = approval), egress for
            # network tools, then RBAC → OPA → SpiceDB → capsule scope via
            # UnifiedGate. Fail-closed: the choke returns "denied" on any
            # error, and a denied tool is a terminal result, not a loop.
            decision = await decide_and_authorize_tool(subject, capsule, name, args, iq)
            display_args = args if isinstance(args, dict) else {}

            if decision == "approval_required":
                yield ToolStreamEvent(
                    type=TOOL_EVENT_APPROVAL,
                    payload={
                        "iteration": iteration,
                        "tool_call_id": tc.id,
                        "name": name,
                        "arguments": display_args,
                    },
                )
                # Real approve/deny round-trip. The gate is created by the
                # transport (the WS consumer opens a future per request and
                # resolves it from the client's `tool.approval`). With no gate
                # attached there is no human to ask, so the answer is no -
                # fail closed, never auto-approve.
                approved = False
                if approval_gate is not None:
                    try:
                        approved = bool(
                            await approval_gate.wait(tc.id, TOOL_APPROVAL_TIMEOUT_S)
                        )
                    except Exception as exc:
                        logger.warning("tool approval wait failed: %s", exc)
                        approved = False
                if not approved:
                    # Refused (or nobody to ask). A denied tool is a terminal
                    # tool result, not a reason to loop.
                    error = get_message(ErrorCode.TOOL_EXECUTION_DENIED)
                    if name == "memory_forget":
                        # The model must not invent erasure after a deny.
                        error = (
                            f"{error} — memory_forget was NOT executed. "
                            "The memory still exists. Do not tell the user "
                            "that any name, fact, or preference was removed "
                            "from memory."
                        )
                    yield ToolStreamEvent(
                        type=TOOL_EVENT_DONE,
                        payload={
                            "iteration": iteration,
                            "tool_call_id": tc.id,
                            "name": name,
                            "arguments": display_args,
                            "result": None,
                            "ok": False,
                            "error": error,
                            "duration_ms": 0,
                            "status": "denied",
                        },
                    )
                    messages.append(build_tool_result_message(tc.id, {}, False, error))
                    continue
                # Approved: the human said yes. Fall through and execute.
                decision = "auto_execute"

            if decision == "denied":
                error = get_message(ErrorCode.TOOL_POLICY_DENIED)
                yield ToolStreamEvent(
                    type=TOOL_EVENT_DONE,
                    payload={
                        "iteration": iteration,
                        "tool_call_id": tc.id,
                        "name": name,
                        "arguments": display_args,
                        "result": None,
                        "ok": False,
                        "error": error,
                        "duration_ms": 0,
                        "status": "denied",
                    },
                )
                messages.append(build_tool_result_message(tc.id, {}, False, error))
                continue

            if args is None:
                error = get_message(ErrorCode.TOOL_INVALID_ARGUMENT, arg="arguments")
                yield ToolStreamEvent(
                    type=TOOL_EVENT_DONE,
                    payload={
                        "iteration": iteration,
                        "tool_call_id": tc.id,
                        "name": name,
                        "arguments": {},
                        "result": None,
                        "ok": False,
                        "error": error,
                        "duration_ms": 0,
                        "status": "invalid_arguments",
                    },
                )
                messages.append(build_tool_result_message(tc.id, {}, False, error))
                continue

            result, ok, error = await execute_tool_call(tool_registry, name, args)
            duration_ms = int((time.perf_counter() - started) * 1000)
            yield ToolStreamEvent(
                type=TOOL_EVENT_DONE,
                payload={
                    "iteration": iteration,
                    "tool_call_id": tc.id,
                    "name": name,
                    "arguments": args,
                    "result": result,
                    "ok": ok,
                    "error": error,
                    "duration_ms": duration_ms,
                    "status": "executed" if ok else "error",
                },
            )
            messages.append(build_tool_result_message(tc.id, result, ok, error))

        # Next iteration: the model sees the tool results and continues.

    # The chain ran to its cap. The user asked a question and deserves an
    # answer, not a status line. One final call with tools disabled produces
    # it. This round runs only when a tool chain actually happened: a plain
    # turn returns above the moment the model stops calling tools.
    stream = llm._astream(messages=messages, tools=None)
    async for chunk in stream:
        text = _chunk_text(chunk)
        if text:
            yield text


__all__ = [
    "MAX_TOOL_ITERATIONS",
    "TOOL_EVENT_APPROVAL",
    "TOOL_EVENT_CALL",
    "TOOL_EVENT_DELTA",
    "TOOL_EVENT_DONE",
    "ToolPolicy",
    "ToolStreamEvent",
    "ToolSubject",
    "build_assistant_tool_message",
    "build_tool_result_message",
    "decide_and_authorize_tool",
    "egress_permitted",
    "execute_tool_call",
    "resolve_tool_policy",
    "run_tool_loop",
]
