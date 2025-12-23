"""Feature Catalog Models.

VIBE COMPLIANT - Tier Builder integration, provider management.
Per SAAS_ADMIN_SRS.md Section 4.3.1
"""

import uuid

from django.db import models

from admin.saas.models.choices import FeatureCategory, QuotaEnforcementPolicy
from admin.saas.models.tiers import SubscriptionTier


class SaasFeature(models.Model):
    """Platform feature catalog entry.

    Master list of all available platform features.
    Used by Tier Builder to configure feature availability per tier.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    code = models.CharField(
        max_length=50, unique=True, help_text="Unique feature code (e.g., 'voice', 'memory', 'mcp')"
    )

    name = models.CharField(max_length=100, help_text="Display name")

    description = models.TextField(blank=True, help_text="Feature description for UI")

    category = models.CharField(
        max_length=30,
        choices=FeatureCategory.choices,
        db_index=True,
        help_text="Feature category for grouping",
    )

    # Icon (Material Symbol name)
    icon = models.CharField(
        max_length=50, default="settings", help_text="Google Material Symbol icon name"
    )

    # Default configuration schema
    config_schema = models.JSONField(
        default=dict, blank=True, help_text="JSON Schema for feature configuration"
    )

    # Default settings when feature is enabled
    default_settings = models.JSONField(
        default=dict, blank=True, help_text="Default settings when feature is enabled"
    )

    # Billing integration
    is_billable = models.BooleanField(
        default=False, help_text="Whether feature has usage-based billing"
    )

    lago_billable_metric_code = models.CharField(
        max_length=100, blank=True, help_text="Lago billable metric code for usage tracking"
    )

    # UI Configuration
    requires_modal = models.BooleanField(
        default=True, help_text="Whether feature requires full-screen config modal"
    )

    modal_component = models.CharField(
        max_length=100, blank=True, help_text="Lit component name for settings modal"
    )

    # Status
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Whether feature is available for configuration"
    )

    is_beta = models.BooleanField(default=False, help_text="Whether feature is in beta")

    sort_order = models.IntegerField(default=0, help_text="Display order in feature catalog")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saas_features"
        ordering = ["category", "sort_order", "name"]
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["category"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["sort_order"]),
        ]
        verbose_name = "SAAS Feature"
        verbose_name_plural = "SAAS Features"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "config_schema": self.config_schema,
            "default_settings": self.default_settings,
            "is_billable": self.is_billable,
            "lago_billable_metric_code": self.lago_billable_metric_code,
            "requires_modal": self.requires_modal,
            "modal_component": self.modal_component,
            "is_active": self.is_active,
            "is_beta": self.is_beta,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TierFeature(models.Model):
    """Feature assignment/configuration for a subscription tier.

    Junction table linking tiers to features with tier-specific settings.
    Used by Tier Builder for drag-and-drop feature assignment.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tier = models.ForeignKey(
        SubscriptionTier, on_delete=models.CASCADE, related_name="tier_features"
    )

    feature = models.ForeignKey(
        SaasFeature, on_delete=models.CASCADE, related_name="tier_assignments"
    )

    # Feature status for this tier
    is_enabled = models.BooleanField(
        default=True, help_text="Whether feature is enabled for this tier"
    )

    # Tier-specific settings override
    settings_override = models.JSONField(
        default=dict, blank=True, help_text="Tier-specific settings that override feature defaults"
    )

    # Quota/limits for this tier
    quota_limit = models.IntegerField(
        null=True, blank=True, help_text="Usage quota limit for this tier (null = unlimited)"
    )

    quota_policy = models.CharField(
        max_length=20,
        choices=QuotaEnforcementPolicy.choices,
        default=QuotaEnforcementPolicy.SOFT,
        help_text="How quota is enforced",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saas_tier_features"
        ordering = ["tier", "feature"]
        unique_together = [["tier", "feature"]]
        indexes = [
            models.Index(fields=["tier", "is_enabled"]),
            models.Index(fields=["feature"]),
        ]
        verbose_name = "Tier Feature"
        verbose_name_plural = "Tier Features"

    def __str__(self):
        status = "enabled" if self.is_enabled else "disabled"
        return f"{self.feature.name} ({status}) on {self.tier.name}"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tier_id": str(self.tier_id),
            "feature_id": str(self.feature_id),
            "feature_code": self.feature.code if self.feature else None,
            "feature_name": self.feature.name if self.feature else None,
            "is_enabled": self.is_enabled,
            "settings_override": self.settings_override,
            "quota_limit": self.quota_limit,
            "quota_policy": self.quota_policy,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FeatureProvider(models.Model):
    """Service provider for a feature.

    Defines available providers for each feature category.
    Used in feature settings modals for provider selection.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    feature = models.ForeignKey(SaasFeature, on_delete=models.CASCADE, related_name="providers")

    code = models.CharField(
        max_length=50, help_text="Unique provider code (e.g., 'elevenlabs', 'openai_whisper')"
    )

    name = models.CharField(max_length=100, help_text="Display name")

    description = models.TextField(blank=True, help_text="Provider description")

    # Provider configuration
    config_schema = models.JSONField(
        default=dict, blank=True, help_text="JSON Schema for provider-specific configuration"
    )

    default_config = models.JSONField(
        default=dict, blank=True, help_text="Default configuration for this provider"
    )

    # Status
    is_active = models.BooleanField(default=True, db_index=True)

    is_default = models.BooleanField(
        default=False, help_text="Whether this is the default provider for the feature"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saas_feature_providers"
        ordering = ["feature", "-is_default", "name"]
        unique_together = [["feature", "code"]]
        indexes = [
            models.Index(fields=["feature", "is_active"]),
            models.Index(fields=["code"]),
        ]
        verbose_name = "Feature Provider"
        verbose_name_plural = "Feature Providers"

    def __str__(self):
        return f"{self.name} ({self.feature.code})"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "feature_id": str(self.feature_id),
            "feature_code": self.feature.code if self.feature else None,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "config_schema": self.config_schema,
            "default_config": self.default_config,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
