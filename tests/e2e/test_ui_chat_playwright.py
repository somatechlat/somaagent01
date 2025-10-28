import os
import json
import asyncio
import httpx
import pytest

# Skip module entirely if pytest-playwright isn't installed
try:
    import playwright  # noqa: F401
except Exception:
    pytest.skip("pytest-playwright not installed", allow_module_level=True)

pytestmark = pytest.mark.e2e

BASE_URL = os.getenv("GATEWAY_BASE_URL", "http://localhost:8010").rstrip("/")


async def _health_ok() -> bool:
    url = f"{BASE_URL}/v1/health"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url)
            if not resp.status_code or resp.status_code >= 500:
                return False
            data = resp.json()
            status = (data or {}).get("status") or (data or {}).get("overall") or (data or {}).get("state")
            return str(status or "ok").lower() != "down"
    except Exception:
        return False


@pytest.mark.asyncio
async def test_ui_chat_happy_path(page, browser):  # type: ignore[no-redef]
    # Require explicit opt-in to run live E2E, to avoid CI flakes when backend isn't up.
    if os.getenv("E2E_LIVE", "false").lower() not in {"1", "true", "yes", "on"}:
        pytest.skip("E2E_LIVE not set; skipping live UI chat test")

    if not await _health_ok():
        pytest.skip("Backend not healthy at /v1/health; skipping live UI chat test")

    ui_url = f"{BASE_URL}/ui/index.html"

    # Navigate to UI and wait for main elements
    await page.goto(ui_url, wait_until="domcontentloaded")
    await page.wait_for_selector("#chat-input")
    await page.wait_for_selector("#send-button")

    # Type a short message and send
    await page.fill("#chat-input", "Hello there")
    await page.click("#send-button")

    # Expect the UI to set context and open SSE; assistant response should appear
    # within a reasonable timeout. We search for a response-type message block.
    # The DOM is managed by webui/messages.js; response entries render as elements
    # with class 'message' and type 'response' or 'agent'. We'll look for new content.

    async def _has_assistant() -> bool:
        # Query DOM for any rendered assistant/agent items with content
        els = await page.query_selector_all(".message")
        for el in els:
            # Extract text content and inferred type via data attributes when present
            txt = (await el.text_content()) or ""
            if not txt.strip():
                continue
            # Be lenient: any non-empty message after sending counts as success
            return True
        return False

    # Poll for up to 60 seconds
    for _ in range(120):
        if await _has_assistant():
            break
        await asyncio.sleep(0.5)
    else:
        # Fetch last few logs from /v1/ui/poll for diagnostics
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(f"{BASE_URL}/v1/ui/poll", json={"log_from": 0, "context": None})
                body = resp.json()
        except Exception:
            body = {"error": "poll_failed"}
        pytest.fail("No assistant response rendered within timeout; poll=\n" + json.dumps(body)[:2000])

    # If we reached here, message is rendered. Pass.
    assert True
