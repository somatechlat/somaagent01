"""Capture all console messages, page errors, and network request failures from the Web UI.

The script uses Playwright (async API) to launch a Chromium browser, navigate to the UI
served by the gateway (default http://localhost:21016), and records:

* ``console`` events – any ``console.log``, ``console.error`` etc.
* ``pageerror`` events – uncaught JavaScript exceptions.
* ``requestfailed`` events – network requests that failed (e.g., 4xx/5xx or DNS errors).

All captured information is written to ``ui_errors.log`` in a human‑readable format.
The script exits with a non‑zero status if any errors were observed, making it useful as
part of CI.

Usage:
    python -m scripts.capture_ui_errors

The script follows 
Playwright API and writes plain logs.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

from playwright.async_api import async_playwright, ConsoleMessage, Page, Request

# Destination log file – placed in the repository root for easy access.
# Resolve the log file path relative to the repository root.
LOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ui_errors.log"))


def _timestamp() -> str:
    """Return an ISO‑8601 timestamp for log entries."""
    return datetime.now(timezone.utc).isoformat()


async def _run() -> int:
    # Ensure the log file is fresh each run.
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        f.write(f"# UI error capture – {_timestamp()}\n")

    # Flag to indicate whether any error‑level messages were seen.
    had_errors = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page: Page = await context.new_page()

        # ---- Event listeners -------------------------------------------------
        async def on_console(msg: ConsoleMessage):
            nonlocal had_errors
            # ``msg.type()`` can be 'log', 'error', 'warning', etc.
            level = msg.type()
            text = msg.text()
            # Record location if available.
            location = msg.location()
            loc_str = f"{location['url']}:{location['lineNumber']}" if location else ""
            entry = f"{_timestamp()} CONSOLE {level.upper():<7} {loc_str} {text}\n"
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
            if level == "error":
                had_errors = True

        async def on_page_error(exception: Exception):
            nonlocal had_errors
            entry = f"{_timestamp()} PAGEERROR {str(exception)}\n"
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
            had_errors = True

        async def on_request_failed(request: Request):
            nonlocal had_errors
            # ``request.failure()`` returns a dict with ``errorText``.
            failure_info = await request.failure()
            error_text = failure_info.get("errorText") if failure_info else "unknown"
            entry = f"{_timestamp()} REQUESTFAILED {request.method} {request.url} – {error_text}\n"
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(entry)
            had_errors = True

        page.on("console", on_console)
        page.on("pageerror", on_page_error)
        page.on("requestfailed", on_request_failed)

        # ---- Navigate to the UI --------------------------------------------
        base_url = os.getenv("GATEWAY_BASE", "http://localhost:21016")
        try:
            await page.goto(base_url, wait_until="load", timeout=60000)
        except Exception as exc:
            print(f"Failed to load UI at {base_url}: {exc}", file=sys.stderr)
            return 1

        # Give the app a moment to settle – many components lazy‑load resources.
        await page.wait_for_timeout(5000)

        await context.close()
        await browser.close()

    return 0 if not had_errors else 1


def main() -> None:
    exit_code = asyncio.run(_run())
    if exit_code:
        print("\nErrors were captured – see ui_errors.log for details.")
    else:
        print("\nNo console or network errors detected.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
