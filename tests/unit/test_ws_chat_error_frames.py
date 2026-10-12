"""Every WebSocket close must carry an error frame the client can see.

A bare ``close(code=N)`` with no preceding ``error`` message is a silent
failure: the browser sees the socket die and has no reason why. The consumer
already has ``_send_error`` / ``_send_internal_error`` — every close path must
use one of them first.

B-* chat WS defect class: bare close, missing error frames.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CONSUMER = REPO_ROOT / "services" / "gateway" / "consumers" / "chat.py"


def _close_call_sites() -> list[tuple[int, list[str]]]:
    """Return (lineno, preceding_stmt_source_lines) for every ``self.close`` call."""
    src = CONSUMER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    lines = src.splitlines()
    sites: list[tuple[int, list[str]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "attr", None) or getattr(func, "id", None)
        if name != "close":
            continue
        # Collect the 5 source lines before this call for context.
        start = max(0, node.lineno - 6)
        context = lines[start : node.lineno]
        sites.append((node.lineno, context))
    return sites


def _has_error_frame_before(context_lines: list[str]) -> bool:
    """True when an error-send call appears in the preceding source lines."""
    joined = "\n".join(context_lines)
    return (
        "_send_error" in joined
        or "_send_internal_error" in joined
        or "send_json" in joined
    )


def test_every_ws_close_has_an_error_frame():
    """No bare close: each ``self.close`` must be preceded by an error frame."""
    sites = _close_call_sites()
    assert sites, "no close() calls found — consumer changed shape; update this test"
    bare = [
        (lineno, ctx)
        for lineno, ctx in sites
        if not _has_error_frame_before(ctx)
    ]
    assert not bare, (
        "bare WebSocket close() with no error frame before it at lines: "
        + ", ".join(str(n) for n, _ in bare)
    )
