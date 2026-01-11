"""Gateway authentication and authorization module.

This module provides JWT-based authentication and OPA policy-based authorization
for the gateway service. All authentication is handled via Django patterns with
custom exceptions from admin.common.exceptions.

Functions:
    authorize_request: Main entry point for request authentication/authorization.
    _resolve_signing_key: Resolves JWT signing key from JWKS or environment.
    _evaluate_opa: Evaluates Open Policy Agent authorization policies.
    _get_policy_client: Returns cached PolicyClient instance.
    _get_openfga_client: Returns OpenFGA client if available.

Example:
    >>> payload = await authorize_request(request, {"action": "read"})
    >>> user_id = payload["user_id"]
"""

import httpx
import jwt
from django.conf import settings

from admin.common.exceptions import ForbiddenError, UnauthorizedError
from services.common.policy_client import PolicyClient, PolicyRequest

jwt_module = jwt

_policy_client: PolicyClient | None = None


async def _resolve_signing_key(header: dict) -> str:
    """Resolve signing key from JWKS or settings."""
    # 1. Try JWKS if configured
    jwks_url = getattr(settings, "JWT_JWKS_URL", None)
    if jwks_url:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(jwks_url)
                resp.raise_for_status()
                jwks = resp.json()

                kid = header.get("kid")
                for key in jwks.get("keys", []):
                    if key.get("kid") == kid:
                        return jwt.algorithms.RSAAlgorithm.from_jwk(key)
        except Exception:
            pass

    # 2. Fallback to static public key/secret
    return getattr(settings, "KEYCLOAK_PUBLIC_KEY", None) or settings.SECRET_KEY


def _get_policy_client() -> PolicyClient | None:
    """Return (and cache) the PolicyClient if OPA is configured."""
    global _policy_client
    if _policy_client is not None:
        return _policy_client

    opa_url = getattr(settings, "OPA_URL", None)
    if not opa_url:
        return None

    _policy_client = PolicyClient(base_url=opa_url)
    return _policy_client


async def _evaluate_opa(payload: dict, policy_context: dict | None) -> None:
    """Evaluate OPA policy for authorization."""
    if not policy_context:
        return
    client = _get_policy_client()
    if client is None:
        return
    request = PolicyRequest(
        tenant=policy_context.get("tenant")
        or payload.get("tenant")
        or payload.get("sub")
        or "default",
        persona_id=policy_context.get("persona_id") or payload.get("persona_id"),
        action=policy_context.get("action") or "gateway.request",
        resource=str(policy_context.get("resource") or "gateway"),
        context={"jwt": payload, **policy_context},
    )
    allowed = await client.evaluate(request)
    if not allowed:
        raise ForbiddenError(action="policy", resource="gateway")


def _get_openfga_client():
    """Get OpenFGA client if available."""
    # Placeholder for future implementation
    return None


async def authorize_request(request, policy_context: dict = None):
    """Authorize request using JWT token from headers.

    🔒 Security: JWT validation + OPA policy check

    Raises:
        UnauthorizedError: If authentication fails
        ForbiddenError: If authorization denied
    """
    auth_required = getattr(settings, "AUTH_REQUIRED", True)

    # Dev/Test Bypass - ONLY if explicitly disabled
    if not auth_required:
        return {
            "user_id": "test_user",
            "tenant": "test_tenant",
            "scope": "read",
            "sub": "test-user-123",
        }

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise UnauthorizedError("Authorization header required")

    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Invalid authorization header format")

    token = auth_header.split(" ")[1]
    if not token:
        raise UnauthorizedError("Token not provided")

    try:
        header = jwt_module.get_unverified_header(token)
        key = await _resolve_signing_key(header)

        payload = jwt_module.decode(
            token,
            key=key,
            algorithms=getattr(settings, "JWT_ALGORITHMS", ["RS256"]),
            audience=getattr(settings, "JWT_AUDIENCE", None),
            issuer=getattr(settings, "JWT_ISSUER", None),
            leeway=getattr(settings, "JWT_LEEWAY", 10),
        )

        opa_context = dict(policy_context or {})
        opa_context.setdefault("action", getattr(request, "method", "request"))
        path = getattr(getattr(request, "url", None), "path", None)
        if path:
            opa_context.setdefault("resource", path)
        opa_context.setdefault("tenant", payload.get("tenant"))

        await _evaluate_opa(payload, opa_context)

        return {
            "user_id": payload.get("sub", "unknown_user"),
            "tenant": payload.get("tenant", payload.get("sub", "default_tenant")),
            "scope": payload.get("scope", "read"),
            "sub": payload.get("sub"),
            "subject": payload.get("sub"),
            **payload,
        }
    except jwt_module.PyJWTError as e:
        raise UnauthorizedError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise UnauthorizedError(f"Authentication failed: {str(e)}")
