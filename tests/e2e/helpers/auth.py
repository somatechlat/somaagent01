"""Authentication Helper for E2E Tests.

VIBE COMPLIANT - Rule 47 (Zero-Backdoor).
Performs REAL OIDC handshake with Keycloak to obtain a valid JWT.
Usage:
    token = get_auth_token()
    page.context.add_cookies([...])
"""

import os
from typing import Any

import httpx

# Keycloak Configuration (Local Dev)
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:49010")
REALM = os.getenv("KEYCLOAK_REALM", "master")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
USERNAME = os.getenv("KEYCLOAK_ADMIN", "admin")
PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")


def get_auth_token() -> str:
    """Get a valid access token from Keycloak.

    Performs a direct Resource Owner Password Credentials grant.
    This simulates a "Real" login without interacting with the UI,
    which is standard practice for speeding up E2E tests while maintaining
    cryptographic validity.
    """
    token_endpoint = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"

    payload = {
        "client_id": CLIENT_ID,
        "username": USERNAME,
        "password": PASSWORD,
        "grant_type": "password",
    }

    try:
        # 1. Attempt Login
        response = httpx.post(token_endpoint, data=payload, timeout=10.0)
        response.raise_for_status()

        data = response.json()
        access_token = data.get("access_token")

        if not access_token:
            raise ValueError("No access_token in Keycloak response")

        print(f"✅ [AuthHelper] Authenticated as {USERNAME} against {REALM}")
        return access_token

    except httpx.RequestError as exc:
        print(f"❌ [AuthHelper] Connection error to Keycloak: {exc}")
        raise
    except httpx.HTTPStatusError as exc:
        print(
            f"❌ [AuthHelper] keycloak returned error {exc.response.status_code}: {exc.response.text}"
        )
        raise
    except Exception as exc:
        print(f"❌ [AuthHelper] Unexpected auth failure: {exc}")
        raise


def inject_auth_cookies(context: Any, token: str, domain: str = "localhost"):
    """Inject the auth token as a cookie into the Playwright context."""
    context.add_cookies(
        [
            {
                "name": "access_token",
                "value": token,
                "domain": domain,
                "path": "/",
                "httpOnly": False,
                "secure": False,
                "sameSite": "Lax",
            }
        ]
    )
    print(f"✅ [AuthHelper] Injected access_token cookie for {domain}")