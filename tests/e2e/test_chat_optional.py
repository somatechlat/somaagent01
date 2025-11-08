import os

import pytest
from playwright.sync_api import expect

BASE_URL = os.getenv("UI_BASE_URL", "http://localhost:21016/")
API_BASE = BASE_URL.rstrip("/") + "/v1"


@pytest.mark.smoke
@pytest.mark.chat
def test_send_message_and_await_assistant(page):
    if not os.getenv("RUN_CHAT_SMOKE"):
        pytest.skip("Set RUN_CHAT_SMOKE=1 to enable the chat flow smoke test.")

    # Quick health check – skip if gateway reports down/degraded core deps
    resp = page.request.get(API_BASE + "/health")
    assert resp.ok, f"health endpoint not OK: {resp.status}"
    data = resp.json()
    status = (data.get("status") or data.get("overall") or data.get("state") or "").lower()
    if status in ("down", "error"):
        pytest.skip(f"Gateway unhealthy: {status}")

    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_function("window.Alpine && !!window.Alpine.version")

    chat_input = page.locator("[data-testid='chat-input']")
    send_button = page.locator("[data-testid='send-button']")
    expect(chat_input).to_be_visible()
    chat_input.fill("Hello from smoke chat")
    send_button.click()

    # Await assistant response appearing in the chat history.
    # We look for any element rendered as an assistant response.
    assistant_locator = page.locator("#chat-history .message-agent-response")

    # Allow a generous timeout for first publish/consumer spin-up
    expect(assistant_locator.first).to_be_visible(timeout=45000)
