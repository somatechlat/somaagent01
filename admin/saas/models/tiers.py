"""Subscription Tier Model.

VIBE COMPLIANT - Django ORM, Lago integration, proper indexes.
Per SAAS_ADMIN_SRS.md Section 4.3
"""

import uuid
from decimal import Decimal

from django.db import models

from admin.saas.models.choices import BillingInterval


class SubscriptionTier(models.Model):
    """Subscription plan/tier definition.

    Integrates with Lago for billing management.
    Each tier defines limits, pricing, and available features.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier"
    )

    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tier display name (e.g., 'Starter', 'Team', 'Enterprise')",
    )

    slug = models.SlugField(max_length=50, unique=True, help_text="URL-safe identifier")

    description = models.TextField(blank=True, help_text="Marketing description for the tier")

    # Pricing
    base_price_cents = models.BigIntegerField(
        default=0, help_text="Base monthly price in cents (USD)"
    )

    billing_interval = models.CharField(
        max_length=20,
        choices=BillingInterval.choices,
        default=BillingInterval.MONTHLY,
        help_text="Billing cycle",
    )

    # Lago Integration
    lago_plan_code = models.CharField(
        max_length=100, blank=True, help_text="Lago billing plan code"
    )

    # Limits
    max_agents = models.IntegerField(default=1, help_text="Maximum agents allowed")

    max_users_per_agent = models.IntegerField(default=5, help_text="Maximum users per agent")

    max_monthly_voice_minutes = models.IntegerField(
        default=60, help_text="Monthly voice minutes allowance"
    )

    max_monthly_api_calls = models.IntegerField(
        default=1000, help_text="Monthly API calls allowance"
    )

    max_storage_gb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
        help_text="Storage allowance in GB",
    )

    # Feature Configuration (defaults for this tier)
    feature_defaults = models.JSONField(
        default=dict, blank=True, help_text="Default feature configurations for this tier"
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this tier is available for new subscriptions",
    )

    is_public = models.BooleanField(
        default=True, help_text="Whether tier is shown on public pricing page"
    )

    sort_order = models.IntegerField(default=0, help_text="Display order on pricing page")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription_tiers"
        ordering = ["sort_order", "base_price_cents"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["sort_order"]),
        ]
        verbose_name = "Subscription Tier"
        verbose_name_plural = "Subscription Tiers"

    def __str__(self):
        return f"{self.name} (${self.base_price_cents / 100:.2f}/mo)"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "base_price_cents": self.base_price_cents,
            "billing_interval": self.billing_interval,
            "lago_plan_code": self.lago_plan_code,
            "max_agents": self.max_agents,
            "max_users_per_agent": self.max_users_per_agent,
            "max_monthly_voice_minutes": self.max_monthly_voice_minutes,
            "max_monthly_api_calls": self.max_monthly_api_calls,
            "max_storage_gb": float(self.max_storage_gb),
            "feature_defaults": self.feature_defaults,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
