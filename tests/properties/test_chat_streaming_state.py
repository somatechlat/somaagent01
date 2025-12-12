"""Property: Streaming state visualization.

Validates: Requirements 4.4, 4.5, 4.6 (streaming cursor, thinking indicator, in-progress styling).
"""

import pathlib
import re


def test_streaming_cursor_and_thinking_indicator_present():
    repo = pathlib.Path(__file__).resolve().parents[2]
    css = (repo / "webui/design-system/chat.css").read_text(encoding="utf-8")
    js = (repo / "webui/components/chat/assistant-message.js").read_text(encoding="utf-8")

    # CSS cursor and blink animation
    assert ".streaming-cursor" in css
    assert "keyframes blink" in css

    # Thinking indicator styles
    assert ".thinking-indicator" in css
    assert ".thinking-dots" in css

    # JS bindings show/hide cursor and thinking indicator based on streaming state
    assert re.search(r"isStreaming\s*&&\s*!this\.isComplete", js), "Cursor show condition missing"
    assert re.search(r"isStreaming\s*&&\s*!this\.content", js), "Thinking indicator condition missing"
