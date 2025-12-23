"""
Subscription Tiers API Router
Manage subscription tiers and pricing.

Per SRS Section 4.3.1 - Subscription Tier Builder.
"""

from uuid import uuid4

from django.db import transaction
from django.utils.text import slugify
from ninja import Router

from admin.saas.api.schemas import (
    MessageResponse,
    SubscriptionTierOut,
    TierCreate,
    TierLimits,
    TierUpdate,
)
from admin.saas.models import SubscriptionTier, Tenant

router = Router()


def _tier_to_out(tier: SubscriptionTier) -> SubscriptionTierOut:
    """Convert SubscriptionTier model to output schema."""
    # Get feature codes from tier_features
    features = list(tier.tier_features.filter(enabled=True).values_list("feature__code", flat=True))

    return SubscriptionTierOut(
        id=str(tier.id),
        name=tier.name,
        slug=tier.slug,
        price=tier.price_cents / 100.0,
        billing_period=tier.billing_interval,
        limits=TierLimits(
            agents=tier.max_agents,
            users=tier.max_users_per_agent,
            tokens_per_month=tier.token_quota_monthly,
            storage_gb=tier.storage_quota_gb,
        ),
        features=features,
        popular=tier.is_popular,
        active_count=Tenant.objects.filter(tier=tier, status="active").count(),
    )


@router.get("", response=list[SubscriptionTierOut])
def list_tiers(request):
    """Get all subscription tiers."""
    tiers = SubscriptionTier.objects.filter(is_active=True).prefetch_related(
        "tier_features__feature"
    )
    return [_tier_to_out(t) for t in tiers]


@router.get("/{tier_id}", response=SubscriptionTierOut)
def get_tier(request, tier_id: str):
    """Get single tier details."""
    tier = SubscriptionTier.objects.prefetch_related("tier_features__feature").get(id=tier_id)
    return _tier_to_out(tier)


@router.post("", response=SubscriptionTierOut)
@transaction.atomic
def create_tier(request, payload: TierCreate):
    """Create a new subscription tier."""
    tier = SubscriptionTier.objects.create(
        id=uuid4(),
        name=payload.name,
        slug=slugify(payload.slug),
        price_cents=payload.price_cents,
        billing_interval=payload.billing_interval,
        max_agents=payload.limits.get("agents", 1),
        max_users_per_agent=payload.limits.get("users", 5),
        token_quota_monthly=payload.limits.get("tokens_per_month", 10000),
        storage_quota_gb=payload.limits.get("storage_gb", 1.0),
        is_active=True,
    )

    # Assign features if provided
    if payload.features:
        from admin.saas.models import SaasFeature, TierFeature

        for feature_code in payload.features:
            feature = SaasFeature.objects.filter(code=feature_code).first()
            if feature:
                TierFeature.objects.create(
                    id=uuid4(),
                    tier=tier,
                    feature=feature,
                    enabled=True,
                )

    # TODO: Sync to Lago as a plan
    return _tier_to_out(tier)


@router.patch("/{tier_id}", response=SubscriptionTierOut)
@transaction.atomic
def update_tier(request, tier_id: str, payload: TierUpdate):
    """Update a subscription tier."""
    tier = SubscriptionTier.objects.get(id=tier_id)

    if payload.name is not None:
        tier.name = payload.name
    if payload.price_cents is not None:
        tier.price_cents = payload.price_cents
    if payload.limits is not None:
        tier.max_agents = payload.limits.get("agents", tier.max_agents)
        tier.max_users_per_agent = payload.limits.get("users", tier.max_users_per_agent)
        tier.token_quota_monthly = payload.limits.get("tokens_per_month", tier.token_quota_monthly)
        tier.storage_quota_gb = payload.limits.get("storage_gb", tier.storage_quota_gb)
    if payload.is_active is not None:
        tier.is_active = payload.is_active

    tier.save()

    # Update features if provided
    if payload.features is not None:
        from admin.saas.models import SaasFeature, TierFeature

        # Remove existing features not in new list
        tier.tier_features.exclude(feature__code__in=payload.features).delete()

        # Add new features
        existing_codes = set(tier.tier_features.values_list("feature__code", flat=True))
        for feature_code in payload.features:
            if feature_code not in existing_codes:
                feature = SaasFeature.objects.filter(code=feature_code).first()
                if feature:
                    TierFeature.objects.create(
                        id=uuid4(),
                        tier=tier,
                        feature=feature,
                        enabled=True,
                    )

    # TODO: Sync changes to Lago
    return _tier_to_out(tier)


@router.delete("/{tier_id}", response=MessageResponse)
@transaction.atomic
def delete_tier(request, tier_id: str):
    """Soft-delete a tier by marking as inactive."""
    tier = SubscriptionTier.objects.get(id=tier_id)

    # Check if any tenants are using this tier
    active_tenants = Tenant.objects.filter(tier=tier, status="active").count()
    if active_tenants > 0:
        return MessageResponse(
            message=f"Cannot delete tier with {active_tenants} active tenants",
            success=False,
        )

    tier.is_active = False
    tier.save()
    return MessageResponse(message=f"Tier {tier.name} deactivated")
