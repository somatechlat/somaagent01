# Top-level pytest configuration
# Existing plugin registration
from pathlib import Path

pytest_plugins = ["playwright.sync_api"]


def pytest_ignore_collect(collection_path: Path, config):
    """Conditionally ignore Playwright tests unless explicitly requested.

    The function returns ``True`` (skip) for files inside the ``playwright``
    directory when the ``RUN_PLAYWRIGHT`` environment variable is not set.
    All other test files are collected normally.
    """
    import os

    if "playwright" in str(collection_path) and not os.getenv("RUN_PLAYWRIGHT"):
        return True
    return False
