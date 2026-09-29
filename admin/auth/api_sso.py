"""Authentication SSO Module - Enterprise SSO endpoints.

Extracted from admin/auth/api.py for 650-line compliance.
"""

from __future__ import annotations

import logging

from ninja import Router

from admin.auth.api_schemas import SSOConfigRequest, SSOTestRequest
from admin.common.auth import AuthBearer
from admin.common.messages import ErrorCode, get_message, SuccessCode
from services.common.authorization import authorize
from services.common.http_timeouts import httpx_timeout  # noqa: E402

logger = logging.getLogger(__name__)
router = Router(tags=["SSO"])


@router.post("/test", auth=AuthBearer())
async def test_sso_connection(request, payload: SSOTestRequest):
    """Test SSO provider connection.

    Identity (``AuthBearer``) and authority (``authorize``) are both required.
    This route takes a caller-supplied issuer URL and makes an outbound request
    to it — it is an integration probe, not a read, and an unauthenticated
    caller holding it is an open relay.
    """
    # Gate before any URL is read out of the payload. Discovering which issuer
    # formats are accepted is itself information about the auth surface.
    await authorize(request, action="system:manage_integrations", resource="sso")
    import httpx

    provider = payload.provider
    config = payload.config

    try:
        if provider == "oidc":
            issuer_url = config.get("issuer_url", "")
            if not issuer_url:
                return {"success": False, "detail": get_message(ErrorCode.SSO_ISSUER_URL_REQUIRED)}

            discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
            async with httpx.AsyncClient(timeout=httpx_timeout()) as client:
                response = await client.get(discovery_url)
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": get_message(SuccessCode.SSO_OIDC_REACHABLE),
                    }
                return {
                    "success": False,
                    "detail": get_message(
                        ErrorCode.SSO_OIDC_DISCOVERY_FAILED, status_code=response.status_code
                    ),
                }

        elif provider == "ldap" or provider == "ad":
            server_url = config.get("server_url", "")
            if not server_url:
                return {"success": False, "detail": get_message(ErrorCode.SSO_SERVER_URL_REQUIRED)}
            # Fail closed: no LDAP bind is performed here. Never report a
            # validated directory without a real bind.
            return {
                "success": False,
                "detail": (
                    "LDAP/AD validation is not implemented: no directory bind "
                    "is performed by this endpoint."
                ),
            }

        elif provider in ["okta", "azure", "ping", "onelogin"]:
            domain = config.get("domain") or config.get("tenant_id") or config.get("subdomain")
            if not domain:
                return {"success": False, "detail": get_message(ErrorCode.SSO_DOMAIN_REQUIRED)}
            # Fail closed: no IdP round-trip is performed here.
            return {
                "success": False,
                "detail": (
                    f"{provider} validation is not implemented: "
                    "no IdP connection test is performed by this endpoint."
                ),
            }

        else:
            return {
                "success": False,
                "detail": get_message(ErrorCode.SSO_UNKNOWN_PROVIDER, provider=provider),
            }

    except Exception as e:
        logger.error("SSO test error: %s", e)
        return {"success": False, "detail": get_message(ErrorCode.SSO_TEST_FAILED, error=str(e))}


@router.post("/configure", auth=AuthBearer())
async def configure_sso(request, payload: SSOConfigRequest):
    """Save SSO provider configuration.

    ``system:security_policy``, not the integration permission: deciding which
    identity provider the platform trusts decides who can authenticate at all.
    That is security policy, and if the two ever split into separate roles the
    tighter one has to be the one that governs login.
    """
    await authorize(request, action="system:security_policy", resource="sso")
    # Fail closed: no config store is wired to this endpoint yet.
    return {
        "success": False,
        "detail": (
            "SSO configuration persistence is not implemented: "
            "no configuration store is wired to this endpoint."
        ),
    }


__all__ = ["router"]
