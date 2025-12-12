"""Property: Message role styling.

Validates: Requirements 4.2, 4.3 (user vs assistant alignment, accenting, avatars).
Checks chat.css contains role-specific styling for user/assistant messages.
"""

import pathlib
import re


def test_role_specific_classes_and_styles_present():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/design-system/chat.css").read_text(encoding="utf-8")

    # User message: reversed flex, accent bubble, right alignment
    assert ".message-user" in text, "User message class missing"
    assert re.search(r"\.message-user[^}]*margin-left:\s*auto", text, re.S)
    assert re.search(r"\.message-user\s+\.message-bubble[^}]*background", text, re.S)

    # Assistant message: left alignment with accent border and avatar glow
    assert ".message-assistant" in text, "Assistant message class missing"
    assert re.search(r"\.message-assistant\s+\.message-bubble[^}]*border-left", text, re.S)
    assert re.search(r"\.message-assistant\s+\.avatar", text, re.S)
