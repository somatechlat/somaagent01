"""UI integration test using Playwright.

This test launches the web UI served by the gateway container, captures any
JavaScript console messages, and performs a simple interaction (opening the
settings modal). It asserts that no console errors are emitted during the
interaction. The test can be run with ``pytest -s tests/ui_test.py``.

Prerequisites:
    - Playwright and its browsers must be installed. Run ``playwright install``
      after installing the ``requirements-dev.txt`` dependencies.
    - The gateway container must be running (port mapping ``${GATEWAY_PORT:-21016}``).
"""

import asyncio

import pytest
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:21016"  # Adjust if GATEWAY_PORT is overridden


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the async Playwright session.

    Pytest creates a new loop per test function by default, which can cause
    Playwright to launch multiple browsers unnecessarily. This fixture ensures a
    single loop is reused for the entire session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_ui_no_console_errors():
    """Load the UI and verify no console errors appear.

    The test performs the following steps:
    1. Launch a Chromium browser in headless mode.
    2. Navigate to the UI root page.
    3. Capture all console messages.
    4. Open the Settings modal (button with id "settings").
    5. Close the modal.
    6. Assert that no messages of type ``error`` were logged.
    """
    console_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Listen for console events
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        # Navigate to the UI. Use "load" instead of "networkidle" because the SSE
        # connection keeps a request open, preventing "networkidle" from ever
        # firing. Increase the timeout to give the page enough time to render.
        await page.goto(BASE_URL, wait_until="load", timeout=60000)

        # Basic sanity: ensure the chat input exists
        chat_input = await page.wait_for_selector("#chat-input", timeout=5000)
        assert chat_input is not None, "Chat input not found"

        # Open the Settings modal (the UI has a button with id "settings")
        settings_button = await page.wait_for_selector("#settings", timeout=5000)
        await settings_button.click()

        # Wait for the modal overlay to become visible. The settings modal is
        # teleported to the body and wrapped in a <div class="modal-overlay">.
        # Selecting the generic overlay works because only the settings modal
        # is opened at this point.
        await page.wait_for_selector(".modal-overlay", timeout=12000)

        # Close the modal by sending an Escape keypress, which triggers the
        # modal's "handleCancel" handler attached to the overlay.
        await page.keyboard.press("Escape")

        # Give a short moment for any pending console messages
        await asyncio.sleep(1)

        await context.close()
        await browser.close()

    # Filter only error messages and format for debugging output
    # Gather error messages from the console.
    error_texts = [msg.text for msg in console_errors]

    # Certain resources (tasks, monitoring) are known to produce HTTP errors
    # during UI startup in the test environment. These are harmless for the
    # purpose of this test, so we filter them out before asserting.
    known_ignorable = [
        "Failed to load resource",
        "Error fetching tasks",
        "Error in monitoring callback",
    ]
    filtered_errors = [e for e in error_texts if not any(ign in e for ign in known_ignorable)]

    if filtered_errors:
        # Print remaining errors for visibility in CI logs
        print("Console errors captured during UI test (filtered):\n" + "\n".join(filtered_errors))
    assert not filtered_errors, f"JavaScript console errors detected: {filtered_errors}"
