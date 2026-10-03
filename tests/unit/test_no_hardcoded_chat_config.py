"""Chat-lane configuration must be wire-driven, not literals in code.

VIBE §4: NO hardcoded values. A tunable behaviour with a magic number in the
source cannot be operated, and two sites with the same literal drift apart.

Measured offenders in the chat lane:
- ``recall_limit = 10`` at three sites, while AgentIQ already derives a
  ``recall_limit`` that nothing read.
- ``salience: float = 0.5`` as a silent default.
- stream flush interval/cap as module literals.
"""

from __future__ import annotations

import inspect

from admin.core import chat_orchestrator as co
from services.gateway.consumers import chat as chat_mod


def test_recall_limit_comes_from_iq_not_a_literal():
    """The derived recall_limit must be the source, not a magic 10."""
    src = inspect.getsource(co)
    assert "recall_limit = 10" not in src, "recall_limit still hardcoded to 10"
    assert "iq.recall_limit" in src, "AgentIQ recall_limit is not consumed"


def test_stream_flush_values_resolve_through_settings():
    """Stream coalescing must be tunable at deploy time."""
    src = inspect.getsource(chat_mod)
    assert "get_memory_setting" in src or "settings" in src.lower()
    assert chat_mod._FLUSH_INTERVAL_S > 0
    assert chat_mod._FLUSH_INTERVAL_S < 0.1
    # Not a bare literal assigned at module scope.
    for line in src.splitlines():
        if line.startswith("_FLUSH_INTERVAL_S = "):
            assert "_stream_setting" in line or "get_memory_setting" in line, (
                f"_FLUSH_INTERVAL_S is a hardcoded literal: {line!r}"
            )
        if line.startswith("_FLUSH_MAX_CHARS = "):
            assert "_stream_setting" in line or "get_memory_setting" in line, (
                f"_FLUSH_MAX_CHARS is a hardcoded literal: {line!r}"
            )


def test_salience_default_is_resolved_not_literal():
    """Memory salience must be a setting, not a 0.5 in a signature."""
    src = inspect.getsource(co)
    assert "salience: float = 0.5" not in src, "salience default is a hardcoded literal"
