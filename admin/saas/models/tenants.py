"""Tenant and TenantUser Models.


Per SAAS_ADMIN_SRS.md Section 4.2, 4.4
"""

import uuid

from django.db import models

from admin.saas.models.choices import TenantRole, TenantStatus
from admin.saas.models.tiers import SubscriptionTier


class Tenant(models.Model):
    """Organization/company entity.

    Each tenant has exactly one subscription tier.
    Multi-tenant isolation is enforced via tenant_id on all child resources.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100, help_text="Organization name")

    slug = models.SlugField(max_length=100, unique=True, help_text="URL-safe identifier for tenant")

    tier = models.ForeignKey(
        SubscriptionTier,
        on_delete=models.PROTECT,
        related_name="tenants",
        help_text="Current subscription tier",
    )

    status = models.CharField(
        max_length=20, choices=TenantStatus.choices, default=TenantStatus.PENDING, db_index=True
    )

    # Keycloak/Auth Integration
    keycloak_realm = models.CharField(
        max_length=100, blank=True, help_text="Keycloak realm for this tenant"
    )

    # Lago Billing Integration
    lago_customer_id = models.CharField(
        max_length=100, blank=True, db_index=True, help_text="Lago customer external ID"
    )

    lago_subscription_id = models.CharField(
        max_length=100, blank=True, help_text="Lago subscription external ID"
    )

    # Contact
    billing_email = models.EmailField(blank=True, help_text="Primary billing contact email")

    # Feature Overrides (JSONB for flexible overrides)
    feature_overrides = models.JSONField(
        default=dict, blank=True, help_text="Per-tenant feature configuration overrides"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Arbitrary metadata for integrations"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True, help_text="When trial period ends")

    class Meta:
        """Meta class implementation."""

        db_table = "tenants"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["lago_customer_id"]),
            models.Index(fields=["-created_at"]),
        ]
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self):
        """Return string representation."""

        return f"{self.name} ({self.status})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "name": self.name,
            "slug": self.slug,
            "tier_id": str(self.tier_id),
            "tier_name": self.tier.name if self.tier else None,
            "status": self.status,
            "keycloak_realm": self.keycloak_realm,
            "lago_customer_id": self.lago_customer_id,
            "lago_subscription_id": self.lago_subscription_id,
            "billing_email": self.billing_email,
            "feature_overrides": self.feature_overrides,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
        }


class TenantUser(models.Model):
    """User membership within a tenant.

    Links Keycloak users to tenants with role-based access.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")

    user_id = models.UUIDField(db_index=True, help_text="Keycloak user ID")

    email = models.EmailField(help_text="User email (denormalized from Keycloak)")

    display_name = models.CharField(max_length=200, blank=True, help_text="User display name")

    role = models.CharField(max_length=20, choices=TenantRole.choices, default=TenantRole.MEMBER)

    is_active = models.BooleanField(default=True, db_index=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "tenant_users"
        ordering = ["-created_at"]
        unique_together = [["tenant", "user_id"]]
        indexes = [
            models.Index(fields=["user_id"]),
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Tenant User"
        verbose_name_plural = "Tenant Users"

    def __str__(self):
        """Return string representation."""

        return f"{self.email} ({self.role} in {self.tenant.name})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "email": self.email,
            "display_name": self.display_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }