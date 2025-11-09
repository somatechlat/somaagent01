"""Integration tests for the ``EnforcePolicy`` OPA middleware.

The middleware respects the ``POLICY_FAIL_OPEN`` environment variable. When it
is ``true`` (the default) all requests are forwarded unchanged. When set to
``false`` the middleware will evaluate the policy. For unit‑test purposes we
simulate a denial via the ``X-OPA-DENY`` request header.
"""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from python.integrations.opa_middleware import EnforcePolicy


@pytest.fixture
def app_factory(monkeypatch):
    """Create a minimal FastAPI app with the OPA middleware attached."""
    def _make(fail_open: str):
        # Ensure the environment variable is set for each instance.
        monkeypatch.setenv("POLICY_FAIL_OPEN", fail_open)
        app = FastAPI()
        # ``EnforcePolicy`` is a middleware class; FastAPI expects the class itself.
        app.add_middleware(EnforcePolicy)

        @app.get("/test")
        def read_root():
            return {"ok": True}

        return app
    return _make


def test_middleware_passes_when_fail_open(monkeypatch, app_factory):
    """When ``POLICY_FAIL_OPEN`` is true the request should succeed."""
    app = app_factory("true")
    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_middleware_denies_when_not_fail_open_and_header(monkeypatch, app_factory):
    """When fail‑open is false and ``X-OPA-DENY`` header is true, a 403 is returned."""
    app = app_factory("false")
    client = TestClient(app)
    response = client.get("/test", headers={"X-OPA-DENY": "true"})
    assert response.status_code == 403
    # The response body should contain the detail we set in the middleware.
    assert "opa_policy_denied" in response.json().get("detail", "")
