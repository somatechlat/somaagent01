"""Property: WebUI design tokens completeness.

Validates: Requirements 1.1, 1.2, 1.6, 1.7, 1.8, 1.9, 1.10
Ensures the design tokens file defines core typography, color, spacing,
radius, shadow, animation, z-index, semantic aliases, and layout variables,
and includes a dark theme block.
"""

import pathlib


def test_design_tokens_completeness():
    repo = pathlib.Path(__file__).resolve().parents[2]
    tokens = repo / "webui/design-system/tokens.css"
    content = tokens.read_text(encoding="utf-8")

    required_vars = [
        "--font-sans",
        "--font-mono",
        "--text-md",
        "--text-3xl",
        "--leading-normal",
        "--font-semibold",
        "--bg-primary",
        "--bg-secondary",
        "--surface-1",
        "--text-primary",
        "--text-secondary",
        "--border-color",
        "--accent-primary",
        "--accent-hover",
        "--success",
        "--warning",
        "--danger",
        "--info",
        "--glass-bg",
        "--glass-blur",
        "--gradient-ai",
        "--space-1",
        "--space-4",
        "--space-16",
        "--radius-md",
        "--radius-2xl",
        "--shadow-md",
        "--shadow-glow",
        "--duration-normal",
        "--ease-out",
        "--z-modal",
        "--c-accent",
        "--c-error-subtle",
        "--header-h",
        "--sidebar-w",
        "--sidebar-collapsed-w",
    ]

    for var in required_vars:
        assert var in content, f"Missing design token: {var}"

    # Dark theme block present
    assert '[data-theme="dark"]' in content, "Dark theme block missing"
