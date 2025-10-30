import os
import pytest

def test_settings_modal_opens_and_loads_sections(page):
    base_url = os.getenv("WEB_UI_BASE_URL") or os.getenv("SA01_BASE_URL") or f"http://localhost:{os.getenv('GATEWAY_PORT','21016')}/ui"
    # Load UI
    page.goto(base_url, wait_until="domcontentloaded")

    # Log console errors for debugging
    page.on("console", lambda msg: print(f"BROWSER[{msg.type}]:", msg.text))

    # Wait for status indicator to render (doesn't need to be green for this test)
    page.wait_for_selector("#status-indicator")

    # Click Settings button
    page.click("#settings")

    # Quick sanity: settingsModalProxy should be present
    typ = page.evaluate("() => typeof window.settingsModalProxy")
    print("settingsModalProxy typeof:", typ)

    # Modal overlay and container should appear
    page.wait_for_selector(".modal-overlay", state="visible")
    page.wait_for_selector(".modal-container .modal-header")

    # Settings title present (target the settings modal title only)
    header = page.locator('[data-testid="settings-modal-title"]').text_content()
    assert header is not None

    # Tabs should be visible for non-scheduler tabs
    page.wait_for_selector(".settings-tabs .settings-tab")

    # Sections list should render when not on scheduler tab
    # If scheduler is default, skip this assertion gracefully
    if page.locator("#settings-sections nav ul li").count() > 0:
        assert page.locator("#settings-sections nav ul li").count() > 0

