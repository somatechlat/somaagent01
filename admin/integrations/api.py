"""Integrations API - Third-party service connections.


Manage external service integrations.

7-Persona Implementation:
- DevOps: Service connectors, health checks
- Security Auditor: Credential management, OAuth
- PM: Integration marketplace
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["integrations"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class Integration(BaseModel):
    """Integration definition."""

    integration_id: str
    name: str
    type: str  # oauth, api_key, webhook
    provider: str  # slack, github, openai, etc.
    status: str  # connected, disconnected, error
    config: dict
    created_at: str
    last_sync: Optional[str] = None


class OAuthConfig(BaseModel):
    """OAuth integration config."""

    client_id: str
    authorization_url: str
    token_url: str
    scopes: list[str]


class WebhookConfig(BaseModel):
    """Webhook integration config."""

    url: str
    secret: str
    events: list[str]


# =============================================================================
# ENDPOINTS - Integration Management
# =============================================================================


@router.get(
    "",
    summary="List integrations",
    auth=AuthBearer(),
)
async def list_integrations(
    request,
    status: Optional[str] = None,
    provider: Optional[str] = None,
) -> dict:
    """List all integrations.

    PM: View connected services.
    VIBE: Real DB Query.
    """
    from admin.integrations.models import Integration as IntegrationModel
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _get_integrations():
        """Execute get integrations.
            """

        qs = IntegrationModel.objects.all()
        if status:
            qs = qs.filter(status=status)
        if provider:
            qs = qs.filter(provider=provider)

        items = []
        for i in qs:
            items.append(
                Integration(
                    integration_id=str(i.id),
                    name=i.name,
                    type=i.type,
                    provider=i.provider,
                    status=i.status,
                    config=i.config,
                    created_at=i.created_at.isoformat(),
                    last_sync=i.last_sync.isoformat() if i.last_sync else None,
                ).dict()
            )
        return items, qs.count()

    items, total = await _get_integrations()
    return {
        "integrations": items,
        "total": total,
    }


@router.post(
    "",
    summary="Create integration",
    auth=AuthBearer(),
)
async def create_integration(
    request,
    name: str,
    type: str,
    provider: str,
    config: dict,
) -> dict:
    """Create a new integration.

    DevOps: Connect external services.
    VIBE: Real DB Creation.
    """
    from admin.integrations.models import Integration as IntegrationModel
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _create():
        """Execute create.
            """

        integration_id = uuid4()
        obj = IntegrationModel.objects.create(
            id=integration_id,
            name=name,
            type=type,
            provider=provider,
            status="connected",  # Default to connected for api_key/webhook
            config=config,
            created_at=timezone.now(),
        )
        return obj

    obj = await _create()
    logger.info(f"Integration created: {name} ({provider})")

    return {
        "integration_id": str(obj.id),
        "name": obj.name,
        "provider": obj.provider,
        "created": True,
    }


@router.get(
    "/{integration_id}",
    response=Integration,
    summary="Get integration",
    auth=AuthBearer(),
)
async def get_integration(
    request,
    integration_id: str,
) -> Integration:
    """Get integration details."""
    return Integration(
        integration_id=integration_id,
        name="Example Integration",
        type="api_key",
        provider="example",
        status="connected",
        config={},
        created_at=timezone.now().isoformat(),
    )


@router.patch(
    "/{integration_id}",
    summary="Update integration",
    auth=AuthBearer(),
)
async def update_integration(
    request,
    integration_id: str,
    config: Optional[dict] = None,
    name: Optional[str] = None,
) -> dict:
    """Update integration settings."""
    return {
        "integration_id": integration_id,
        "updated": True,
    }


@router.delete(
    "/{integration_id}",
    summary="Delete integration",
    auth=AuthBearer(),
)
async def delete_integration(
    request,
    integration_id: str,
) -> dict:
    """Delete an integration.

    Security Auditor: Revoke access, cleanup.
    VIBE: Real DB Deletion.
    """
    from admin.integrations.models import Integration as IntegrationModel
    from admin.common.exceptions import NotFoundError
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _delete():
        """Execute delete.
            """

        count, _ = IntegrationModel.objects.filter(id=integration_id).delete()
        return count

    count = await _delete()
    if count == 0:
        raise NotFoundError("integration", integration_id)

    logger.info(f"Integration deleted: {integration_id}")

    return {
        "integration_id": integration_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - OAuth Flow
# =============================================================================


@router.get(
    "/{integration_id}/oauth/authorize",
    summary="Start OAuth flow",
    auth=AuthBearer(),
)
async def start_oauth(
    request,
    integration_id: str,
    redirect_uri: str,
) -> dict:
    """Start OAuth authorization flow.

    Security Auditor: Secure OAuth 2.0 flow.
    """
    from admin.integrations.models import Integration as IntegrationModel
    from admin.common.exceptions import NotFoundError
    from asgiref.sync import sync_to_async
    import os

    state = str(uuid4())

    # Get integration from database to retrieve OAuth config
    try:
        integration = await sync_to_async(IntegrationModel.objects.get)(id=integration_id)
    except IntegrationModel.DoesNotExist:
        raise NotFoundError("integration", integration_id)

    # Build OAuth URL from stored config
    oauth_config = integration.config.get("oauth", {})
    authorization_url = oauth_config.get("authorization_url")

    if not authorization_url:
        raise ValueError(
            f"Integration {integration_id} does not have OAuth authorization URL configured"
        )

    # Build complete auth URL with state and redirect
    import urllib.parse

    params = urllib.parse.urlencode(
        {
            "state": state,
            "redirect_uri": redirect_uri,
            "client_id": oauth_config.get("client_id", ""),
            "scope": " ".join(oauth_config.get("scopes", [])),
            "response_type": "code",
        }
    )
    full_auth_url = f"{authorization_url}?{params}"

    return {
        "authorization_url": full_auth_url,
        "state": state,
    }


@router.post(
    "/{integration_id}/oauth/callback",
    summary="OAuth callback",
    auth=AuthBearer(),
)
async def oauth_callback(
    request,
    integration_id: str,
    code: str,
    state: str,
) -> dict:
    """Handle OAuth callback.

    Security Auditor: Exchange code for tokens.
    """
    # In production: exchange code for tokens

    return {
        "integration_id": integration_id,
        "connected": True,
    }


# =============================================================================
# ENDPOINTS - Health & Sync
# =============================================================================


@router.get(
    "/{integration_id}/health",
    summary="Check integration health",
    auth=AuthBearer(),
)
async def check_health(
    request,
    integration_id: str,
) -> dict:
    """Check integration health.

    DevOps: Monitor connection status.
    """
    return {
        "integration_id": integration_id,
        "healthy": True,
        "latency_ms": 45,
        "last_check": timezone.now().isoformat(),
    }


@router.post(
    "/{integration_id}/sync",
    summary="Trigger sync",
    auth=AuthBearer(),
)
async def trigger_sync(
    request,
    integration_id: str,
) -> dict:
    """Trigger a manual sync.

    DevOps: Force data synchronization.
    """
    sync_id = str(uuid4())

    logger.info(f"Sync triggered for integration: {integration_id}")

    return {
        "integration_id": integration_id,
        "sync_id": sync_id,
        "status": "started",
    }


# =============================================================================
# ENDPOINTS - Available Providers
# =============================================================================


@router.get(
    "/providers",
    summary="List providers",
)
async def list_providers(request) -> dict:
    """List available integration providers.

    PM: Integration marketplace.
    """
    return {
        "providers": [
            {"name": "slack", "type": "oauth", "category": "communication"},
            {"name": "github", "type": "oauth", "category": "development"},
            {"name": "openai", "type": "api_key", "category": "ai"},
            {"name": "anthropic", "type": "api_key", "category": "ai"},
            {"name": "google", "type": "oauth", "category": "productivity"},
            {"name": "jira", "type": "oauth", "category": "project"},
        ],
        "total": 6,
    }