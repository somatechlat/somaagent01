"""Authentication OAuth Module - OAuth/PKCE endpoints.

Extracted from admin/auth/api.py for 650-line compliance.
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx
from ninja import Router, Schema

from admin.auth.api_helpers import determine_redirect_path, update_last_login
from admin.common.auth import decode_token, get_keycloak_config
from admin.common.exceptions import BadRequestError

logger = logging.getLogger(__name__)
router = Router(tags=["OAuth"])


class OAuthInitiateResponse(Schema):
    """OAuth initiation response with redirect URL."""

    redirect_url: str
    state: str


class OAuthCallbackRequest(Schema):
    """OAuth callback query parameters."""

    code: str
    state: str


@router.get("/{provider}", response=OAuthInitiateResponse)
async def oauth_initiate(request, provider: str):
    """Initiate OAuth flow with PKCE."""
    from admin.common.pkce import generate_code_challenge, get_oauth_state_store

    supported_providers = {"google", "github"}
    if provider not in supported_providers:
        raise BadRequestError(
            message=f"Unsupported OAuth provider: {provider}",
            details={"supported": list(supported_providers)},
        )

    base_url = request.build_absolute_uri("/").rstrip("/")
    redirect_uri = f"{base_url}/api/v2/auth/oauth/callback"

    state_store = await get_oauth_state_store()
    oauth_state = await state_store.store_state(provider=provider, redirect_uri=redirect_uri)
    code_challenge = generate_code_challenge(oauth_state.code_verifier)

    config = get_keycloak_config()
    auth_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/auth"
    params = {
        "client_id": config.client_id,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": redirect_uri,
        "state": oauth_state.state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "kc_idp_hint": provider,
    }

    redirect_url = f"{auth_url}?{urlencode(params)}"
    logger.info(f"OAuth initiated: provider={provider}, state={oauth_state.state[:8]}...")
    return OAuthInitiateResponse(redirect_url=redirect_url, state=oauth_state.state)


@router.get("/callback")
async def oauth_callback(request, code: str, state: str):
    """Handle OAuth callback from Keycloak."""
    from django.http import HttpResponseRedirect

    from admin.common.pkce import get_oauth_state_store
    from admin.common.session_manager import get_session_manager

    state_store = await get_oauth_state_store()
    oauth_state = await state_store.consume_state(state)

    if oauth_state is None:
        logger.warning(f"OAuth callback with invalid/expired state: state={state[:8]}...")
        return HttpResponseRedirect("/login?error=oauth_state_invalid")

    config = get_keycloak_config()
    token_url = f"{config.server_url}/realms/{config.realm}/protocol/openid-connect/token"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": config.client_id,
                    "code": code,
                    "redirect_uri": oauth_state.redirect_uri,
                    "code_verifier": oauth_state.code_verifier,
                },
            )
            if response.status_code != 200:
                logger.warning(f"OAuth token exchange failed: status={response.status_code}")
                return HttpResponseRedirect("/login?error=oauth_token_exchange_failed")
            token_data = response.json()
    except httpx.HTTPError as e:
        logger.error(f"OAuth token exchange error: {e}")
        return HttpResponseRedirect("/login?error=oauth_service_unavailable")

    try:
        token_payload = await decode_token(token_data["access_token"])
    except Exception as e:
        logger.error(f"OAuth token decode error: {e}")
        return HttpResponseRedirect("/login?error=oauth_token_invalid")

    session_manager = await get_session_manager()
    permissions = await session_manager.resolve_permissions(
        user_id=token_payload.sub,
        tenant_id=token_payload.tenant_id or "",
        roles=token_payload.roles,
    )
    session = await session_manager.create_session(
        user_id=token_payload.sub,
        tenant_id=token_payload.tenant_id or "",
        email=token_payload.email or "",
        roles=token_payload.roles,
        permissions=permissions,
        ip_address=request.META.get("REMOTE_ADDR", ""),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )

    await update_last_login(token_payload)
    redirect_path = determine_redirect_path(token_payload)
    logger.info(
        f"OAuth login successful: provider={oauth_state.provider}, user_id={token_payload.sub}"
    )

    response = HttpResponseRedirect(redirect_path)
    max_age = token_data.get("expires_in", 900)
    response.set_cookie(
        "access_token",
        token_data["access_token"],
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    if token_data.get("refresh_token"):
        response.set_cookie(
            "refresh_token",
            token_data["refresh_token"],
            max_age=86400,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
    response.set_cookie(
        "session_id",
        session.session_id,
        max_age=max_age,
        httponly=True,
        secure=True,
        samesite="Lax",
    )
    return response


__all__ = ["router"]
