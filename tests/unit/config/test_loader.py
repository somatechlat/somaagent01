"""Tests for the central configuration loader.

These tests verify that the VIBE‑compliant loader (``src.core.config.loader``)
correctly reads ``SA01_``‑prefixed environment variables and that the public
``get_config`` façade returns a fully validated ``Config`` instance.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch):
    """Ensure a clean environment for each test.

    The loader caches the configuration on first call, so we need to clear the
    cache between tests.  ``src.core.config`` stores the cached object in the
    private ``_cached_config`` variable – we reset it via the public ``reload``
    helper.
    """
    # Remove any SA01_* variables that may be present on the host CI runner.
    for key in list(os.environ):
        if key.startswith("SA01_"):
            monkeypatch.delenv(key, raising=False)
    # Force a reload after the test finishes.
    yield
    from src.core.config import reload_config

    reload_config()


def test_loader_reads_sa01_env(monkeypatch: pytest.MonkeyPatch):
    """A ``SA01_`` environment variable should be visible via ``get_config``.

    The ``Config`` model contains a ``service.deployment_mode`` field that maps
    to the ``SA01_DEPLOYMENT_MODE`` variable (via the ``env_prefix`` in the
    ``Settings`` model).  We set the variable, reload the config and assert the
    value is present.
    """
    monkeypatch.setenv("SA01_DEPLOYMENT_MODE", "TEST")
    # Reload the cached configuration so the new env var is taken into account.
    from src.core.config import reload_config

    cfg = reload_config()

    assert cfg.service.deployment_mode == "TEST"
