"""Plan / quota tier model.

Defines the resource ceilings a tenant's agents run under. There is no
pricing, no billing interval and no payment concept in this product — see
AGENT.md §1.1 (Scope). This is a quota plan, not a subscription.
"""

import uuid
from decimal import Decimal

from django.db import models


class SubscriptionTier(models.Model):
    """Quota plan definition.

    Each tier defines the limits its tenant's agents run under and the
    default feature configuration for that tier. No pricing.
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

    description = models.TextField(blank=True, help_text="What this tier is for")

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
        help_text="Whether this tier can be assigned to a tenant",
    )

    sort_order = models.IntegerField(default=0, help_text="Display order")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "subscription_tiers"
        ordering = ["sort_order", "name"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["sort_order"]),
        ]
        verbose_name = "Plan Tier"
        verbose_name_plural = "Plan Tiers"

    def __str__(self):
        """Return string representation."""

        return self.name

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "max_agents": self.max_agents,
            "max_users_per_agent": self.max_users_per_agent,
            "max_monthly_voice_minutes": self.max_monthly_voice_minutes,
            "max_monthly_api_calls": self.max_monthly_api_calls,
            "max_storage_gb": float(self.max_storage_gb),
            "feature_defaults": self.feature_defaults,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
