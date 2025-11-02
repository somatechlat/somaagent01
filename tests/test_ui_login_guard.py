import os
import time

import jwt
from fastapi.testclient import TestClient

from services.gateway.main import app, JWT_SECRET


def test_root_redirects_to_login_when_oidc_enabled(monkeypatch):
    monkeypatch.setenv("OIDC_ENABLED", "true")
    client = TestClient(app)
    resp = client.get("/", allow_redirects=False)
    assert resp.status_code in (302, 307, 303)
    assert resp.headers.get("location", "").endswith("/login")


def test_root_allows_when_session_cookie_present(monkeypatch):
    monkeypatch.setenv("OIDC_ENABLED", "true")
    # Ensure a secret
    secret = os.getenv("GATEWAY_JWT_SECRET") or "test-secret"
    monkeypatch.setenv("GATEWAY_JWT_SECRET", secret)
    # Minimal session token
    now = int(time.time())
    token = jwt.encode({"sub": "u1", "iat": now, "exp": now + 600}, secret, algorithm="HS256")

    client = TestClient(app)
    client.cookies.set("jwt", token)
    resp = client.get("/", allow_redirects=False)
    assert resp.status_code in (302, 307, 303)
    assert resp.headers.get("location", "").endswith("/ui/index.html")
