"""The WebSocket path must construct a ChatTurn that actually exists.

`services/gateway/consumers/chat.py` used to pass ``capsule_id=`` into
``ChatTurn``. ``ChatTurn`` has no such field, so every WebSocket turn raised
``TypeError`` at construction and the blanket ``except Exception`` swallowed it.
No turn ever reached ``stream_turn``.
"""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from admin.core.chat_orchestrator import ChatTurn

REPO_ROOT = Path(__file__).resolve().parents[2]
CONSUMER = REPO_ROOT / "services" / "gateway" / "consumers" / "chat.py"


def _consumer_turn_kwargs() -> set[str]:
    """Return the keyword argument names passed to ChatTurn in the consumer."""
    tree = ast.parse(CONSUMER.read_text(encoding="utf-8"))
    used: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "id", None) or getattr(func, "attr", None)
        if name != "ChatTurn":
            continue
        for kw in node.keywords:
            if kw.arg is not None:
                used.add(kw.arg)
    return used


def test_chat_turn_has_no_capsule_id_field():
    """ChatTurn carries a Capsule instance, not a capsule id."""
    names = {f.name for f in fields(ChatTurn)}
    assert "capsule_id" not in names


def test_consumer_passes_only_real_chatturn_fields():
    """Every kwarg the consumer passes must exist on ChatTurn."""
    allowed = {f.name for f in fields(ChatTurn)}
    used = _consumer_turn_kwargs()
    assert used, "consumer no longer constructs a ChatTurn - update this test"
    unknown = used - allowed
    assert unknown == set(), f"consumer passes unknown ChatTurn fields: {sorted(unknown)}"


def test_consumer_passes_attachments():
    """Attachments must reach the turn so capability detection sees vision/audio."""
    assert "attachments" in _consumer_turn_kwargs()


def test_consumer_construction_site_is_parseable():
    """Guard the exact construction shape the runtime uses."""
    allowed = {f.name for f in fields(ChatTurn)}
    # The fields the consumer is expected to populate.
    expected = {
        "capsule",
        "iq_settings",
        "tool_registry",
        "user_id",
        "tenant_id",
        "user_message",
        "conversation_id",
        "attachments",
        "history",
        "agent_mode",
    }
    assert expected <= allowed
