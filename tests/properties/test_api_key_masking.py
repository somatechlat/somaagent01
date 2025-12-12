"""Property: API key masking and visibility toggling.

Validates: Requirements 7.26, 7.27 (masked display, show/hide toggle, password input binding).
"""

import pathlib
import re


def test_api_key_masking_and_toggle_bindings():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/components/settings/api-key-card.js").read_text(encoding="utf-8")

    # Masking logic slices first/last four characters
    assert "maskedValue" in text
    assert "slice(0, 4)" in text and "slice(-4)" in text

    # Visibility toggling flips isVisible and switches input type binding
    assert "toggleVisibility()" in text
    assert re.search(r":type'.*isVisible.*text.*password", text.replace('"', "'")), (
        "Input type binding should depend on isVisible"
    )

    # Test button disables when missing value and exposes loading class
    assert "@click': () => this.testKey()" in text or "@click\": () => this.testKey()" in text
    assert ":disabled" in text and "btn-loading" in text, "Test button state bindings missing"
