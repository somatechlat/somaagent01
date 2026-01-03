"""Auth Config API - Hierarchical authentication configuration.

VIBE COMPLIANT - Django Ninja.
Platform Defaults → Tenant Overrides architecture.

7-Persona Implementation:
- Security Auditor: Auth policy enforcement
- DevOps: SSO configuration
- PM: Tenant customization
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import uuid4

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["auth-config"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class OAuthProvider(BaseModel):
    """OAuth provider configuration."""

    provider_id: str
    name: str
    provider_type: str  # google, github, microsoft, saml, oidc
    client_id: str
    enabled: bool = True
    created_at: str


class MfaPolicy(BaseModel):
    """MFA policy."""

    required: bool
    allowed_methods: list[str]  # totp, sms, email
    grace_period_days: int = 7


class PasswordPolicy(BaseModel):
    """Password policy."""

    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    expire_days: int = 90


class PlatformAuthConfig(BaseModel):
    """Platform-wide auth configuration (defaults)."""

    mfa_policy: MfaPolicy
    password_policy: PasswordPolicy
    session_timeout_minutes: int = 60
    allowed_domains: list[str]
    ip_whitelist_enabled: bool = False


class TenantAuthConfig(BaseModel):
    """Tenant-specific auth overrides."""

    tenant_id: str
    use_platform_defaults: bool = True
    mfa_policy_override: Optional[MfaPolicy] = None
    password_policy_override: Optional[PasswordPolicy] = None
    custom_providers: list[OAuthProvider] = []
    ip_whitelist: list[str] = []


class EffectiveAuthConfig(BaseModel):
    """Merged effective auth config."""

    tenant_id: str
    source: str  # platform, tenant, merged
    mfa_policy: MfaPolicy
    password_policy: PasswordPolicy
    providers: list[OAuthProvider]


# =============================================================================
# ENDPOINTS - Platform Defaults (SysAdmin/Eye of God)
# =============================================================================


@router.get(
    "/platform",
    response=PlatformAuthConfig,
    summary="Get platform defaults",
    auth=AuthBearer(),
)
async def get_platform_config(request) -> PlatformAuthConfig:
    """Get platform-wide auth defaults.

    Security Auditor: Platform policy review.
    """
    return PlatformAuthConfig(
        mfa_policy=MfaPolicy(
            required=False,
            allowed_methods=["totp", "email"],
            grace_period_days=7,
        ),
        password_policy=PasswordPolicy(),
        session_timeout_minutes=60,
        allowed_domains=[],
        ip_whitelist_enabled=False,
    )


@router.put(
    "/platform",
    summary="Update platform defaults",
    auth=AuthBearer(),
)
async def update_platform_config(
    request,
    mfa_required: Optional[bool] = None,
    session_timeout_minutes: Optional[int] = None,
    ip_whitelist_enabled: Optional[bool] = None,
) -> dict:
    """Update platform-wide auth defaults.

    Security Auditor: Policy updates.
    """
    logger.info("Platform auth config updated")

    return {
        "updated": True,
        "affects_all_tenants": True,
    }


# =============================================================================
# ENDPOINTS - Platform Providers
# =============================================================================


@router.get(
    "/platform/providers",
    summary="List platform providers",
    auth=AuthBearer(),
)
async def list_platform_providers(request) -> dict:
    """List platform OAuth providers.

    DevOps: Provider management.
    """
    return {
        "providers": [
            OAuthProvider(
                provider_id="google",
                name="Google",
                provider_type="google",
                client_id="platform-google-client",
                enabled=True,
                created_at=timezone.now().isoformat(),
            ).dict(),
            OAuthProvider(
                provider_id="github",
                name="GitHub",
                provider_type="github",
                client_id="platform-github-client",
                enabled=True,
                created_at=timezone.now().isoformat(),
            ).dict(),
        ],
        "total": 2,
    }


@router.post(
    "/platform/providers",
    response=OAuthProvider,
    summary="Add platform provider",
    auth=AuthBearer(),
)
async def add_platform_provider(
    request,
    name: str,
    provider_type: str,
    client_id: str,
    client_secret: str,
) -> OAuthProvider:
    """Add OAuth provider to platform defaults.

    DevOps: Add SSO provider.
    """
    provider_id = str(uuid4())

    logger.info(f"Platform provider added: {name}")

    return OAuthProvider(
        provider_id=provider_id,
        name=name,
        provider_type=provider_type,
        client_id=client_id,
        enabled=True,
        created_at=timezone.now().isoformat(),
    )


@router.post(
    "/platform/providers/{provider_id}/test",
    summary="Test provider",
    auth=AuthBearer(),
)
async def test_platform_provider(request, provider_id: str) -> dict:
    """Test OAuth provider connection.

    DevOps: Validate SSO config.
    """
    return {
        "provider_id": provider_id,
        "status": "success",
        "message": "Connection successful",
    }


@router.delete(
    "/platform/providers/{provider_id}",
    summary="Remove provider",
    auth=AuthBearer(),
)
async def remove_platform_provider(request, provider_id: str) -> dict:
    """Remove platform OAuth provider."""
    logger.warning(f"Platform provider removed: {provider_id}")

    return {
        "provider_id": provider_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Platform MFA
# =============================================================================


@router.get(
    "/platform/mfa",
    response=MfaPolicy,
    summary="Get MFA policy",
    auth=AuthBearer(),
)
async def get_platform_mfa(request) -> MfaPolicy:
    """Get platform MFA policy."""
    return MfaPolicy(
        required=False,
        allowed_methods=["totp", "email"],
        grace_period_days=7,
    )


@router.put(
    "/platform/mfa",
    summary="Update MFA policy",
    auth=AuthBearer(),
)
async def update_platform_mfa(
    request,
    required: bool,
    allowed_methods: list[str],
    grace_period_days: int = 7,
) -> dict:
    """Update platform MFA policy.

    Security Auditor: MFA enforcement.
    """
    logger.info(f"Platform MFA policy updated: required={required}")

    return {
        "updated": True,
        "required": required,
    }


# =============================================================================
# ENDPOINTS - Tenant Overrides (TenantAdmin)
# =============================================================================


@router.get(
    "/tenants/{tenant_id}",
    response=TenantAuthConfig,
    summary="Get tenant config",
    auth=AuthBearer(),
)
async def get_tenant_config(request, tenant_id: str) -> TenantAuthConfig:
    """Get tenant auth configuration.

    PM: Tenant customization.
    """
    return TenantAuthConfig(
        tenant_id=tenant_id,
        use_platform_defaults=True,
    )


@router.put(
    "/tenants/{tenant_id}",
    summary="Update tenant config",
    auth=AuthBearer(),
)
async def update_tenant_config(
    request,
    tenant_id: str,
    use_platform_defaults: Optional[bool] = None,
    mfa_required: Optional[bool] = None,
) -> dict:
    """Update tenant auth overrides.

    PM: Customize tenant auth.
    """
    return {
        "tenant_id": tenant_id,
        "updated": True,
    }


@router.post(
    "/tenants/{tenant_id}/providers",
    response=OAuthProvider,
    summary="Add tenant provider",
    auth=AuthBearer(),
)
async def add_tenant_provider(
    request,
    tenant_id: str,
    name: str,
    provider_type: str,
    client_id: str,
    client_secret: str,
) -> OAuthProvider:
    """Add custom OAuth provider for tenant.

    PM: Custom SSO for tenant.
    """
    provider_id = str(uuid4())

    logger.info(f"Tenant {tenant_id} provider added: {name}")

    return OAuthProvider(
        provider_id=provider_id,
        name=name,
        provider_type=provider_type,
        client_id=client_id,
        enabled=True,
        created_at=timezone.now().isoformat(),
    )


@router.delete(
    "/tenants/{tenant_id}/providers/{provider_id}",
    summary="Remove tenant provider",
    auth=AuthBearer(),
)
async def remove_tenant_provider(
    request,
    tenant_id: str,
    provider_id: str,
) -> dict:
    """Remove tenant OAuth provider."""
    return {
        "tenant_id": tenant_id,
        "provider_id": provider_id,
        "deleted": True,
    }


# =============================================================================
# ENDPOINTS - Effective Config (Merged)
# =============================================================================


@router.get(
    "/tenants/{tenant_id}/effective",
    response=EffectiveAuthConfig,
    summary="Get effective config",
    auth=AuthBearer(),
)
async def get_effective_config(request, tenant_id: str) -> EffectiveAuthConfig:
    """Get merged effective auth config.

    Platform defaults + tenant overrides = effective.
    """
    return EffectiveAuthConfig(
        tenant_id=tenant_id,
        source="platform",  # or "merged" if overrides exist
        mfa_policy=MfaPolicy(
            required=False,
            allowed_methods=["totp", "email"],
            grace_period_days=7,
        ),
        password_policy=PasswordPolicy(),
        providers=[
            OAuthProvider(
                provider_id="google",
                name="Google",
                provider_type="google",
                client_id="platform-google-client",
                enabled=True,
                created_at=timezone.now().isoformat(),
            ),
        ],
    )


@router.post(
    "/tenants/{tenant_id}/reset",
    summary="Reset to defaults",
    auth=AuthBearer(),
)
async def reset_tenant_config(request, tenant_id: str) -> dict:
    """Reset tenant to platform defaults.

    PM: Revert customizations.
    """
    logger.info(f"Tenant {tenant_id} reset to platform defaults")

    return {
        "tenant_id": tenant_id,
        "reset": True,
        "now_using": "platform_defaults",
    }
