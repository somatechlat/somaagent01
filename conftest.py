"""Test configuration for the Agent‑Zero repository.

Pytest does not automatically import ``sitecustomize`` when it is executed as a
module, so we ensure the repository root (and the internal ``python`` package)
are placed at the front of ``sys.path`` before any test modules are imported.
This mirrors the behaviour of the ``sitecustomize.py`` file but guarantees it
works in the pytest environment.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

PYTHON_PKG = os.path.join(REPO_ROOT, "python")
if PYTHON_PKG not in sys.path:
    sys.path.append(PYTHON_PKG)

# Debug: print sys.path when pytest loads conftest to verify ordering
print('DEBUG conftest sys.path start:', sys.path[:5])
# Additional debug: attempt to import the local "python" package and report the result.
try:
    import importlib
    spec = importlib.util.find_spec('python')
    print('DEBUG find_spec python:', spec)
    import python
    print('DEBUG imported python package from:', getattr(python, '__file__', None))
except Exception as e:
    print('DEBUG import error for python package:', e)
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
