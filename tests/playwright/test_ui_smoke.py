import asyncio
import os
import time
import sys

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def run_test():
    # Single-origin rule: always target the Gateway (serves UI + /v1 APIs)
    url = os.environ.get('WEB_UI_BASE_URL') or os.environ.get('BASE_URL') or f"http://127.0.0.1:{os.getenv('GATEWAY_PORT','21016')}"
    async with async_playwright() as p:
        # Allow GUI mode when HEADLESS env var is '0' or 'false'
        headless_env = os.environ.get('HEADLESS', '1').lower()
        headless = not (headless_env in ('0', 'false', 'no'))
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        console_messages = []
        page.on('console', lambda msg: console_messages.append((msg.type, msg.text)))
        page.on('pageerror', lambda exc: console_messages.append(('pageerror', str(exc))))

        responses = []
        requests = []
        failed_requests = []

        async def on_response(response):
            try:
                responses.append((response.status, response.url))
            except Exception:
                pass

        page.on('response', on_response)

        def on_request(req):
            try:
                requests.append((req.method, req.url))
            except Exception:
                pass
        page.on('request', on_request)

        def on_request_failed(req):
            try:
                failed_requests.append((req.url, req.failure.error_text if req.failure else 'unknown error'))
            except Exception:
                pass
        page.on('requestfailed', on_request_failed)

        # Open UI (wait for full load, longer timeout)
        await page.goto(url, wait_until='load', timeout=60000)
        # Give the app a moment to boot and poll health
        await page.wait_for_timeout(800)
        # Wait until the status indicator reports not-down (ok or degraded)
        try:
            await page.wait_for_function(
                "() => { const el = document.getElementById('status-indicator'); return !!el && el.dataset && el.dataset.status && el.dataset.status !== 'down'; }",
                timeout=10000,
            )
        except PlaywrightTimeoutError:
            print('Health status did not reach ok/degraded in time; proceeding anyway')
            # proceed best-effort

        print('--- CONSOLE MESSAGES ---')
        for t, m in console_messages:
            print(t, m)

        print('\n--- NETWORK RESPONSES (first 40) ---')
        for status, u in responses[:40]:
            print(status, u)
        print('\n--- NETWORK REQUESTS (first 40) ---')
        for m, u in requests[:40]:
            print(m, u)

        if failed_requests:
            print('\n--- FAILED REQUESTS ---')
            for url, err in failed_requests:
                print('FAILED', url, err)

        # Try to send a chat message
        request_seen = False
        response_seen = False
        try:
            await page.wait_for_selector('#chat-input', timeout=15000)
            await page.wait_for_selector('#send-button', timeout=15000)
            chat = await page.query_selector('#chat-input')
            send_btn = await page.query_selector('#send-button')
            if chat:
                await chat.fill('Hello from Playwright')
                # Wait for the POST to Gateway message endpoint (trigger via Enter key to hit keydown handler)
                try:
                    # First, expect the request to be issued
                    async with page.expect_request(lambda r: '/v1/session/message' in r.url and r.method == 'POST', timeout=15000) as req_info:
                        await chat.press('Enter')
                    req = await req_info.value
                    print('Observed request:', req.method, req.url)
                    request_seen = True
                    # Optionally also wait for a response (may 500 when infra is down, that's okay)
                    try:
                        async with page.expect_response(lambda r: r.url == req.url and r.request.method == 'POST', timeout=15000) as resp_info:
                            pass
                        resp = await resp_info.value
                        print('Message async response status:', resp.status)
                        response_seen = True
                    except PlaywrightTimeoutError:
                        print('No response observed for /v1/session/message within 15s (request was sent).')
                except PlaywrightTimeoutError:
                    print('Timed out waiting for /v1/session/message response')
            else:
                print('Chat input or send button not found')
        except PlaywrightTimeoutError:
            print('Chat controls did not appear in time')
        except Exception as e:
            print('Chat attempt failed:', repr(e))

        # Wait up to 30s for an AI reply element to appear in the DOM
        ai_msg = None
        end = time.time() + 30
        selectors = ['.message.ai', '.msg.ai', '.agent-message.ai', '.message.from-agent', '.message.system']
        while time.time() < end:
            for sel in selectors:
                elems = await page.query_selector_all(sel)
                if elems:
                    try:
                        ai_msg = await elems[-1].inner_text()
                    except Exception:
                        ai_msg = await elems[-1].text_content()
                    break
            if ai_msg:
                break
            await page.wait_for_timeout(1000)

        print('\n--- FINAL CONSOLE MESSAGES ---')
        for t, m in console_messages:
            print(t, m)

        if ai_msg:
            print('Found AI reply (truncated):', ai_msg[:400])
        else:
            print('No AI reply found in the DOM within 30s. Ensure workers are running and connected to Kafka/LLM.')

        # Emit a simple machine-readable summary and exit code.
        print(f"\nSMOKE RESULT: REQUEST_SENT={int(request_seen)}, RESPONSE_SEEN={int(response_seen)}, AI_REPLY_SEEN={int(bool(ai_msg))}")
        # Make the smoke tolerant in infra-down mode: pass if we at least saw the POST issued by the UI.
        if not request_seen:
            await browser.close()
            sys.exit(1)

        await browser.close()


if __name__ == '__main__':
    asyncio.run(run_test())
