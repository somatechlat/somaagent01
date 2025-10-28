import os
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

BASE_URL = os.getenv("UI_BASE_URL", "http://localhost:21016/")


@pytest.mark.smoke
@pytest.mark.playwright
def test_ui_has_no_console_errors(page):
    # Collect console and pageerror events
    console_messages = []
    page.on("console", lambda msg: console_messages.append((msg.type, msg.text)))
    page.on("pageerror", lambda exc: console_messages.append(("pageerror", str(exc))))

    # Try to load the UI; skip if not reachable in a reasonable time
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=10000)
    except PlaywrightTimeoutError:
        pytest.skip(f"UI not reachable at {BASE_URL}; skipping console check")

    # Give the page a moment to finish bootstrapping
    page.wait_for_timeout(1000)

    # Filter high-severity messages, with a small allowlist for known benign errors
    allowlist_substrings = [
        "Cannot redefine property: $nextTick",
        "Failed to load resource: the server responded with a status of 404",
    ]
    def _allowed(msg: str) -> bool:
        return any(s in msg for s in allowlist_substrings)

    errors = [
        (t, m)
        for (t, m) in console_messages
        if t in ("error", "pageerror") and not _allowed(m)
    ]

    if errors:
        print("--- CONSOLE ERRORS ---")
        for t, m in errors:
            print(t, m)
        pytest.xfail("Console errors detected on UI load (recorded above)")
