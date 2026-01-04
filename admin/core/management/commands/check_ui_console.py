"""Playwright script to capture JavaScript console errors from the UI.

The UI is served by the Django gateway on the host port defined in the
Docker compose file (default ``21016``). This script launches a headless
Chromium browser, navigates to the root URL, and records any console
messages emitted by the page. Errors, warnings and other log levels are
collected and printed to stdout. The output can be redirected to a file for
further analysis.

Usage:
    python scripts/check_ui_console.py [--url http://localhost:21016]

Prerequisites:
    - ``playwright`` must be installed (``pip install playwright``).
    - Browser binaries must be installed (run ``playwright install`` once).

The script follows the project's 
annotations, minimal external dependencies, and explicit error handling.
"""

import argparse
import asyncio
from pathlib import Path
from typing import List

from playwright.async_api import async_playwright, ConsoleMessage, Page


async def capture_console(url: str) -> List[ConsoleMessage]:
    """Open ``url`` in a headless browser and return console messages.

    Args:
        url: The absolute URL to navigate to.

    Returns:
        A list of ``ConsoleMessage`` objects recorded during page load.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page: Page = await context.new_page()
        messages: List[ConsoleMessage] = []

        # Register a listener for console events.
        page.on("console", lambda msg: messages.append(msg))

        await page.goto(url, wait_until="networkidle")
        # Give a short pause for any delayed scripts.
        await asyncio.sleep(2)
        await browser.close()
        return messages


def format_message(msg: ConsoleMessage) -> str:
    """Format a Playwright ``ConsoleMessage`` for readable output."""
    return f"[{msg.type.upper():<7}] {msg.text}"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Capture UI console logs via Playwright")
    parser.add_argument(
        "--url",
        default="http://localhost:21016",
        help="Base URL of the UI (default: http://localhost:21016)",
    )
    args = parser.parse_args()

    print(f"Navigating to {args.url} …")
    messages = await capture_console(args.url)

    if not messages:
        print("No console messages captured.")
        return

    print("Console output captured (most recent first):")
    for msg in reversed(messages):
        print(format_message(msg))

    # Optionally write to a file for CI pipelines.
    out_path = Path("ui_console.log")
    out_path.write_text("\n".join(format_message(m) for m in messages))
    print(f"Full log written to {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
