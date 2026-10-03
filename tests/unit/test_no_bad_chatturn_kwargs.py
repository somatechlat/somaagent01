"""Every ChatTurn construction site must pass only real fields.

`ChatTurn` is a plain dataclass. There is no custom ``__init__`` and no
``**kwargs``, so an unknown field raises ``TypeError`` at construction. That
has now happened twice in production paths — once in the WebSocket consumer
(``capsule_id=``) and once in the Telegram/WhatsApp bridge — and both times
the exception was swallowed by a blanket ``except Exception``, so the user
simply got no reply.

This guard walks the whole tree and checks every call site.
"""

from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path

from admin.core.chat_orchestrator import ChatTurn

REPO_ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {f.name for f in fields(ChatTurn)}

# Files known to construct a ChatTurn. Grep keeps this honest: the test below
# also asserts the set matches what is actually in the tree.
_SEARCH_ROOTS = (
    "admin",
    "services",
    "config",
)


def _iter_python_files():
    for root in _SEARCH_ROOTS:
        base = REPO_ROOT / root
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts or "tests" in path.parts:
                continue
            yield path


def _chatturn_callsites() -> dict[str, list[tuple[int, set[str]]]]:
    """Return {file: [(lineno, {kwargs})]} for every ChatTurn(...) call."""
    found: dict[str, list[tuple[int, set[str]]]] = {}
    for path in _iter_python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:  # pragma: no cover - a broken file is its own failure
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = getattr(func, "id", None) or getattr(func, "attr", None)
            if name != "ChatTurn":
                continue
            kwargs = {kw.arg for kw in node.keywords if kw.arg is not None}
            found.setdefault(str(path.relative_to(REPO_ROOT)), []).append(
                (node.lineno, kwargs)
            )
    return found


def test_chatturn_has_no_capsule_id_field():
    """ChatTurn carries a Capsule instance, not a capsule id."""
    assert "capsule_id" not in ALLOWED


def test_every_chatturn_call_site_passes_only_real_fields():
    """No construction site may pass a field the dataclass does not declare."""
    sites = _chatturn_callsites()
    assert sites, "no ChatTurn call sites found - update this test"
    offenders = []
    for file, calls in sorted(sites.items()):
        for lineno, kwargs in calls:
            unknown = kwargs - ALLOWED
            if unknown:
                offenders.append(f"{file}:{lineno} -> {sorted(unknown)}")
    assert offenders == [], f"ChatTurn called with unknown fields: {offenders}"


def test_call_sites_include_the_known_entrypoints():
    """The three entry points that have each broken at least once."""
    sites = _chatturn_callsites()
    expected = {
        "services/gateway/consumers/chat.py",
        "services/bridge_worker/dispatcher.py",
        "admin/chat/api/chat.py",
    }
    missing = expected - set(sites)
    assert missing == set(), f"expected ChatTurn call sites disappeared: {missing}"
