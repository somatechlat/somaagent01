"""Orchestrator hook registry for Capsule Modules (WP D1).

Minimal but real registry that modules use to extend the agent loop, matching
the hook points from SOMA-A0-PARITY-001 §6.4 / Annex D.3.

Usage (from a module's ``hooks.py``)::

    from admin.modules.hooks import register_hook

    def _on_message_loop_start(ctx):
        return {"channel_context": ctx.get("channel")}

    register_hook("message_loop_start", _on_message_loop_start, module="mod_whatsapp")

The orchestrator calls :func:`run_hook` at the named points. Handlers are
callables ``fn(ctx: dict) -> Any``; the dict payload is hook-specific. Failures
in one handler never break the agent loop — errors are collected and returned.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable

logger = logging.getLogger(__name__)

HookHandler = Callable[[dict[str, Any]], Any]

# Hook points required for bridge/plugin parity (§6.4). Keep as the canonical
# set — unknown hook names are rejected at registration so typos surface early.
KNOWN_HOOKS: tuple[str, ...] = (
    "message_loop_start",  # before LLM — load channel context
    "system_prompt",  # prompt build — inject channel/persona
    "response_stream",  # tokens — TG draft edit / WA typing
    "tool_execute_after",  # tool done — forward result
    "process_chain_end",  # turn end — send reply to channel
    "monologue_end",  # session end — typing cleanup
    "job_loop",  # worker tick — poll WA/TG/IMAP
    "handle_exception",  # error — notify channel on failure
)

# Full Annex D.3 Python list for discoverability; only KNOWN_HOOKS are
# registerable today — the rest are reserved names reported by the API.
RESERVED_HOOKS: tuple[str, ...] = (
    "agent_init",
    "banners",
    "before_main_llm_call",
    "error_format",
    "hist_add_before",
    "hist_add_tool_result",
    "message_loop_end",
    "message_loop_prompts_before",
    "message_loop_prompts_after",
    "message_loop_result",
    "monologue_start",
    "reasoning_stream",
    "reasoning_stream_chunk",
    "reasoning_stream_end",
    "response_stream_chunk",
    "response_stream_end",
    "startup_migration",
    "tool_execute_before",
    "user_message_ui",
    "util_model_call_before",
    "webui_ws_connect",
    "webui_ws_disconnect",
    "webui_ws_event",
)


class UnknownHookError(ValueError):
    """Raised when registering against a hook name outside KNOWN_HOOKS."""


@dataclass(frozen=True)
class HookRegistration:
    """One registered handler."""

    hook: str
    module: str
    handler: HookHandler


# The registry itself: hook name -> ordered list of registrations.
_HOOK_REGISTRY: dict[str, list[HookRegistration]] = defaultdict(list)


def register_hook(
    hook: str,
    handler: HookHandler,
    *,
    module: str = "unknown",
) -> HookRegistration:
    """Register ``handler`` for ``hook``. Raises on unknown hook names."""

    if hook not in KNOWN_HOOKS:
        raise UnknownHookError(
            f"unknown hook '{hook}'; known hooks: {', '.join(KNOWN_HOOKS)}"
        )
    if not callable(handler):
        raise TypeError("hook handler must be callable")
    registration = HookRegistration(hook=hook, module=module, handler=handler)
    _HOOK_REGISTRY[hook].append(registration)
    logger.debug("hook registered: %s <- %s", hook, module)
    return registration


def unregister_module(module: str) -> int:
    """Drop all handlers registered by ``module``. Returns count removed."""

    removed = 0
    for hook in list(_HOOK_REGISTRY):
        before = len(_HOOK_REGISTRY[hook])
        _HOOK_REGISTRY[hook] = [r for r in _HOOK_REGISTRY[hook] if r.module != module]
        removed += before - len(_HOOK_REGISTRY[hook])
    return removed


def get_hooks(hook: str) -> list[HookRegistration]:
    """Return registered handlers for ``hook`` (empty list when none)."""

    return list(_HOOK_REGISTRY.get(hook, ()))


def list_registrations() -> dict[str, list[dict[str, str]]]:
    """Introspection payload for the modules API: hook → {module, handler}."""

    payload: dict[str, list[dict[str, str]]] = {}
    for hook in KNOWN_HOOKS:
        regs = _HOOK_REGISTRY.get(hook, [])
        payload[hook] = [
            {"module": r.module, "handler": getattr(r.handler, "__name__", repr(r.handler))}
            for r in regs
        ]
    return payload


def run_hook(hook: str, ctx: dict[str, Any] | None = None) -> list[Any]:
    """Invoke every handler for ``hook`` with ``ctx``.

    Returns the list of handler results (exceptions become ``None`` entries and
    are logged). Raises :class:`UnknownHookError` for unrecognized hook names so
    orchestrator wiring mistakes fail loudly at the call site.
    """

    if hook not in KNOWN_HOOKS:
        raise UnknownHookError(f"unknown hook '{hook}'")
    context = dict(ctx or {})
    results: list[Any] = []
    for registration in get_hooks(hook):
        try:
            results.append(registration.handler(context))
        except Exception:
            logger.exception("hook handler failed: %s/%s", registration.module, hook)
            results.append(None)
    return results


def run_system_prompt_hooks(ctx: dict[str, Any]) -> list[str]:
    """Convenience: collect string prompt fragments from ``system_prompt`` hooks."""

    fragments: list[str] = []
    for result in run_hook("system_prompt", ctx):
        if isinstance(result, str) and result.strip():
            fragments.append(result.strip())
        elif isinstance(result, list):
            fragments.extend(str(item).strip() for item in result if str(item).strip())
    return fragments
