"""
Features API Router
Manage SAAS features and feature flags.

Per SRS Section 4.3.1 - Tier Builder Feature Management.
"""

from typing import Any, Optional

from django.db import transaction
from ninja import Router

from admin.saas.api.schemas import (
    FeatureFlagOut,
    FeatureFlagUpdate,
    FeatureOut,
    MessageResponse,
)
import logging
from admin.common.messages import ErrorCode, SuccessCode, get_message
from admin.saas.models import FeatureProvider, SaasFeature, TierFeature

logger = logging.getLogger(__name__)

router = Router()


# =============================================================================
# SAAS FEATURES (for Tier Builder)
# =============================================================================
@router.get("", response=list[FeatureOut])
def list_features(request):
    """Get all available SAAS features for tier builder."""
    features = SaasFeature.objects.filter(is_active=True).order_by("sort_order")
    return [
        FeatureOut(
            id=str(f.id),
            code=f.code,
            name=f.name,
            description=f.description,
            category=f.category,
            icon=f.icon,
            enabled=f.is_active,
            default_config=f.default_settings or {},
        )
        for f in features
    ]


@router.get("/{feature_id}", response=FeatureOut)
def get_feature(request, feature_id: str):
    """Get single feature details."""
    try:
        f = SaasFeature.objects.get(id=feature_id)
        return FeatureOut(
            id=str(f.id),
            code=f.code,
            name=f.name,
            description=f.description,
            category=f.category,
            icon=f.icon,
            enabled=f.is_active,
            default_config=f.default_settings or {},
        )
    except SaasFeature.DoesNotExist:
        # Ninja will handle 404 if we raise Http404, or we can return error response if schema allows
        # For strict schema (FeatureOut), raising 404 is cleaner than returning ErrorResponse
        from django.http import Http404
        raise Http404(get_message(ErrorCode.FEATURE_NOT_FOUND, code=feature_id))


@router.get("/{feature_code}/providers", response=list[dict])
def list_feature_providers(request, feature_code: str):
    """Get available providers for a feature (e.g., voice providers)."""
    providers = FeatureProvider.objects.filter(
        feature__code=feature_code,
        is_active=True,
    ).order_by("sort_order")

    return [
        {
            "id": str(p.id),
            "code": p.code,
            "name": p.name,
            "description": p.description,
            "icon": p.icon,
            "feature_id": str(p.feature_id),
            "config_schema": p.config_schema or {},
            "is_default": p.is_default,
        }
        for p in providers
    ]


# =============================================================================
# TIER FEATURES (Feature assignments to tiers)
# =============================================================================
@router.get("/tiers/{tier_id}", response=list[dict])
def list_tier_features(request, tier_id: str):
    """Get all features assigned to a tier."""
    tier_features = TierFeature.objects.filter(tier_id=tier_id).select_related("feature")

    return [
        {
            "id": str(tf.id),
            "feature_id": str(tf.feature_id),
            "feature_code": tf.feature.code,
            "feature_name": tf.feature.name,
            "enabled": tf.enabled,
            "quota_limit": tf.quota_limit,
            "settings_override": tf.settings_override or {},
        }
        for tf in tier_features
    ]


@router.post("/tiers/{tier_id}/{feature_code}", response=dict)
@transaction.atomic
def assign_feature_to_tier(
    request,
    tier_id: str,
    feature_code: str,
    settings: Optional[dict[str, Any]] = None,
):
    """Assign a feature to a tier with optional settings override."""
    try:
        feature = SaasFeature.objects.get(code=feature_code)
    except SaasFeature.DoesNotExist:
        from django.http import Http404
        raise Http404(get_message(ErrorCode.FEATURE_NOT_FOUND, code=feature_code))

    tf, created = TierFeature.objects.update_or_create(
        tier_id=tier_id,
        feature=feature,
        defaults={
            "is_enabled": True,
            "settings_override": settings or {},
        },
    )

    action = "assigned to" if created else "updated on"
    logger.info(f"Feature {feature_code} {action} tier {tier_id}")

    return {
        "id": str(tf.id),
        "feature_code": feature_code,
        "enabled": tf.is_enabled,
        "created": created,
    }


@router.delete("/tiers/{tier_id}/{feature_code}", response=MessageResponse)
@transaction.atomic
def remove_feature_from_tier(request, tier_id: str, feature_code: str):
    """Remove a feature from a tier."""
    deleted, _ = TierFeature.objects.filter(
        tier_id=tier_id,
        feature__code=feature_code,
    ).delete()

    if deleted:
        logger.info(f"Feature {feature_code} removed from tier {tier_id}")
        return MessageResponse(message=get_message(SuccessCode.FEATURE_REMOVED, code=feature_code))
    
    return MessageResponse(
        message=get_message(ErrorCode.FEATURE_NOT_ON_TIER, code=feature_code),
        success=False,
    )


@router.patch("/tiers/{tier_id}/{feature_code}", response=dict)
@transaction.atomic
def update_tier_feature_settings(
    request,
    tier_id: str,
    feature_code: str,
    settings: dict[str, Any],
):
    """Update feature settings for a specific tier."""
    tf = TierFeature.objects.select_related("feature").get(
        tier_id=tier_id,
        feature__code=feature_code,
    )

    # Merge with existing settings
    existing = tf.settings_override or {}
    existing.update(settings)
    tf.settings_override = existing
    tf.save()

    return {
        "id": str(tf.id),
        "feature_code": feature_code,
        "settings_override": tf.settings_override,
    }


# =============================================================================
# FEATURE FLAGS (Legacy - for rollout control)
# =============================================================================
@router.get("/flags", response=list[FeatureFlagOut])
def list_feature_flags(request):
    """Get all feature flags."""
    # TODO: Implement feature flags table or use external service
    return []


@router.patch("/flags/{flag_id}", response=FeatureFlagOut)
def update_feature_flag(request, flag_id: str, payload: FeatureFlagUpdate):
    """Update a feature flag."""
    # TODO: Implement feature flag updates
    raise Exception("Feature flags not yet implemented")
