"""Module playwright."""

import subprocess
from pathlib import Path

from admin.core.helpers import files

# this helper ensures that playwright is installed in /lib/playwright
# should work for both docker and local installation


def get_playwright_binary():
    """Retrieve playwright binary.
        """

    pw_cache = Path(get_playwright_cache_dir())
    headless_shell = next(pw_cache.glob("chromium_headless_shell-*/chrome-*/headless_shell"), None)
    return headless_shell


def get_playwright_cache_dir():
    """Retrieve playwright cache dir.
        """

    return files.get_abs_path("tmp/playwright")


def ensure_playwright_binary():
    """Execute ensure playwright binary.
        """

    bin = get_playwright_binary()
    if not bin:
        cache = get_playwright_cache_dir()
        import os

        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = cache
        subprocess.check_call(["playwright", "install", "chromium", "--only-shell"], env=env)
    bin = get_playwright_binary()
    if not bin:
        raise Exception("Playwright binary not found after installation")
    return bin