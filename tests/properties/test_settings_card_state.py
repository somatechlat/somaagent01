"""Property: Settings card state consistency.

Validates: Requirements 7.6, 7.7, 7.8, 7.9 (collapse/expand behaviour, ARIA state, toggle hook).
Checks that the settings card component exposes toggle/expand/collapse helpers
and binds aria-expanded/controls on the header plus x-show/x-collapse on the body.
"""

import pathlib
import re


def test_settings_card_exposes_state_helpers_and_aria():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/components/settings/settings-card.js").read_text(encoding="utf-8")

    # State helpers present
    assert "toggle()" in text
    assert "expand()" in text
    assert "collapse()" in text

    # Header bindings include aria-expanded and aria-controls
    assert re.search(r":aria-expanded", text), "aria-expanded binding missing on header"
    assert re.search(r":aria-controls", text), "aria-controls binding missing on header"

    # Body bindings include x-show/x-collapse and aria-hidden
    assert "x-show" in text and "x-collapse" in text, "body collapse bindings missing"
    assert re.search(r":aria-hidden", text), "aria-hidden binding missing on body"
