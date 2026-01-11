"""
Profile (Settings) Models for SAAS Admin

Implementation of the "Deep Settings Architecture" defined in SRS-SAAS-MASTER-SETTINGS-INDEX.md.
Provides persistent storage for:
1.  Global Defaults (Singleton) - The "Blueprint" for new tenants.
2.  Tenant Settings (OneToOne) - Secure, JSONB-backed configuration for each tenant.
3.  User Preferences - End user personal preferences.

Compliance: VIBE-CORE-004 (Real Implementations Only).
"""

import uuid
from typing import Any, Dict

from django.core.exceptions import ValidationError
from django.db import models

# We avoid importing Tenant here directly if it causes circular imports,
# but models.OneToOneField('saas.Tenant') handles it via string reference.


class GlobalDefault(models.Model):
    """Singleton model storing platform-wide default configurations.

    This model acts as the "Master Blueprint" for:
    - Default Model Catalog (what models are available globally)
    - Default Role Definitions (what permissions roles have)
    - Default quotas and limits

    Pattern: Singleton (ensure_one_instance)
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # JSONB field storing the master catalog
    defaults = models.JSONField(
        default=dict,
        help_text="Canonical default settings (models, roles, quotas)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta options."""

        db_table = "saas_global_defaults"
        verbose_name = "Global Default"
        verbose_name_plural = "Global Defaults"

    def save(self, *args, **kwargs):
        """Enforce Singleton Pattern."""
        if not self.pk and GlobalDefault.objects.exists():
            raise ValidationError("There can be only one GlobalDefault instance")
        super().save(*args, **kwargs)

    @classmethod
    def get_instance(cls) -> "GlobalDefault":
        """Retrieve or create the singleton instance."""
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create(defaults=cls._initial_defaults())
        return obj

    @classmethod
    async def aget_instance(cls) -> "GlobalDefault":
        """Async retrieve or create the singleton instance."""
        obj = await cls.objects.afirst()
        if not obj:
            obj = await cls.objects.acreate(defaults=cls._initial_defaults())
        return obj

    @staticmethod
    def _initial_defaults() -> Dict[str, Any]:
        """Return hardcoded bootstrap defaults to prevent empty system."""
        return {
            "models": [
                {"id": "gpt-4o", "provider": "openai", "enabled": True},
                {"id": "claude-3-5-sonnet", "provider": "anthropic", "enabled": True},
            ],
            "roles": [
                {"id": "admin", "permissions": ["*"]},
                {"id": "member", "permissions": ["read"]},
            ],
            "dev_sandbox_defaults": {
                "max_agents": 2,
                "max_users": 1,
                "enable_code_interpreter": False,
                "enable_filesystem": False,
                "rate_limits_multiplier": 0.5,
            },
            "dev_live_defaults": {
                "max_agents": 10,
                "max_users": 5,
                "enable_code_interpreter": True,
                "enable_filesystem": True,
                "rate_limits_multiplier": 1.0,
            },
        }

    def __str__(self) -> str:
        return "Global SaaS Defaults"


class AdminProfile(models.Model):
    """
    Platform Admin personal settings.
    Linked to Keycloak user ID, stores platform-level preferences.

    Route: /platform/profile
    """

    user_id = models.UUIDField(primary_key=True, help_text="Keycloak user ID")
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100)
    avatar_url = models.URLField(blank=True, default="")
    phone = models.CharField(max_length=20, blank=True, default="")

    # Security
    session_timeout = models.IntegerField(
        default=30, help_text="Session timeout in minutes (5-480)"
    )

    # Notifications
    notification_prefs = models.JSONField(
        default=dict,
        help_text="Notification preferences: criticalAlerts, billingEvents, weeklyDigest, marketing",
    )

    # Audit
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "saas_admin_profile"
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"

    def __str__(self):
        """Return string representation."""

        return f"{self.display_name} ({self.email})"

    def get_default_notification_prefs(self):
        """Return default notification preferences."""
        return {
            "criticalAlerts": True,
            "billingEvents": True,
            "weeklyDigest": False,
            "marketing": False,
        }

    def save(self, *args, **kwargs):
        # Initialize default notification prefs if empty
        """Execute save."""

        if not self.notification_prefs:
            self.notification_prefs = self.get_default_notification_prefs()
        super().save(*args, **kwargs)


class TenantSettings(models.Model):
    """
    Tenant organization settings.
    Extends core Tenant model with branding, security, and feature settings.

    Route: /admin/settings
    """

    MFA_POLICY_CHOICES = [
        ("off", "Off"),
        ("optional", "Optional"),
        ("required", "Required"),
    ]

    tenant = models.OneToOneField(
        "saas.Tenant", on_delete=models.CASCADE, related_name="settings", primary_key=True
    )

    # Branding
    logo_url = models.URLField(blank=True, default="")
    primary_color = models.CharField(max_length=7, default="#2563eb")
    accent_color = models.CharField(max_length=7, default="#3b82f6")
    custom_domain = models.CharField(max_length=255, blank=True, default="")

    # Security
    mfa_policy = models.CharField(max_length=10, choices=MFA_POLICY_CHOICES, default="optional")
    sso_enabled = models.BooleanField(default=False)
    sso_config = models.JSONField(default=dict, help_text="SSO provider configuration")
    session_timeout = models.IntegerField(default=30, help_text="Session timeout in minutes")

    # Features
    feature_overrides = models.JSONField(
        default=dict, help_text="Feature overrides within tier limits"
    )

    # SRS Compliance Extensions (JSONB pillars)
    compliance = models.JSONField(default=dict, blank=True)
    compute = models.JSONField(default=dict, blank=True)
    auth = models.JSONField(default=dict, blank=True)

    # Metadata
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "saas_tenant_settings"
        verbose_name = "Tenant Settings"
        verbose_name_plural = "Tenant Settings"

    def __str__(self):
        """Return string representation."""

        return f"Settings for {self.tenant.name}"

    def merge_defaults(self):
        """Merge global defaults into local settings (Placeholder)."""
        pass


class UserPreferences(models.Model):
    """
    End user personal preferences.
    Theme, language, timezone, and notifications.

    Route: /profile
    """

    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("system", "System"),
    ]

    user_id = models.UUIDField(primary_key=True, help_text="Keycloak user ID")

    # Display
    display_name = models.CharField(max_length=100, blank=True, default="")
    avatar_url = models.URLField(blank=True, default="")
    bio = models.TextField(blank=True, default="")

    # Preferences
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="system")
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=50, default="UTC")
    date_format = models.CharField(max_length=20, default="YYYY-MM-DD")

    # Notifications
    notification_prefs = models.JSONField(
        default=dict,
        help_text="Notification preferences: agentReplies, activitySummary, productUpdates",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Meta class implementation."""

        db_table = "saas_user_preferences"
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"

    def __str__(self):
        """Return string representation."""

        return f"Preferences for {self.user_id}"

    def get_default_notification_prefs(self):
        """Return default notification preferences."""
        return {
            "agentReplies": True,
            "activitySummary": False,
            "productUpdates": False,
        }

    def save(self, *args, **kwargs):
        """Execute save."""

        if not self.notification_prefs:
            self.notification_prefs = self.get_default_notification_prefs()
        super().save(*args, **kwargs)


class UserSession(models.Model):
    """
    Track active user sessions for security.
    Allows admins to view and revoke sessions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = models.UUIDField(db_index=True)

    # Session info
    device = models.CharField(max_length=200)
    browser = models.CharField(max_length=100, blank=True, default="")
    os = models.CharField(max_length=100, blank=True, default="")
    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=100, blank=True, default="")

    # Tokens
    refresh_token_hash = models.CharField(max_length=64, blank=True)

    # Status
    is_current = models.BooleanField(default=False)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        """Meta class implementation."""

        db_table = "saas_user_session"
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ["-last_active"]

    def __str__(self):
        """Return string representation."""

        return f"{self.device} - {self.ip_address}"


class ApiKey(models.Model):
    """
    API keys for platform or tenant access.
    """

    KEY_TYPE_CHOICES = [
        ("platform", "Platform"),
        ("tenant", "Tenant"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    key_type = models.CharField(max_length=10, choices=KEY_TYPE_CHOICES)

    # Owner
    user_id = models.UUIDField(null=True, blank=True, help_text="For platform keys")
    tenant_id = models.UUIDField(null=True, blank=True, help_text="For tenant keys")

    # Key info
    name = models.CharField(max_length=100)
    key_prefix = models.CharField(max_length=8, help_text="First 8 chars of key for display")
    key_hash = models.CharField(max_length=64, help_text="SHA256 hash of full key")

    # Permissions
    scopes = models.JSONField(default=list, help_text="List of permission scopes")

    # Tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        """Meta class implementation."""

        db_table = "saas_api_key"
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""

        return f"{self.name} ({self.key_prefix}...)"
