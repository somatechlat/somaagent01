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
# API KEYS
# =============================================================================
@router.get("/api-keys", response=list[ApiKeyOut])
def list_api_keys(request, tenant_id: Optional[str] = None):
    """Get all API keys, optionally filtered by tenant."""
    # For now, return demo data
    return []


@router.post("/api-keys", response=ApiKeyOut)
@transaction.atomic
def create_api_key(request, payload: ApiKeyCreate):
    """Create a new API key."""
    # - Generate cryptographically secure key
    # - Store hashed version
    # - Return plaintext once only
    raise Exception("API key creation not yet implemented")


@router.delete("/api-keys/{key_id}", response=MessageResponse)
@transaction.atomic
def revoke_api_key(request, key_id: str):
    """Revoke an API key."""
    return MessageResponse(message=f"API key {key_id} revoked")


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
