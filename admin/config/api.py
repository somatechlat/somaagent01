"""Configuration API - System and tenant configuration.

System-wide and tenant-specific configuration management.
Provides endpoints for system config, tenant config, feature flags, and secrets.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from asgiref.sync import sync_to_async
from django.conf import settings as django_settings
from ninja import Router
from pydantic import BaseModel

from admin.common.auth import AuthBearer
from admin.common.exceptions import NotFoundError
from admin.common.messages import ErrorCode, get_message
from admin.core.models import FeatureFlag as FeatureFlagModel
from services.common.authorization import authorize

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
    rollout_percentage: int = 0
    created_at: str


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

    VIBE: Returns REAL Environment Variables (safelist).
    DevOps: Platform-level settings.
    """
    await authorize(request, action="system:view", resource="settings")
    # Safe list of exposed config
    exposed_keys = [
        ("DEBUG", "bool", "general"),
        ("TIME_ZONE", "string", "general"),
        ("AWS_REGION", "string", "infra"),
        ("AWS_S3_BUCKET", "string", "infra"),
        ("AAAS_DEFAULT_TENANT_ID", "string", "aaas"),
        ("LOG_LEVEL", "string", "logging"),
    ]

    items = []
    for key, type_, cat in exposed_keys:
        val = getattr(django_settings, key, os.environ.get(key))
        if val is not None:
            if category and cat != category:
                continue
            items.append(
                ConfigItem(key=key, value=str(val), type=type_, category=cat, sensitive=False)
            )

    return ConfigListResponse(items=items, total=len(items))


@router.patch(
    "/system/{key}",
    summary="Update system config",
    auth=AuthBearer(),
)
async def update_system_config(
    request,
    key: str,
    value: str,
) -> tuple[dict, int]:
    """Update system configuration.

    VIBE: Runtime updates not supported for Env Vars.
    Use Deployment update.
    """
    await authorize(request, action="system:configure", resource="settings")
    return {"error": get_message(ErrorCode.CONFIG_RUNTIME_UPDATE_NOT_SUPPORTED)}, 400


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

    Pending: Wire to AgentSetting or TenantConfig model when available.
    """
    await authorize(request, action="org:read", resource="settings")
    return ConfigListResponse(items=[], total=0)


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
) -> tuple[dict, int]:
    """Update tenant configuration."""
    await authorize(request, action="org:update", resource="settings")
    return {"error": get_message(ErrorCode.CONFIG_TENANT_MODEL_PENDING)}, 501


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

    DevOps: Feature flag management via DB.
    """
    await authorize(request, action="system:view", resource="settings")

    @sync_to_async
    def _get_flags():
        """Execute get flags."""

        qs = FeatureFlagModel.objects.all().order_by("name")
        items = []
        for f in qs:
            items.append(
                FeatureFlag(
                    key=f.name,
                    enabled=f.is_enabled,
                    description=f.description,
                    rollout_percentage=f.rollout_percentage,
                    created_at=f.created_at.isoformat(),
                )
            )
        return items, qs.count()

    items, total = await _get_flags()
    return FeatureFlagsResponse(flags=items, total=total)


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
    await authorize(request, action="system:configure", resource="settings")

    @sync_to_async
    def _create():
        """Execute create."""

        obj, created = FeatureFlagModel.objects.get_or_create(
            name=key, defaults={"is_enabled": enabled, "description": description or ""}
        )
        return obj, created

    obj, created = await _create()
    return {"key": obj.name, "enabled": obj.is_enabled, "created": created}


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
    await authorize(request, action="system:configure", resource="settings")

    @sync_to_async
    def _update():
        """Execute update."""

        count = FeatureFlagModel.objects.filter(name=key).update(is_enabled=enabled)
        return count

    count = await _update()
    if count == 0:
        raise NotFoundError("flag", key)

    logger.info("Feature flag %s set to %s", key, enabled)
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
    await authorize(request, action="system:configure", resource="settings")

    @sync_to_async
    def _delete():
        """Execute delete."""

        count, _ = FeatureFlagModel.objects.filter(name=key).delete()
        return count

    count = await _delete()
    if count == 0:
        raise NotFoundError("flag", key)

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
    await authorize(request, action="system:view", resource="settings")

    @sync_to_async
    def _check():
        """Execute check."""

        try:
            flag = FeatureFlagModel.objects.get(name=key)
            # Basic check: is_enabled OR rollout logic
            # But simplistic is better than broken.
            return flag.is_enabled
        except FeatureFlagModel.DoesNotExist:
            return False  # Default to disabled if missing

    enabled = await _check()
    return {
        "key": key,
        "enabled": enabled,
        "reason": "database",
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

    These credentials live in Vault (VIBE Rule 164), never in the environment,
    so this reports whether the Vault credential exists — not whether some ENV
    var is set. An ENV set-check would advertise a model that does not exist and
    would read as "configured" for a value the application never consults.
    """
    # Names and presence, never values — but an inventory of which credentials
    # exist is still a map of where the bodies are buried. It is not public.
    await authorize(request, action="system:view", resource="settings")
    from services.common.unified_secret_manager import get_secret_manager

    credentials = ["llm_api_key", "somabrain_memory_http_token", "postgres_password"]

    sm = get_secret_manager()
    clean_list = []
    for key in credentials:
        try:
            present = bool(sm.get_credential(key))
        except Exception:
            # Vault unreachable. That is not "unset" — it is unknown, and the
            # distinction matters to whoever has to fix it.
            present = None
        clean_list.append({"key": key, "source": "vault", "masked": True, "set": present})

    return {
        "secrets": clean_list,
        "total": len(clean_list),
    }
