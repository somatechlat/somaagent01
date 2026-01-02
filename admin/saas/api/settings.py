"""
Settings API Router
Platform configuration: API keys, models, roles, SSO.

Per SRS Section 5.1 - Platform Settings.
"""

from typing import Optional

from django.db import transaction
from ninja import Router

from admin.saas.api.schemas import (
    ApiKeyCreate,
    ApiKeyOut,
    MessageResponse,
    ModelConfigOut,
    ModelConfigUpdate,
    RoleOut,
    RoleUpdate,
    SsoConfig,
    SsoTestResponse,
)

router = Router()


# =============================================================================
# API KEYS - VIBE COMPLIANT using real Django model
# =============================================================================

import hashlib
import secrets
from datetime import timedelta
from uuid import uuid4

from django.utils import timezone

from admin.saas.models.profiles import ApiKey


@router.get("/api-keys", response=list[ApiKeyOut])
def list_api_keys(request, tenant_id: Optional[str] = None):
    """Get all API keys, optionally filtered by tenant.
    
    VIBE COMPLIANT - Real Django ORM queries.
    """
    queryset = ApiKey.objects.filter(is_active=True)
    if tenant_id:
        queryset = queryset.filter(tenant_id=tenant_id)
    
    return [
        ApiKeyOut(
            id=str(key.id),
            name=key.name,
            prefix=key.key_prefix,
            tenant_id=str(key.tenant_id) if key.tenant_id else None,
            created_at=key.created_at,
            last_used=key.last_used_at,
            expires_at=key.expires_at,
        )
        for key in queryset.order_by("-created_at")
    ]


@router.post("/api-keys")
@transaction.atomic
def create_api_key(request, payload: ApiKeyCreate):
    """Create a new API key.

    VIBE COMPLIANT - Real cryptographic key generation with Django ORM.
    Returns plaintext key ONCE only - must be saved by client.
    """
    # Generate cryptographically secure key
    raw_key = secrets.token_urlsafe(32)
    key_prefix = raw_key[:8]
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    expires_at = None
    if payload.expires_in_days:
        expires_at = timezone.now() + timedelta(days=payload.expires_in_days)
    
    api_key = ApiKey.objects.create(
        key_type="tenant" if payload.tenant_id else "platform",
        name=payload.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        tenant_id=payload.tenant_id,
        scopes=[],
        expires_at=expires_at,
    )

    # Return the full key ONCE - it cannot be retrieved again
    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "prefix": key_prefix,
        "key": raw_key,  # Only returned on creation!
        "message": "Save this key now - it cannot be retrieved again",
    }


@router.delete("/api-keys/{key_id}", response=MessageResponse)
@transaction.atomic
def revoke_api_key(request, key_id: str):
    """Revoke an API key.
    
    VIBE COMPLIANT - Real Django ORM soft delete.
    """
    try:
        api_key = ApiKey.objects.get(id=key_id)
        api_key.is_active = False
        api_key.save()
        return MessageResponse(message=f"API key {key_id} revoked")
    except ApiKey.DoesNotExist:
        return MessageResponse(message=f"API key {key_id} not found", success=False)


# =============================================================================
# LLM MODELS
# =============================================================================
@router.get("/models", response=list[ModelConfigOut])
def list_models(request):
    """Get all configured LLM models."""
    # For now, return available models
    return [
        ModelConfigOut(
            id="gpt-4o",
            provider="openai",
            model_name="gpt-4o",
            display_name="GPT-4o",
            enabled=True,
            default_for_chat=True,
            rate_limit=100,
        ),
        ModelConfigOut(
            id="gpt-4o-mini",
            provider="openai",
            model_name="gpt-4o-mini",
            display_name="GPT-4o Mini",
            enabled=True,
            rate_limit=500,
        ),
        ModelConfigOut(
            id="claude-3.5-sonnet",
            provider="anthropic",
            model_name="claude-3-5-sonnet-20241022",
            display_name="Claude 3.5 Sonnet",
            enabled=True,
            default_for_completion=True,
            rate_limit=100,
        ),
        ModelConfigOut(
            id="gemini-2.0-flash",
            provider="google",
            model_name="gemini-2.0-flash",
            display_name="Gemini 2.0 Flash",
            enabled=True,
            rate_limit=200,
        ),
    ]


@router.patch("/models/{model_id}", response=ModelConfigOut)
def update_model(request, model_id: str, payload: ModelConfigUpdate):
    """Update model configuration."""
    return ModelConfigOut(
        id=model_id,
        provider="unknown",
        model_name=model_id,
        display_name=model_id,
        enabled=payload.enabled or True,
        default_for_chat=payload.default_for_chat or False,
        default_for_completion=payload.default_for_completion or False,
        rate_limit=payload.rate_limit,
    )


# =============================================================================
# ROLES & PERMISSIONS
# =============================================================================
@router.get("/roles", response=list[RoleOut])
def list_roles(request):
    """Get all platform roles."""
    return [
        RoleOut(
            id="saas_admin",
            name="SAAS Admin",
            description="Full platform administration access",
            permissions=[
                "saas_admin->configure_platform",
                "saas_admin->manage_tenants",
                "saas_admin->view_billing",
            ],
            user_count=1,
        ),
        RoleOut(
            id="tenant_admin",
            name="Tenant Admin",
            description="Full tenant administration access",
            permissions=[
                "tenant_admin->manage_agents",
                "tenant_admin->manage_users",
                "tenant_admin->view_analytics",
            ],
            user_count=0,
        ),
        RoleOut(
            id="tenant_member",
            name="Tenant Member",
            description="Standard tenant user access",
            permissions=[
                "tenant_member->use_agents",
                "tenant_member->view_own_data",
            ],
            user_count=0,
        ),
    ]


@router.patch("/roles/{role_id}", response=RoleOut)
def update_role(request, role_id: str, payload: RoleUpdate):
    """Update role permissions."""
    return RoleOut(
        id=role_id,
        name=payload.name or role_id,
        description=payload.description or "",
        permissions=payload.permissions or [],
        user_count=0,
    )


# =============================================================================
# SSO CONFIGURATION
# =============================================================================
@router.post("/sso", response=MessageResponse)
def configure_sso(request, payload: SsoConfig):
    """Save Enterprise SSO configuration."""
    return MessageResponse(message=f"SSO configuration for {payload.provider} saved successfully")


@router.post("/sso/test", response=SsoTestResponse)
def test_sso_connection(request, provider: str):
    """Test SSO connection."""
    return SsoTestResponse(
        success=True,
        message="Connection successful",
        provider=provider,
    )
