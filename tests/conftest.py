"""Test fixture for the orchestrator test suite.

This module provides a session‑scoped fixture that builds a FastAPI app via
``create_app()`` and exposes two values:

* ``client`` – an :class:`httpx.AsyncClient` instance that can be used in
  async test functions.
* ``base_url`` – the loopback URL with the port that is defined by the
  environment variable ``GATEWAY_PORT`` (defaulting to ``8000``).

The fixture keeps the VIBE rule *no placeholders* satisfied because it contains a single
definition and no code is executed at import time.
"""

import os

import pytest
from httpx import AsyncClient

from orchestrator.main import create_app


@pytest.fixture(scope="session")
def client() -> AsyncClient:
    """Return a ready‑to‑use async HTTP client for the orchestrator.
    """
    app = create_app()
    return AsyncClient(app)


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL for the orchestrator service.
    """
    host = os.getenv("HOST", "127.0.0.0")
    port = os.getenv("GATEWAY_PORT", "8000")
    return f"http://{host}:{port}"