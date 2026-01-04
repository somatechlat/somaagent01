"""Feature Flags Admin API Router.

Migrated from: services/gateway/routers/feature_flags.py
Pure Django Ninja with Django signals and centralized config.


"""

from __future__ import annotations

import logging
from typing import Any

from django.dispatch import Signal
from django.http import HttpRequest
from ninja import Router
from pydantic import BaseModel, Field

from admin.common.exceptions import ServiceError, ValidationError

router = Router(tags=["feature_flags"])
logger = logging.getLogger(__name__)

# Django signals for config updates
feature_flag_updated = Signal()  # args: tenant, key, enabled
feature_profile_updated = Signal()  # args: tenant, profile


class FlagUpdateRequest(BaseModel):
    """Request body for updating a single flag."""

    enabled: bool = Field(..., description="Whether flag is enabled")


class ProfileUpdateRequest(BaseModel):
    """Request body for updating profile."""

    profile: str = Field(..., description="Profile name (minimal/standard/enhanced/max)")


def _get_store():
    """Get FeatureFlagsStore instance."""
    from services.common.feature_flags_store import FeatureFlagsStore

    return FeatureFlagsStore()


def _get_tenant(request: HttpRequest) -> str:
    """Extract tenant from request headers."""
    return request.headers.get("X-Tenant-Id", "default")


async def _publish_config_update(tenant: str, payload: dict):
    """Publish config update event via Kafka."""
    try:
        from django.conf import settings

        from services.gateway.providers import get_publisher

        publisher = get_publisher()
        topic = settings.KAFKA_CONVERSATION_TOPIC
        await publisher.publish(topic=topic, payload=payload, tenant=tenant)
    except Exception as exc:
        logger.warning(f"Failed to publish config update: {exc}")


@router.get("", summary="List all feature flags")
async def list_feature_flags(request: HttpRequest) -> dict[str, Any]:
    """Get all feature flags with effective values.

    Returns effective flags with current profile, flag states, and sources.
    """
    store = _get_store()
    tenant = _get_tenant(request)

    result = await store.get_effective_flags(tenant)
    logger.info(f"Feature flags retrieved for tenant: {tenant}, profile: {result['profile']}")

    return result


@router.get("/profile", summary="Get current profile")
async def get_current_profile(request: HttpRequest) -> dict[str, str]:
    """Get current feature profile."""
    store = _get_store()
    tenant = _get_tenant(request)

    profile = await store.get_profile(tenant)
    return {"profile": profile}


@router.put("/{key}", summary="Update feature flag")
async def update_feature_flag(
    request: HttpRequest, key: str, body: FlagUpdateRequest
) -> dict[str, Any]:
    """Update a single feature flag.

    Admin-only endpoint. Validates flag key exists before update.
    """
    store = _get_store()
    tenant = _get_tenant(request)

    # Validate flag key exists
    all_flags = await store.list_all_flags()
    if key not in all_flags:
        raise ValidationError(f"Invalid flag key '{key}'. Valid keys: {', '.join(all_flags)}")

    # Update flag
    success = await store.set_flag(tenant, key, body.enabled)
    if not success:
        raise ServiceError("Failed to update feature flag")

    logger.info(f"Feature flag updated: {tenant}/{key} = {body.enabled}")

    # Emit Django signal
    feature_flag_updated.send(sender=None, tenant=tenant, key=key, enabled=body.enabled)

    # Publish config update event
    await _publish_config_update(
        tenant,
        {
            "type": "system.config_update",
            "tenant": tenant,
            "source": "feature_flags",
            "action": "update_flag",
            "key": key,
            "value": body.enabled,
        },
    )

    return {
        "status": "updated",
        "key": key,
        "enabled": body.enabled,
        "tenant": tenant,
        "note": "Agent reload triggered successfully",
    }


@router.put("/profile", summary="Update feature profile")
async def update_profile(request: HttpRequest, body: ProfileUpdateRequest) -> dict[str, Any]:
    """Update feature profile and apply all profile defaults.

    Admin-only endpoint. Applies bulk flag updates efficiently.
    """
    store = _get_store()
    tenant = _get_tenant(request)

    try:
        success = await store.set_profile(tenant, body.profile)
    except ValueError as e:
        raise ValidationError(str(e))

    if not success:
        raise ServiceError("Failed to update profile")

    all_flags = await store.list_all_flags()
    flags_count = len(all_flags)

    logger.info(f"Feature profile updated: {tenant} -> {body.profile} ({flags_count} flags)")

    # Emit Django signal
    feature_profile_updated.send(sender=None, tenant=tenant, profile=body.profile)

    # Publish config update event
    await _publish_config_update(
        tenant,
        {
            "type": "system.config_update",
            "tenant": tenant,
            "source": "feature_flags",
            "action": "update_profile",
            "profile": body.profile,
        },
    )

    return {
        "status": "updated",
        "profile": body.profile,
        "flags_updated": flags_count,
        "tenant": tenant,
        "note": "Agent reload triggered successfully",
    }


@router.get("/available", summary="List available flags")
async def list_available_flags() -> dict[str, Any]:
    """List all available feature flag keys and profiles."""
    store = _get_store()
    flags = await store.list_all_flags()

    return {"flags": flags, "profiles": ["minimal", "standard", "enhanced", "max"]}