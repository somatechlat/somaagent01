import os

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

BASE_URL = (
    os.getenv("WEB_UI_BASE_URL")
    or os.getenv("UI_BASE_URL")
    or f"http://localhost:{os.getenv('GATEWAY_PORT','21016')}/ui"
)


@pytest.mark.smoke
@pytest.mark.playwright
def test_ui_has_no_console_errors(page):
    # Collect console and pageerror events
    console_messages = []
    page.on("console", lambda msg: console_messages.append((msg.type, msg.text)))
    page.on("pageerror", lambda exc: console_messages.append(("pageerror", str(exc))))
    failed_requests = []
    page.on(
        "requestfailed",
        lambda req: failed_requests.append(
            (req.url, req.failure.value if req.failure else "failed")
        ),
    )
    bad_responses = []
    page.on(
        "response",
        lambda resp: bad_responses.append((resp.url, resp.status)) if resp.status >= 400 else None,
    )

    # Try to load the UI; skip if not reachable in a reasonable time
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=10000)
    except PlaywrightTimeoutError:
        pytest.skip(f"UI not reachable at {BASE_URL}; skipping console check")

    # Give the page a moment to finish bootstrapping
    page.wait_for_timeout(1200)

    # Fail on any high-severity console error or pageerror
    errors = [(t, m) for (t, m) in console_messages if t in ("error", "pageerror")]

    if errors or failed_requests or any(status >= 400 for _, status in bad_responses):
        print("--- CONSOLE ERRORS ---")
        for t, m in errors:
            print(t, m)
        if failed_requests:
            print("--- REQUEST FAILED ---")
            for url, reason in failed_requests:
                print(reason, url)
        bads = [(u, s) for (u, s) in bad_responses if s >= 400]
        if bads:
            print("--- BAD RESPONSES ---")
            for url, status in bads:
                print(status, url)
    assert (
        not errors and not failed_requests and not any(status >= 400 for _, status in bad_responses)
    ), "UI console must be clean of errors on load"
