"""
Settings API Router
Platform configuration: API keys, models, roles, SSO.

Per SRS Section 5.1 - Platform Settings.
"""

from typing import Optional

from django.db import transaction
from ninja import Router

from admin.aaas.api.schemas import (
    ApiKeyCreate,
    ApiKeyOut,
    MessageResponse,
    ModelConfigOut,
    ModelConfigUpdate,
    RoleOut,
    RoleUpdate,
)
from admin.common.auth import AuthBearer
from admin.common.exceptions import ValidationError
from admin.common.messages import ErrorCode, get_message, SuccessCode
from admin.core.authz import permissions_for_roles, validate_scopes
from services.common.authorization import authorize_sync

# Every handler below gates with ``authorize_sync()``, which reads roles from
# ``request.auth`` — and Django Ninja only sets ``request.auth`` when the route
# declares an auth callback. A gated route without ``auth=AuthBearer()`` reaches
# the gate as a principal with no roles and is denied 403 for everyone,
# sysadmin included. Both halves are required.
router = Router()


# =============================================================================
# API KEYS -
# =============================================================================

import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone

from admin.aaas.models.profiles import ApiKey


@router.get("/api-keys", response=list[ApiKeyOut], auth=AuthBearer())
def list_api_keys(request, tenant_id: Optional[str] = None):
    """Get all API keys, optionally filtered by tenant."""
    authorize_sync(request, action="org:apikey_read", resource="api_keys")
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


@router.post("/api-keys", auth=AuthBearer())
@transaction.atomic
def create_api_key(request, payload: ApiKeyCreate):
    """Create a new API key.

    The key is a delegation: it receives an explicit, non-empty subset of the
    issuing principal's authority and nothing more. Returns plaintext key ONCE
    only - must be saved by client.
    """
    # Gate before touching scopes: minting a delegation is itself a privilege,
    # and an unauthenticated caller must not learn which scopes exist.
    authorize_sync(request, action="org:apikey_create", resource="api_keys")
    auth = getattr(request, "auth", None)
    issuer_permissions = permissions_for_roles(list(getattr(auth, "roles", None) or []))

    try:
        scopes = sorted(validate_scopes(payload.scopes, issuer_permissions))
    except ValueError as exc:
        raise ValidationError(str(exc), field="scopes")

    # Generate cryptographically secure key. 256 bits of CSPRNG entropy,
    # presented once, stored only as a verifier.
    from admin.common.auth import API_KEY_PREFIX

    raw_key = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
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
        scopes=scopes,
        expires_at=expires_at,
    )

    # Return the full key ONCE - it cannot be retrieved again
    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "prefix": key_prefix,
        "key": raw_key,  # Only returned on creation!
        "message": get_message(SuccessCode.API_KEY_SAVE_WARNING),
    }


@router.delete("/api-keys/{key_id}", response=MessageResponse, auth=AuthBearer())
@transaction.atomic
def revoke_api_key(request, key_id: str):
    """Revoke an API key."""
    authorize_sync(request, action="org:apikey_revoke", resource="api_keys")
    try:
        api_key = ApiKey.objects.get(id=key_id)
        api_key.is_active = False
        api_key.save()
        return MessageResponse(message=get_message(SuccessCode.API_KEY_REVOKED, key_id=key_id))
    except ApiKey.DoesNotExist:
        return MessageResponse(
            message=get_message(ErrorCode.API_KEY_NOT_FOUND, key_id=key_id), success=False
        )


# =============================================================================
# LLM MODELS
# =============================================================================
@router.get("/models", response=list[ModelConfigOut], auth=AuthBearer())
def list_models(request):
    """Get all configured LLM models from Global Defaults."""
    authorize_sync(request, action="system:view", resource="settings")
    from admin.aaas.models.profiles import PlatformConfig

    defaults = PlatformConfig.get_instance().defaults
    models_data = defaults.get("models", [])

    # Transform dicts to Pydantic models
    return [
        ModelConfigOut(
            id=m["id"],
            provider=m["provider"],
            model_name=m.get("model_name", m["id"]),
            display_name=m.get("display_name", m["id"]),
            enabled=m.get("enabled", True),
            default_for_chat=m.get("default_for_chat", False),
            default_for_completion=m.get("default_for_completion", False),
            rate_limit=m.get("rate_limit"),
        )
        for m in models_data
    ]


@router.patch("/models/{model_id}", response=ModelConfigOut, auth=AuthBearer())
@transaction.atomic
def update_model(request, model_id: str, payload: ModelConfigUpdate):
    """Update model configuration in Global Defaults."""
    authorize_sync(request, action="system:configure", resource="settings")
    from admin.aaas.models.profiles import PlatformConfig

    gd = PlatformConfig.get_instance()
    defaults = gd.defaults
    models_data = defaults.get("models", [])

    updated_model: dict | None = None

    for m in models_data:
        if m["id"] == model_id:
            # Every field ModelConfigUpdate accepts is written back. Dropping
            # one on the floor while returning 200 is a silent no-op.
            if payload.enabled is not None:
                m["enabled"] = payload.enabled
            if payload.default_for_chat is not None:
                m["default_for_chat"] = payload.default_for_chat
            if payload.default_for_completion is not None:
                m["default_for_completion"] = payload.default_for_completion
            if payload.rate_limit is not None:
                m["rate_limit"] = payload.rate_limit
            updated_model = m
            break

    if updated_model is None:
        from django.http import Http404

        raise Http404(f"Model {model_id} not found")

    gd.defaults = defaults
    gd.save()

    return ModelConfigOut(
        id=updated_model["id"],
        provider=updated_model["provider"],
        model_name=updated_model.get("model_name", updated_model["id"]),
        display_name=updated_model.get("display_name", updated_model["id"]),
        enabled=updated_model.get("enabled", True),
        default_for_chat=updated_model.get("default_for_chat", False),
        default_for_completion=updated_model.get("default_for_completion", False),
        rate_limit=updated_model.get("rate_limit"),
    )


# =============================================================================
# ROLES & PERMISSIONS
# =============================================================================
@router.get("/roles", response=list[RoleOut], auth=AuthBearer())
def list_roles(request):
    """Get all platform roles from Global Defaults."""
    authorize_sync(request, action="org:read", resource="settings")
    from admin.aaas.models.profiles import PlatformConfig

    defaults = PlatformConfig.get_instance().defaults
    roles_data = defaults.get("roles", [])

    return [
        RoleOut(
            id=r["id"],
            name=r.get("name", r["id"]),
            description=r.get("description", ""),
            permissions=r.get("permissions", []),
            user_count=0,  # Calculation requires user scan, expensive for list
        )
        for r in roles_data
    ]


@router.patch("/roles/{role_id}", response=RoleOut, auth=AuthBearer())
@transaction.atomic
def update_role(request, role_id: str, payload: RoleUpdate):
    """Update role permissions.

    ``org:assign_roles`` rather than a read permission: rewriting what a role
    grants is how authority is handed out, which is the same class of act as
    assigning that role to a person.
    """
    authorize_sync(request, action="org:assign_roles", resource="settings")
    from admin.aaas.models.profiles import PlatformConfig

    gd = PlatformConfig.get_instance()
    defaults = gd.defaults
    roles_data = defaults.get("roles", [])

    updated_role: dict | None = None

    for r in roles_data:
        if r["id"] == role_id:
            if payload.permissions is not None:
                r["permissions"] = payload.permissions
            updated_role = r
            break

    if updated_role is None:
        from django.http import Http404

        raise Http404(f"Role {role_id} not found")

    gd.save()

    return RoleOut(
        id=updated_role["id"],
        name=updated_role.get("name", updated_role["id"]),
        description=updated_role.get("description", ""),
        permissions=updated_role.get("permissions", []),
        user_count=0,
    )


# =============================================================================
# SSO CONFIGURATION
# =============================================================================
# The live SSO endpoints are admin/auth/api_sso.py, mounted at /auth/sso.
# /auth/sso/test performs real OIDC discovery and /auth/sso/configure fails
# closed until a config store is wired. The two endpoints that used to live
# here were an unused duplicate, and /sso reported "saved successfully"
# without persisting anything.


# =============================================================================
# LLM PROVIDER API KEYS - VIBE Rule 164 (Vault-Mandatory)
# =============================================================================
# These endpoints manage LLM provider API keys stored in Vault.
# Path: secret/agent/api_keys/{provider}_api_key
# =============================================================================

from pydantic import BaseModel, Field

from services.common.unified_secret_manager import get_secret_manager


class LLMProviderKeyIn(BaseModel):
    """Input for setting LLM provider API key."""

    provider: str = Field(..., description="Provider name: openai, anthropic, openrouter, groq")
    api_key: str = Field(..., description="The API key value")


class LLMProviderOut(BaseModel):
    """Output for LLM provider status."""

    provider: str
    configured: bool
    masked_key: Optional[str] = None  # First 8 chars only


@router.get("/llm-providers", response=list[LLMProviderOut], auth=AuthBearer())
def list_llm_providers(request):
    """List all LLM providers and their configuration status.

    Returns which providers have API keys configured in Vault.
    VIBE Rule 164: Keys stored in Vault, never exposed.
    """
    # Integrations, not ordinary config: this reveals which credentials exist
    # and the leading characters of each. Read authority is explicit.
    authorize_sync(request, action="system:manage_integrations", resource="settings")
    sm = get_secret_manager()
    providers = ["openai", "anthropic", "openrouter", "groq", "ollama", "fireworks"]

    result = []
    for provider in providers:
        key = sm.get_provider_key(provider)
        configured = bool(key)
        masked = f"{key[:8]}..." if key and len(key) > 8 else None
        result.append(
            LLMProviderOut(
                provider=provider,
                configured=configured,
                masked_key=masked,
            )
        )

    return result


@router.post("/llm-providers", response=MessageResponse, auth=AuthBearer())
def set_llm_provider_key(request, payload: LLMProviderKeyIn):
    """Set API key for an LLM provider.

    Stores the key securely in Vault at secret/agent/api_keys/{provider}_api_key.
    VIBE Rule 164: All secrets in Vault, never in ENV or database.
    """
    # Gate first. Writing a credential into Vault is the highest-privilege
    # write on this surface: whoever holds it can redirect every LLM call the
    # platform makes. An unauthenticated request must not reach it, and must
    # not learn which provider names are valid.
    authorize_sync(request, action="system:manage_integrations", resource="settings")
    sm = get_secret_manager()

    # Validate provider name
    valid_providers = ["openai", "anthropic", "openrouter", "groq", "ollama", "fireworks"]
    provider = payload.provider.lower()

    if provider not in valid_providers:
        return MessageResponse(
            message=f"Invalid provider '{provider}'. Valid: {valid_providers}",
            success=False,
        )

    # Store in Vault
    success = sm.set_provider_key(provider, payload.api_key)

    if success:
        return MessageResponse(message=f"API key for '{provider}' saved to Vault successfully")
    else:
        return MessageResponse(
            message=f"Failed to save API key for '{provider}'. Check Vault connectivity.",
            success=False,
        )


@router.delete("/llm-providers/{provider}", response=MessageResponse, auth=AuthBearer())
def delete_llm_provider_key(request, provider: str):
    """Delete API key for an LLM provider from Vault."""
    # Same privilege as setting one: deleting a provider credential takes the
    # platform's LLM traffic down. Gate before the name is even validated.
    authorize_sync(request, action="system:manage_integrations", resource="settings")
    sm = get_secret_manager()

    success = sm.delete_provider_key(provider.lower())

    if success:
        return MessageResponse(message=f"API key for '{provider}' deleted from Vault")
    else:
        return MessageResponse(
            message=f"Failed to delete API key for '{provider}'",
            success=False,
        )
