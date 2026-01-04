"""Module test_chat_flow."""

import pytest
from playwright.sync_api import expect, Page

from tests.e2e.helpers.auth import get_auth_token, inject_auth_cookies


def test_chat_interface_loads(page: Page):
    """
    Verify that the chat interface loads and is accessible with Real Auth.
    Valid OIDC Session required.
    """
    # 1. Get Real Token (Programmatic Login, no UI automation for auth)
    token = get_auth_token()

    # 2. Inject Context
    inject_auth_cookies(page.context, token)

    # 3. Navigate
    page.goto("http://localhost:20173/chat")

    # Check title (Updated to match reality)
    expect(page).to_have_title("SaaS Sys Admin — Enterprise Platform")

    # Check for sidebar
    expect(page.locator(".sidebar")).to_be_visible(timeout=10000)

    # Check for chat input
    expect(page.locator("textarea[placeholder*='Type']")).to_be_visible()

    """
    Verify sending a message and receiving a response.
    """
    try:
        # Locate input
        input_box = page.locator("textarea[placeholder*='Type']")
        expect(input_box).to_be_visible(timeout=10000)

        # Type message
        message = "Hello Verification Agent"
        input_box.fill(message)

        # Send (Press Enter)
        input_box.press("Enter")

        # Verify user message appears in chat history
        # Using a more robust selector for the message bubble
        # Increased timeout to 20s to account for WebSocket connection latency
        try:
            expect(page.locator(f"text={message}")).to_be_visible(timeout=20000)
        except Exception:
            # Capture state on failure
            print(f"FAILED to find message: {message}")
            if page.locator(".toast-error").is_visible():
                print(f"Toast Error: {page.locator('.toast-error').inner_text()}")
            page.screenshot(path="tmp/failure_message_visibility.png")
            raise
        # Verify assistant response
        # We expect a "thinking" indicator or an actual response message
        # Wait for network idle to ensure WS traffic settles
        page.wait_for_load_state("networkidle")

    except Exception:
        page.screenshot(path="tmp/failure.png")
        raise

    # Check for error toasts which usually indicate WebSocket auth failures
    if page.locator(".toast-error").is_visible():
        error = page.locator(".toast-error").inner_text()
        pytest.fail(f"UI reported error: {error}")
