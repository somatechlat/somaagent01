"""Property: Responsive layout breakpoints.

Validates: Requirements 2.6, 2.7
Ensures layouts.css defines tablet and mobile breakpoint rules.
"""

import pathlib


def test_layout_breakpoints_exist():
    repo = pathlib.Path(__file__).resolve().parents[2]
    text = (repo / "webui/design-system/layouts.css").read_text(encoding="utf-8")

    assert "@media (max-width: 1024px)" in text, "Tablet breakpoint missing"
    assert "@media (max-width: 768px)" in text, "Mobile breakpoint missing"

    assert "grid-template-areas" in text
    assert "app-shell" in text
