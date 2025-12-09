"""Unit test configuration - isolated from real infrastructure.

Unit tests MUST NOT require real infrastructure (PostgreSQL, Redis, Kafka, SomaBrain).
This conftest sets up environment variables to allow unit tests to run in isolation.

For tests that require real infrastructure, use:
- tests/integration/ - Integration tests against real services
- tests/functional/ - Full functional tests against real infrastructure
- tests/e2e/ - End-to-end tests
"""

import os
import pytest

# Set minimal environment variables BEFORE any imports that might trigger config loading
# These are ONLY for unit tests - they allow the config system to initialize without
# requiring real infrastructure connections.


def pytest_configure(config):
    """Set up environment for isolated unit tests.
    
    This runs before any test collection, ensuring the config system
    can initialize without requiring real infrastructure.
    """
    # Only set if not already set - allows CI to override
    env_defaults = {
        # SomaBrain URL - required by config system but not actually used in unit tests
        "SA01_SOMA_BASE_URL": os.environ.get("SA01_SOMA_BASE_URL", "http://localhost:9696"),
        # Database - not actually connected in unit tests
        "SA01_DB_DSN": os.environ.get("SA01_DB_DSN", "postgresql://test:test@localhost:5432/test"),
        # Redis - not actually connected in unit tests
        "SA01_REDIS_URL": os.environ.get("SA01_REDIS_URL", "redis://localhost:6379/0"),
        # Kafka - not actually connected in unit tests
        "SA01_KAFKA_BOOTSTRAP_SERVERS": os.environ.get("SA01_KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        # OPA - not actually connected in unit tests
        "SA01_POLICY_URL": os.environ.get("SA01_POLICY_URL", "http://localhost:8181"),
        # Disable auth for unit tests
        "SA01_AUTH_REQUIRED": os.environ.get("SA01_AUTH_REQUIRED", "false"),
        # Disable SomaBrain for memory tests
        "SA01_SOMABRAIN_ENABLED": os.environ.get("SA01_SOMABRAIN_ENABLED", "false"),
    }
    
    for key, value in env_defaults.items():
        if key not in os.environ:
            os.environ[key] = value


@pytest.fixture(autouse=True)
def reset_config_cache():
    """Reset config cache between tests to ensure isolation."""
    yield
    # Reset the config cache after each test
    try:
        from src.core.config.loader import reload_config
        reload_config()
    except ImportError:
        pass


@pytest.fixture
def mock_env(monkeypatch):
    """Fixture to temporarily set environment variables for a test.
    
    Usage:
        def test_something(mock_env):
            mock_env("SA01_SOME_VAR", "value")
            # test code
    """
    def _set_env(key: str, value: str):
        monkeypatch.setenv(key, value)
    return _set_env


@pytest.fixture
def isolated_config(monkeypatch):
    """Fixture providing a completely isolated config environment.
    
    Clears all SA01_ environment variables and sets only the minimum required.
    """
    # Clear all SA01_ vars
    for key in list(os.environ.keys()):
        if key.startswith("SA01_"):
            monkeypatch.delenv(key, raising=False)
    
    # Set minimum required
    monkeypatch.setenv("SA01_SOMA_BASE_URL", "http://test:9696")
    monkeypatch.setenv("SA01_DB_DSN", "postgresql://test:test@localhost:5432/test")
    
    # Reset config cache
    try:
        from src.core.config.loader import reload_config
        reload_config()
    except ImportError:
        pass
    
    yield
    
    # Cleanup
    try:
        from src.core.config.loader import reload_config
        reload_config()
    except ImportError:
        pass
