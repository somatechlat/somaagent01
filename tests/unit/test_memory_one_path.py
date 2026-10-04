"""One memory path: every read and write goes through MemoryGateway.

``SomaBrainClient.remember/recall/forget`` are the raw brain client. Calling
them from product code is a second memory authority — a write that never
enters the durable outbox and a read that bypasses the ranked seam. The
chat orchestrator already writes through ``MemoryGateway``; these four
surfaces were left off-seam and must join it.

``admin/somabrain/api_router.py`` stays an HTTP surface. Its internals call
the gateway; the request/response shapes are mapped at the edge.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: Product code that must not touch the raw brain memory verbs.
OFF_SEAM_FILES = (
    "admin/agents/services/somabrain_integration.py",
    "admin/somabrain/api_router.py",
    "services/common/chat_service.py",
    "services/tool_executor/result_publisher.py",
)

#: The raw client's memory verbs. Not the seam.
FORBIDDEN_METHODS = frozenset({"remember", "recall", "forget"})


def _memory_client_calls(path: Path) -> list[str]:
    """Return ``attr.method`` for every SomaBrain* memory-verb call in the file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in FORBIDDEN_METHODS:
            continue
        # ``something.remember(...)`` where something is a client, not the gateway.
        value = func.value
        name = ""
        if isinstance(value, ast.Name):
            name = value.id
        elif isinstance(value, ast.Attribute):
            name = value.attr
        elif isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute):
            name = value.func.attr
        if "gateway" in name.lower():
            continue
        found.append(f"{name}.{func.attr}")
    return found


def test_off_seam_files_do_not_call_the_raw_brain_memory_verbs():
    for rel in OFF_SEAM_FILES:
        path = ROOT / rel
        calls = _memory_client_calls(path)
        assert calls == [], f"{rel} still calls raw brain memory verbs: {calls}"


def test_off_seam_files_use_the_memory_gateway():
    for rel in OFF_SEAM_FILES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert "get_memory_gateway" in src or "MemoryGateway" in src, (
            f"{rel} does not reference MemoryGateway"
        )
