import asyncio
import os

# Support running via `pytest` and direct `python` by handling imports flexibly
try:
    # When collected by pytest from repo root
    from tests.playwright.test_ui_behavior_golden import run_behavior  # type: ignore
except Exception:
    try:
        # When executed directly from this folder
        from test_ui_behavior_golden import run_behavior  # type: ignore
    except Exception as e:  # pragma: no cover
        raise ImportError(f"Unable to import run_behavior from test_ui_behavior_golden: {e}")


async def main():
    base = (
        os.environ.get("WEB_UI_BASE_URL")
        or os.environ.get("BASE_URL")
        or f"http://127.0.0.1:{os.getenv('GATEWAY_PORT','21016')}"
    )
    code = await run_behavior(base)
    if code != 0:
        raise SystemExit(code)


if __name__ == "__main__":
    asyncio.run(main())
