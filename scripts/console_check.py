#!/usr/bin/env python3
"""Simple Playwright script to capture browser console output and errors.
Usage: python3 scripts/console_check.py [BASE_URL]
If BASE_URL is omitted, defaults to http://localhost:21016
"""
import sys
import asyncio
from playwright.async_api import async_playwright

async def main(base_url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        console_messages: list[str] = []
        page_errors: list[str] = []
        # Capture console messages (type and text)
        def _on_console(msg):
            # msg.type() is a method; msg.text is an attribute in newer Playwright versions.
            msg_type = msg.type() if callable(msg.type) else getattr(msg, "type", "")
            msg_text = msg.text() if callable(msg.text) else getattr(msg, "text", "")
            console_messages.append(f"[{msg_type}] {msg_text}")
        page.on("console", _on_console)
        # Capture page errors (uncaught exceptions)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        try:
            await page.goto(base_url, wait_until="load", timeout=60000)
            # Wait a short while for any async console logs
            await asyncio.sleep(5)
        finally:
            await context.close()
            await browser.close()
        # Output results
        print("=== Console Messages ===")
        for line in console_messages:
            print(line)
        print("=== Page Errors ===")
        for e in page_errors:
            print(e)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:21016"
    asyncio.run(main(url))
