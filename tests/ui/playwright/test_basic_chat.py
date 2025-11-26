"""Playwright smoke test: send a chat message via the real UI and verify an AI reply."""

import time

import pytest
from playwright.async_api import async_playwright

from services.common import env


async def _launch_page(headless: bool):
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)
    context = await browser.new_context()
    page = await context.new_page()
    return pw, browser, context, page


@pytest.mark.asyncio
async def test_chat_message_roundtrip():
    base_url = env.get("GATEWAY_BASE", "http://localhost:21016")
    headless_env = (env.get("HEADLESS", "1") or "1").lower()
    headless = headless_env not in {"0", "false", "no"}

    pw = browser = context = page = None
    try:
        pw, browser, context, page = await _launch_page(headless=headless)
        await page.goto(base_url, wait_until="load", timeout=60000)
        await page.wait_for_selector("#chat-input", timeout=20000)

        # Ensure baseline AI message count so we can detect the new response.
        selector = ".message-container.ai-container, .message-container.response-container"
        prev_ai = len(await page.query_selector_all(selector))

        message = "Hello from Playwright smoke test"
        await page.fill("#chat-input", message)
        await page.click("#send-button")

        # Wait for backend acknowledgement so we know the message really went out.
        # This ensures we don't race ahead before Kafka/SSE start streaming.
        # Playwright's async API may not expose ``wait_for_response`` on the ``Page``
        # object in some versions. Use ``wait_for_event('response')`` with a predicate
        # that matches the POST request to the chat session endpoint.
        await page.wait_for_event(
            "response",
            lambda resp: resp.request.method == "POST" and "/v1/session/message" in resp.url,
            timeout=20000,
        )

        # Poll until a new AI bubble appears (streaming can take several seconds).
        deadline = time.time() + 60
        response_text = None
        while time.time() < deadline:
            ai_nodes = await page.query_selector_all(selector)
            if len(ai_nodes) > prev_ai:
                last_ai = ai_nodes[-1]
                response_text = (await last_ai.inner_text()).strip()
                if response_text:
                    break
            await page.wait_for_timeout(500)

        assert response_text, "Assistant response never arrived via SSE"
        assert (
            "error" not in response_text.lower()
        ), f"Unexpected error in response: {response_text}"

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()
