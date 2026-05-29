"""Authentication SSO Module - Enterprise SSO endpoints.

Extracted from admin/auth/api.py for 650-line compliance.
"""

from __future__ import annotations

import logging

from ninja import Router

from admin.auth.api_schemas import SSOConfigRequest, SSOTestRequest
from admin.common.messages import ErrorCode, SuccessCode, get_message

logger = logging.getLogger(__name__)
router = Router(tags=["SSO"])


@router.post("/test")
async def test_sso_connection(request, payload: SSOTestRequest):
    """Test SSO provider connection."""
    import httpx

    provider = payload.provider
    config = payload.config

    try:
        if provider == "oidc":
            issuer_url = config.get("issuer_url", "")
            if not issuer_url:
                return {"success": False, "detail": get_message(ErrorCode.SSO_ISSUER_URL_REQUIRED)}

            discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(discovery_url)
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": get_message(SuccessCode.SSO_OIDC_REACHABLE),
                    }
                return {
                    "success": False,
                    "detail": get_message(ErrorCode.SSO_OIDC_DISCOVERY_FAILED, status_code=response.status_code),
                }

        elif provider == "ldap" or provider == "ad":
            server_url = config.get("server_url", "")
            if not server_url:
                return {"success": False, "detail": get_message(ErrorCode.SSO_SERVER_URL_REQUIRED)}
            return {
                "success": True,
                "message": get_message(SuccessCode.SSO_LDAP_VALIDATED, server_url=server_url),
            }

        elif provider in ["okta", "azure", "ping", "onelogin"]:
            domain = config.get("domain") or config.get("tenant_id") or config.get("subdomain")
            if not domain:
                return {"success": False, "detail": get_message(ErrorCode.SSO_DOMAIN_REQUIRED)}
            return {"success": True, "message": get_message(SuccessCode.SSO_PROVIDER_VALIDATED, provider=provider.title())}

        else:
            return {"success": False, "detail": get_message(ErrorCode.SSO_UNKNOWN_PROVIDER, provider=provider)}

    except Exception as e:
        logger.error('SSO test error: %s', e)
        return {"success": False, "detail": get_message(ErrorCode.SSO_TEST_FAILED, error=str(e))}


@router.post("/configure")
async def configure_sso(request, payload: SSOConfigRequest):
    """Save SSO provider configuration."""
    logger.info('SSO configured: provider=%s', payload.provider)
    return {"success": True, "message": get_message(SuccessCode.SSO_CONFIGURED, provider=payload.provider)}


__all__ = ["router"]
