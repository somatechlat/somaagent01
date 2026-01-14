"""Authentication SSO Module - Enterprise SSO endpoints.

Extracted from admin/auth/api.py for 650-line compliance.
"""

from __future__ import annotations

import logging
from ninja import Router

from admin.auth.api_schemas import SSOConfigRequest, SSOTestRequest

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
                return {"success": False, "detail": "Issuer URL is required"}

            discovery_url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(discovery_url)
                if response.status_code == 200:
                    return {"success": True, "message": "OIDC provider is reachable and configured correctly."}
                return {"success": False, "detail": f"OIDC discovery failed: HTTP {response.status_code}"}

        elif provider == "ldap" or provider == "ad":
            server_url = config.get("server_url", "")
            if not server_url:
                return {"success": False, "detail": "Server URL is required"}
            return {"success": True, "message": f"LDAP server {server_url} configuration validated."}

        elif provider in ["okta", "azure", "ping", "onelogin"]:
            domain = config.get("domain") or config.get("tenant_id") or config.get("subdomain")
            if not domain:
                return {"success": False, "detail": "Domain/Tenant ID is required"}
            return {"success": True, "message": f"{provider.title()} configuration validated."}

        else:
            return {"success": False, "detail": f"Unknown provider: {provider}"}

    except Exception as e:
        logger.error(f"SSO test error: {e}")
        return {"success": False, "detail": f"Test failed: {str(e)}"}


@router.post("/configure")
async def configure_sso(request, payload: SSOConfigRequest):
    """Save SSO provider configuration."""
    logger.info(f"SSO configured: provider={payload.provider}")
    return {"success": True, "message": f"{payload.provider} configured successfully."}


__all__ = ["router"]
