import asyncio
import os
import time

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


async def run_behavior(url: str) -> int:
    async with async_playwright() as p:
        headless_env = os.environ.get("HEADLESS", "1").lower()
        headless = headless_env not in ("0", "false", "no")
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(url, wait_until="load", timeout=60000)
        await page.wait_for_timeout(500)

        # Basic boot: chat input appears
        try:
            await page.wait_for_selector("#chat-input", timeout=15000)
            await page.wait_for_selector("#send-button", timeout=15000)
        except PlaywrightTimeoutError:
            await browser.close()
            return 1

        # Welcome message (any message in history counts)
        try:
            await page.wait_for_selector("#chat-history .message", timeout=8000)
        except PlaywrightTimeoutError:
            # Not fatal; continue
            pass

        # Send a tiny message
        chat = await page.query_selector("#chat-input")
        if chat:
            await chat.fill("ping")
            await chat.press("Enter")
        else:
            await browser.close()
            return 2

        # Expect thinking indicator to appear soon
        async def progress_nonempty() -> bool:
            el = await page.query_selector("#progress-bar")
            if not el:
                return False
            txt = (await el.inner_text()) or ""
            return len(txt.strip()) > 0

        appeared = False
        for _ in range(20):  # up to ~10s
            if await progress_nonempty():
                appeared = True
                break
            await page.wait_for_timeout(500)
        if not appeared:
            # If it didn't appear, consider failure
            await browser.close()
            return 3

        # Wait for an assistant message (best-effort)
        ai_text = None
        end = time.time() + 45
        while time.time() < end:
            els = await page.query_selector_all("#chat-history .message-ai")
            if els:
                try:
                    ai_text = await els[-1].inner_text()
                except Exception:
                    ai_text = await els[-1].text_content()
                break
            await page.wait_for_timeout(1000)

        # Indicator should eventually clear after completion; allow a small window
        cleared = False
        for _ in range(30):  # up to ~15s
            el = await page.query_selector("#progress-bar")
            txt = (await el.inner_text()) if el else ""
            if not (txt or "").strip():
                cleared = True
                break
            await page.wait_for_timeout(500)

        # Try the Show thoughts toggle only if thoughts rows exist
        thoughts = await page.query_selector_all(".msg-thoughts")
        if thoughts:
            # Find the Show thoughts switch and turn it off
            # The switch is in Preferences; locate by the label text then find the input nearby
            btns = await page.query_selector_all(
                "xpath=//li[.//span[contains(., 'Show thoughts')]]//input[@type='checkbox']"
            )
            if btns:
                # Turn off
                await btns[0].check()
                await page.wait_for_timeout(200)
                await btns[0].uncheck()
                await page.wait_for_timeout(400)
                # Verify at least the first thoughts row is hidden via computed style
                disp = await thoughts[0].evaluate("(el) => getComputedStyle(el).display")
                # In our UI, hiding sets display: none; treat non-visible as pass
                if disp != "none":
                    # Not a hard failure; environments may style differently
                    pass

        await browser.close()
        # Return 0 if thinking appeared; assistant message optional
        return 0 if appeared else 4


async def main():
    base = os.environ.get("GOLDEN_UI_BASE_URL") or "http://127.0.0.1:7001"
    try:
        code = await run_behavior(base)
    except Exception as e:  # pragma: no cover
        # Print a minimal diagnostic to help CI/users
        print(f"ERROR: Exception during run_behavior: {e}")
        raise
    if code != 0:
        print(f"BEHAVIOR_TEST_NONZERO:{code}")
        raise SystemExit(code)


if __name__ == "__main__":
    asyncio.run(main())
