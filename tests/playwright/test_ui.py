import os
import re

UI_BASE_URL = (
    os.getenv("WEB_UI_BASE_URL") or f"http://127.0.0.1:{os.getenv('GATEWAY_PORT','21016')}/ui"
)


def test_basic_chat_flow(page):
    """End‑to‑end UI smoke test against the running container."""
    # Open the UI
    page.goto(UI_BASE_URL)
    # Wait for the chat input to be attached and visible – the sidebar overlay is hidden by default
    page.wait_for_selector("#chat-input", timeout=10000)

    # Verify chat input exists
    chat_input = page.wait_for_selector("#chat-input", timeout=3000)
    assert chat_input.is_visible(), "Chat input textarea not visible"

    # Send a message
    chat_input.fill("Hello, Agent Zero!")
    chat_input.press("Enter")

    # Wait for assistant response – look for AI message element
    response_selector = ".message-ai, .message-agent-response"
    page.wait_for_selector(response_selector, timeout=30000)

    # Grab the first matching element's text
    response_text = page.inner_text(response_selector)
    assert response_text, "Assistant response was empty"
    assert re.search(
        r"hello|hi|greeting", response_text, re.I
    ), f"Unexpected response content: {response_text!r}"

    # ---- Additional E2E verification: Save Chat ----
    # Expect a download when clicking the Save Chat button (id=loadChat)
    with page.expect_download() as download_info:
        page.click("#loadChat")
    download = download_info.value
    # Verify the download has a JSON filename (Agent Zero saves chats as .json)
    assert download.suggested_filename.endswith(
        ".json"
    ), f"Unexpected download filename: {download.suggested_filename}"
    # Optionally, you could save the file to a temp location and inspect its contents:
    # path = download.path()
    # assert path.read_text().strip().startswith('{'), "Downloaded chat file does not contain JSON"
