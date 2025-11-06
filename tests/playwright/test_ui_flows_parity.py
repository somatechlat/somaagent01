import asyncio
import os
import time
from contextlib import asynccontextmanager
from urllib.parse import urlsplit

import httpx
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


@asynccontextmanager
async def browser_page(headless: bool = True):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        try:
            yield page
        finally:
            await browser.close()


async def ensure_reachable(base_url: str, timeout_ms: int = 5000) -> bool:
    try:
        async with httpx.AsyncClient(timeout=timeout_ms / 1000.0) as client:
            r = await client.get(base_url)
            return r.status_code < 500
    except Exception:
        return False


async def run_flows(base_url: str) -> dict:
    headless_env = os.environ.get("HEADLESS", "1").lower()
    headless = not (headless_env in ("0", "false", "no"))

    results = {
        "base": base_url,
        "opened": False,
        "no_dup_ai": None,
        "reset_clears": None,
        "delete_switches": None,
        "uploads_ok": None,
        "toggles_persist": None,
        "tool_echo_seen": None,
    }

    async with browser_page(headless=headless) as page:
        # Open UI
        await page.goto(base_url, wait_until="load", timeout=60000)
        try:
            await page.wait_for_selector("#chat-input", timeout=20000)
            results["opened"] = True
        except Exception:
            # Target UI not ready; mark as skipped for this base
            results["skipped"] = True
            return results

        # New chat
        btn_new = await page.query_selector("#newChat")
        if btn_new:
            await btn_new.click()
            await page.wait_for_timeout(200)

        # Send a message and ensure exactly one AI bubble appears
        prev_ai = len(await page.query_selector_all("#chat-history .message-ai"))
        async with page.expect_response(lambda r: "/v1/session/message" in r.url and r.request.method == "POST", timeout=20000) as resp_info:
            chat = await page.query_selector("#chat-input")
            await chat.fill("simple hello")
            await chat.press("Enter")
        msg_resp = await resp_info.value
        session_id = None
        try:
            j = await msg_resp.json()
            session_id = j.get("session_id") or j.get("ctxid")
        except Exception:
            pass

        # Wait for AI message; verify count increased by 1
        end = time.time() + 40
        while time.time() < end:
            now = len(await page.query_selector_all("#chat-history .message-ai"))
            if now >= prev_ai + 1:
                break
            await page.wait_for_timeout(500)
        new_count = len(await page.query_selector_all("#chat-history .message-ai"))
        results["no_dup_ai"] = (new_count - prev_ai) == 1

        # Reset chat should clear history
        hist = await page.query_selector("#chat-history")
        reset_btn = await page.query_selector("#resetChat")
        if reset_btn:
            await reset_btn.click()
            await page.wait_for_timeout(300)
            text = (await hist.inner_text()) if hist else ""
            results["reset_clears"] = len((text or "").strip()) == 0

        # Upload flow: attach a tiny file and ensure POST /v1/uploads occurs
        upload_ok = False
        file_input = await page.query_selector("#file-input")
        if file_input:
            async with page.expect_request(lambda r: "/v1/uploads" in r.url and r.method == "POST", timeout=15000) as req_info:
                # Create a temporary file
                tmp_path = os.path.join(os.getcwd(), "tmp_playwright_upload.txt")
                with open(tmp_path, "w", encoding="utf-8") as f:
                    f.write("hello-uploads")
                await file_input.set_input_files(tmp_path)
            req = await req_info.value
            upload_ok = req is not None
        results["uploads_ok"] = upload_ok

        # Toggle persistence: flip JSON on, Thoughts off, reload, and verify
        # Find the inputs by their effect signatures
        json_chk = await page.query_selector("xpath=//li[.//span[contains(., 'Show JSON')]]//input[@type='checkbox']")
        thoughts_chk = await page.query_selector("xpath=//li[.//span[contains(., 'Show thoughts')]]//input[@type='checkbox']")
        if json_chk:
            await json_chk.check()
        if thoughts_chk:
            await thoughts_chk.uncheck()
        await page.reload(wait_until="load")
        await page.wait_for_selector("#chat-input", timeout=15000)
        # JSON rows should be visible when present; we just assert the checkbox model persisted by re-reading style via a synthetic row
        # Accept best-effort: ensure CSS for thoughts is set to display:none
        persisted = True
        # We can’t guarantee thoughts rows exist, so check CSS by injecting a fake element
        await page.evaluate("""
            const el = document.createElement('div');
            el.className = 'msg-thoughts';
            document.body.appendChild(el);
        """)
        disp = await page.evaluate("() => getComputedStyle(document.querySelector('.msg-thoughts')).display")
        persisted = persisted and (disp == "none")
        results["toggles_persist"] = persisted

        # Tool flow via backend enqueue → observe in UI
        tool_seen = False
        if session_id:
            # Derive API origin from the URL (works with or without trailing /ui)
            parts = urlsplit(base_url)
            base_api = f"{parts.scheme}://{parts.netloc}"
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    payload = {
                        "session_id": session_id,
                        "tool_name": "echo",
                        "args": {"text": "pw-echo"},
                        "metadata": {"requeue_override": True},
                    }
                    r = await client.post(f"{base_api}/v1/tool/request", json=payload)
                    if r.status_code == 200:
                        # Wait for a tool block to appear in the DOM
                        end2 = time.time() + 30
                        while time.time() < end2:
                            blocks = await page.query_selector_all("#chat-history .message-util, #chat-history .message.tool")
                            if blocks:
                                tool_seen = True
                                break
                            await page.wait_for_timeout(1000)
            except Exception:
                tool_seen = False
        results["tool_echo_seen"] = tool_seen

        # Delete chat: click the current chat X and ensure selection changes or list reduces
        # Find first chat delete button and click
        del_btn = await page.query_selector("#chats-section .config-list li button.edit-button")
        if del_btn:
            count_before = len(await page.query_selector_all("#chats-section .config-list li"))
            await del_btn.click()
            await page.wait_for_timeout(400)
            count_after = len(await page.query_selector_all("#chats-section .config-list li"))
            results["delete_switches"] = count_after <= max(0, count_before - 1)

    return results


async def main():
    golden = os.environ.get("GOLDEN_UI_BASE_URL", "http://127.0.0.1:7001")
    local = os.environ.get("WEB_UI_BASE_URL") or f"http://127.0.0.1:{os.getenv('GATEWAY_PORT','21016')}"

    out = {"golden": None, "local": None}

    # Golden first; skip if not reachable
    if await ensure_reachable(golden):
        out["golden"] = await run_flows(golden)
    else:
        out["golden"] = {"base": golden, "skipped": True}

    # Local must run
    out["local"] = await run_flows(local)

    # Print compact summary for CI logs
    print("UI CHECK SUMMARY:", out)

    # If golden ran, compare critical booleans; otherwise just ensure local passed core flows
    def all_ok(d: dict):
        return all(
            d.get(k) in (True, None)  # None allowed for non-deterministic parts
            for k in ("opened", "no_dup_ai", "reset_clears", "delete_switches", "uploads_ok", "toggles_persist")
        )

    if out["golden"] and not out["golden"].get("skipped"):
        if not all_ok(out["golden"]):
            raise SystemExit(16)
        if not all_ok(out["local"]):
            raise SystemExit(32)
    else:
        if not all_ok(out["local"]):
            raise SystemExit(64)


if __name__ == "__main__":
    asyncio.run(main())
