"""Tests for selective authorization decorator & helper.

These tests monkeypatch PolicyClient.evaluate to simulate allow/deny/error
without performing real HTTP calls.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from services.common.authorization import authorize
from services.common.policy_client import PolicyClient


@pytest.fixture
def app(monkeypatch):
    app = FastAPI()

    # Provide a predictable PolicyClient instance
    client = PolicyClient()

    def _fake_get_client():
        return client

    monkeypatch.setattr("services.common.authorization.get_policy_client", _fake_get_client)

    @app.get("/allow")
    async def allow_endpoint(request: Request):  # type: ignore[override]
        await authorize(request=request, action="test.allow", resource="unit")
        return {"ok": True}

    @app.get("/deny")
    async def deny_endpoint(request: Request):  # type: ignore[override]
        await authorize(request=request, action="test.deny", resource="unit")
        return {"ok": True}

    return app, client


def test_allow(monkeypatch, app):
    app_obj, client = app

    async def _eval_allow(req):  # type: ignore[override]
        return True

    monkeypatch.setattr(client, "evaluate", _eval_allow)
    client_http = TestClient(app_obj)
    r = client_http.get("/allow")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_deny(monkeypatch, app):
    app_obj, client = app

    async def _eval_deny(req):  # type: ignore[override]
        return False

    monkeypatch.setattr(client, "evaluate", _eval_deny)
    
    # Enable auth to ensure policy is enforced.
    from services.common import runtime_config as cfg
    original_settings = cfg._STATE.settings if cfg._STATE else None
    try:
        import copy
        fake_settings = copy.deepcopy(cfg.settings())
        fake_settings.auth_required = True
        cfg._STATE.settings = fake_settings
        
        client_http = TestClient(app_obj)
        r = client_http.get("/deny")
        assert r.status_code == 403
        assert "policy_denied" in r.text
    finally:
        cfg._STATE.settings = original_settings


def test_error(monkeypatch, app):
    app_obj, client = app

    async def _eval_error(req):  # type: ignore[override]
        raise RuntimeError("boom")

    monkeypatch.setattr(client, "evaluate", _eval_error)
    
    # Enable auth to ensure policy is enforced.
    from services.common import runtime_config as cfg
    original_settings = cfg._STATE.settings if cfg._STATE else None
    try:
        import copy
        fake_settings = copy.deepcopy(cfg.settings())
        fake_settings.auth_required = True
        cfg._STATE.settings = fake_settings
        
        client_http = TestClient(app_obj)
        r = client_http.get("/deny")
        # Error path currently treated as deny (fail-closed)
        assert r.status_code == 403
    finally:
        cfg._STATE.settings = original_settings
