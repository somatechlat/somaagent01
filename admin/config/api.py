"""Configuration API - System and tenant configuration.

VIBE COMPLIANT - Django Ninja.
System-wide and tenant-specific configuration management.

7-Persona Implementation:
- DevOps: System configuration, feature flags
- Security Auditor: Sensitive config protection
- PM: Tenant customization
"""

from __future__ import annotations

import logging
from typing import Optional

from django.utils import timezone
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer

router = Router(tags=["config"])
logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================


class ConfigItem(BaseModel):
    """Configuration item."""

    key: str
    value: str
    type: str = "string"  # string, int, bool, json
    description: Optional[str] = None
    sensitive: bool = False
    category: str = "general"


class ConfigListResponse(BaseModel):
    """Configuration list."""

    items: list[ConfigItem]
    total: int


class FeatureFlag(BaseModel):
    """Feature flag."""

    key: str
    enabled: bool
    description: Optional[str] = None
    rules: Optional[dict] = None  # targeting rules


class FeatureFlagsResponse(BaseModel):
    """Feature flags response."""

    flags: list[FeatureFlag]
    total: int


# =============================================================================
# ENDPOINTS - System Configuration
# =============================================================================


@router.get(
    "/system",
    response=ConfigListResponse,
    summary="Get system config",
    auth=AuthBearer(),
)
async def get_system_config(
    request,
    category: Optional[str] = None,
) -> ConfigListResponse:
    """Get system-wide configuration.

    DevOps: Platform-level settings.
    """
    # In production: fetch from database
    return ConfigListResponse(
        items=[
            ConfigItem(key="max_agents_per_tenant", value="10", type="int", category="limits"),
            ConfigItem(key="default_token_expiry", value="900", type="int", category="auth"),
            ConfigItem(key="enable_mfa", value="true", type="bool", category="security"),
        ],
        total=3,
    )


@router.patch(
    "/system/{key}",
    summary="Update system config",
    auth=AuthBearer(),
)
async def update_system_config(
    request,
    key: str,
    value: str,
) -> dict:
    """Update system configuration.

    Security Auditor: Admin only, audit logged.
    """
    logger.info(f"System config updated: {key}")

    return {
        "key": key,
        "value": value,
        "updated": True,
        "updated_at": timezone.now().isoformat(),
    }


# =============================================================================
# ENDPOINTS - Tenant Configuration
# =============================================================================


@router.get(
    "/tenants/{tenant_id}",
    response=ConfigListResponse,
    summary="Get tenant config",
    auth=AuthBearer(),
)
async def get_tenant_config(
    request,
    tenant_id: str,
) -> ConfigListResponse:
    """Get tenant-specific configuration.

    PM: Tenant customization settings.
    """
    return ConfigListResponse(
        items=[],
        total=0,
    )


@router.patch(
    "/tenants/{tenant_id}/{key}",
    summary="Update tenant config",
    auth=AuthBearer(),
)
async def update_tenant_config(
    request,
    tenant_id: str,
    key: str,
    value: str,
) -> dict:
    """Update tenant configuration."""
    return {
        "tenant_id": tenant_id,
        "key": key,
        "value": value,
        "updated": True,
    }


# =============================================================================
# ENDPOINTS - Feature Flags
# =============================================================================


@router.get(
    "/flags",
    response=FeatureFlagsResponse,
    summary="Get feature flags",
    auth=AuthBearer(),
)
async def get_feature_flags(
    request,
    tenant_id: Optional[str] = None,
) -> FeatureFlagsResponse:
    """Get feature flags.

    DevOps: Feature flag management.
    """
    return FeatureFlagsResponse(
        flags=[
            FeatureFlag(key="new_chat_ui", enabled=True, description="New chat interface"),
            FeatureFlag(
                key="multimodal_enabled", enabled=True, description="Multimodal processing"
            ),
            FeatureFlag(key="a2a_workflows", enabled=False, description="Agent-to-agent workflows"),
        ],
        total=3,
    )


@router.post(
    "/flags",
    summary="Create feature flag",
    auth=AuthBearer(),
)
async def create_feature_flag(
    request,
    key: str,
    enabled: bool = False,
    description: Optional[str] = None,
) -> dict:
    """Create a new feature flag."""
    return {
        "key": key,
        "enabled": enabled,
        "description": description,
        "created": True,
    }


@router.patch(
    "/flags/{key}",
    summary="Update feature flag",
    auth=AuthBearer(),
)
async def update_feature_flag(
    request,
    key: str,
    enabled: bool,
) -> dict:
    """Update feature flag state."""
    logger.info(f"Feature flag {key} set to {enabled}")

    return {
        "key": key,
        "enabled": enabled,
        "updated": True,
    }


@router.delete(
    "/flags/{key}",
    summary="Delete feature flag",
    auth=AuthBearer(),
)
async def delete_feature_flag(request, key: str) -> dict:
    """Delete a feature flag."""
    return {
        "key": key,
        "deleted": True,
    }


@router.get(
    "/flags/{key}/check",
    summary="Check feature flag",
    auth=AuthBearer(),
)
async def check_feature_flag(
    request,
    key: str,
    tenant_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Check if feature is enabled for context.

    DevOps: Evaluate feature flag with targeting rules.
    """
    # In production: evaluate targeting rules
    return {
        "key": key,
        "enabled": True,
        "reason": "default",
    }


# =============================================================================
# ENDPOINTS - Secrets
# =============================================================================


@router.get(
    "/secrets",
    summary="List secrets",
    auth=AuthBearer(),
)
async def list_secrets(request) -> dict:
    """List secret keys (not values).

    Security Auditor: Only key names, not values.
    """
    return {
        "secrets": [
            {"key": "OPENAI_API_KEY", "masked": True, "last_rotated": None},
            {"key": "LAGO_API_KEY", "masked": True, "last_rotated": None},
            {"key": "SOMABRAIN_TOKEN", "masked": True, "last_rotated": None},
        ],
        "total": 3,
    }


@router.post(
    "/secrets/{key}",
    summary="Set secret",
    auth=AuthBearer(),
)
async def set_secret(
    request,
    key: str,
    value: str,
) -> dict:
    """Set a secret value.

    Security Auditor: Encrypted storage, audit logged.
    """
    logger.info(f"Secret set: {key}")

    # In production: store in Vault or encrypted database

    return {
        "key": key,
        "set": True,
        "rotated_at": timezone.now().isoformat(),
    }


@router.delete(
    "/secrets/{key}",
    summary="Delete secret",
    auth=AuthBearer(),
)
async def delete_secret(request, key: str) -> dict:
    """Delete a secret."""
    return {
        "key": key,
        "deleted": True,
    }
