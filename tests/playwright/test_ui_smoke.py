import asyncio
import os
import time

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def run_test():
    # Single-origin rule: always target the Gateway (serves UI + /v1 APIs)
    url = os.environ.get('WEB_UI_BASE_URL', 'http://127.0.0.1:21016/')
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        console_messages = []
        page.on('console', lambda msg: console_messages.append((msg.type, msg.text)))
        page.on('pageerror', lambda exc: console_messages.append(('pageerror', str(exc))))

        responses = []

        async def on_response(response):
            try:
                responses.append((response.status, response.url))
            except Exception:
                pass

        page.on('response', on_response)

        # Open UI (wait for full load, longer timeout)
        await page.goto(url, wait_until='load', timeout=60000)
        await page.wait_for_timeout(1500)

        print('--- CONSOLE MESSAGES ---')
        for t, m in console_messages:
            print(t, m)

        print('\n--- NETWORK RESPONSES (first 40) ---')
        for status, u in responses[:40]:
            print(status, u)

        # Try to send a chat message
        try:
            await page.wait_for_selector('#chat-input', timeout=15000)
            await page.wait_for_selector('#send-button', timeout=15000)
            chat = await page.query_selector('#chat-input')
            send_btn = await page.query_selector('#send-button')
            if chat and send_btn:
                await chat.fill('Hello from Playwright')
                # Wait for the POST to Gateway message endpoint
                try:
                    async with page.expect_response(lambda r: '/v1/session/message' in r.url and r.request.method == 'POST', timeout=20000) as resp_info:
                        await send_btn.click()
                    resp = await resp_info.value
                    print('Message async response status:', resp.status)
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

        await browser.close()


if __name__ == '__main__':
    asyncio.run(run_test())
