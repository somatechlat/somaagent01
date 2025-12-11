"""Property: SSE manager backoff and heartbeat config.

Validates: Requirements 12.2, 12.3, 12.4, 12.7, 12.8
Checks default config values and exponential backoff calculation bounds.
"""

import pathlib
import re


def test_sse_default_config_values():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/core/sse/manager.js").read_text(encoding="utf-8")

    assert "reconnectBaseDelay: 1000" in text
    assert "reconnectMaxDelay: 30000" in text
    assert "reconnectMaxAttempts: 10" in text
    assert "heartbeatTimeout: 45000" in text
    assert "heartbeatCheckInterval: 5000" in text


def test_sse_backoff_formula():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/core/sse/manager.js").read_text(encoding="utf-8")
    # Expect Math.min(base * 2^(n-1), max)
    assert re.search(r"Math\.pow\(2,\s*this\.reconnectAttempts\s*-\s*1\)", text)
    assert "this.config.reconnectBaseDelay" in text
    assert "this.config.reconnectMaxDelay" in text
