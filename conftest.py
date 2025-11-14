"""Test configuration for the Agent‑Zero repository.

Pytest does not automatically import ``sitecustomize`` when it is executed as a
module, so we ensure the repository root (and the internal ``python`` package)
are placed at the front of ``sys.path`` before any test modules are imported.
This mirrors the behaviour of the ``sitecustomize.py`` file but guarantees it
works in the pytest environment.
"""

import os
import sys
from services.common import env as env_snapshot

# Ensure ``pytest.Request`` exists for type‑hinting in the test suite. The
# attribute is not provided by the public pytest API, so we add it here using the
# internal ``FixtureRequest`` class. This runs after pytest has been imported,
# guaranteeing the attribute is attached to the actual pytest module used by the
# tests.
try:
    import pytest
    from _pytest.fixtures import FixtureRequest

    if not hasattr(pytest, "Request"):
        pytest.Request = FixtureRequest  # type: ignore[attr-defined]
except Exception:
    # If pytest is not available for any reason, ignore – the tests that depend
    # on the attribute will fail appropriately.
    pass

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

PYTHON_PKG = os.path.join(REPO_ROOT, "python")
if PYTHON_PKG not in sys.path:
    sys.path.append(PYTHON_PKG)

# Debug: print sys.path when pytest loads conftest to verify ordering
print("DEBUG conftest sys.path start:", sys.path[:5])
# Additional debug: attempt to import the local "python" package and report the result.
try:
    import importlib

    spec = importlib.util.find_spec("python")
    print("DEBUG find_spec python:", spec)
    import python

    print("DEBUG imported python package from:", getattr(python, "__file__", None))
except Exception as e:
    print("DEBUG import error for python package:", e)
# Ensure .env is loaded so tests can see provider keys saved via the Settings page
try:
    from python.helpers.dotenv import load_dotenv as _a0_load_dotenv

    _a0_load_dotenv()
    # Optional: reflect that OPENAI_API_KEY is visible to pytest skip markers
    if env_snapshot.get("OPENAI_API_KEY"):
        print("DEBUG .env loaded: OPENAI_API_KEY detected")
    else:
        print("DEBUG .env loaded: OPENAI_API_KEY not set")
except Exception as _e:
    print("DEBUG dotenv load failed:", _e)
# Disable OTLP exports during tests to avoid network calls, but keep SDK enabled for context tests
# Keep OTel SDK enabled for context-related unit tests, but avoid any network exporters.
# Standard OTel envs to disable default exporters used by instrumentations.
os.environ.setdefault("OTEL_TRACES_EXPORTER", "none")
os.environ.setdefault("OTEL_METRICS_EXPORTER", "none")
os.environ.setdefault("OTEL_LOGS_EXPORTER", "none")
os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "")

# Note: POLICY_FAIL_OPEN is deprecated and ignored (fail-closed default).
# No override is set here; tests rely on local fixtures and bypass gating.

# Also inform our internal tracing helper to skip creating an OTLP exporter.
# This prevents attempts to connect to Jaeger during tests when modules import
# setup_tracing() at import time (e.g., the gateway).
os.environ.setdefault("OTEL_EXPORTER_OTLP_DISABLED", "true")

# Ensure test mode flag is set so selective authorization uses bypass logic
os.environ.setdefault("TESTING", "1")

# Make tool catalog conveniently available as `catalog` for tests that reference it directly
try:
    import builtins as _builtins

    from integrations.tool_catalog import catalog as _catalog

    if not hasattr(_builtins, "catalog"):
        _builtins.catalog = _catalog  # type: ignore[attr-defined]
    print("DEBUG: injected builtins.catalog for tests")
except Exception as _e:
    print("DEBUG: failed to inject builtins.catalog:", _e)
# Top-level pytest configuration
# Existing plugin registration
from pathlib import Path

# Only enable the Playwright plugin when explicitly requested to avoid
# importing heavy browser deps (and transitive packages like pyee.asyncio)
# in environments where they are not installed.
if os.getenv("RUN_PLAYWRIGHT"):
    pytest_plugins = ["playwright.sync_api"]
else:
    pytest_plugins = []


def pytest_ignore_collect(collection_path: Path, config):
    """Conditionally ignore Playwright tests unless explicitly requested.

    The function returns ``True`` (skip) for files inside the ``playwright``
    directory when the ``RUN_PLAYWRIGHT`` environment variable is not set.
    All other test files are collected normally.
    """
    import os

    path_str = str(collection_path)
    if "playwright" in path_str and not os.getenv("RUN_PLAYWRIGHT"):
        return True
    # Skip heavy/live and integration-style suites unless explicitly enabled
    run_integration = os.getenv("RUN_INTEGRATION") in {"1", "true", "yes"}
    if ("tests/integration" in path_str or "tests/context" in path_str) and not run_integration:
        return True
    if path_str.endswith("tests/test_outbox_repository.py") and not run_integration:
        return True
    # When running full integration, avoid collecting duplicate unit test module names
    # that clash with their integration counterparts (e.g., test_session_repository).
    if run_integration and path_str.endswith("tests/test_session_repository.py"):
        return True
    # Skip the async FastA2A CLI client test in unit-only runs
    if (
        path_str.endswith("tests/test_fasta2a_client.py")
        or path_str.endswith("test_fasta2a_client.py")
        or "tests/test_fasta2a_client.py" in path_str
    ) and not run_integration:
        return True
    # Skip capsule registry tests until the service exists in this repo
    if path_str.endswith("tests/unit/test_capsule_registry_install_endpoint.py"):
        return True
    return False


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless RUN_INTEGRATION=1 is set.

    This keeps the default test run fast and green without requiring external
    services. To run integration tests against real services, set the
    environment variable and bring up Kafka/Postgres as needed.
    """
    import os

    import pytest

    run_integration = os.getenv("RUN_INTEGRATION") in {"1", "true", "yes"}
    if run_integration:
        return
    skip_integration = pytest.mark.skip(reason="RUN_INTEGRATION not set")
    for item in items:
        if any(mark.name == "integration" for mark in item.iter_markers()):
            item.add_marker(skip_integration)
