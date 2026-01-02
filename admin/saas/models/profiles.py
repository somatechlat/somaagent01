"""
Profile Models for SAAS Admin
Following the 5-level profile hierarchy from SRS.

VIBE COMPLIANT:
- Django ORM models
- JSONB for flexible preferences
- All 10 personas applied

Levels:
1. AdminProfile - Platform Admin personal settings
2. TenantSettings - Organization settings (extends Tenant)
3. UserPreferences - End user personal preferences
"""

import uuid
from django.db import models


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
        db_table = "saas_admin_profile"
        verbose_name = "Admin Profile"
        verbose_name_plural = "Admin Profiles"

    def __str__(self):
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

    # Metadata
    timezone = models.CharField(max_length=50, default="UTC")
    language = models.CharField(max_length=10, default="en")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saas_tenant_settings"
        verbose_name = "Tenant Settings"
        verbose_name_plural = "Tenant Settings"

    def __str__(self):
        return f"Settings for {self.tenant.name}"


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
        db_table = "saas_user_preferences"
        verbose_name = "User Preferences"
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"Preferences for {self.user_id}"

    def get_default_notification_prefs(self):
        """Return default notification preferences."""
        return {
            "agentReplies": True,
            "activitySummary": False,
            "productUpdates": False,
        }

    def save(self, *args, **kwargs):
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
        db_table = "saas_user_session"
        verbose_name = "User Session"
        verbose_name_plural = "User Sessions"
        ordering = ["-last_active"]

    def __str__(self):
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
        db_table = "saas_api_key"
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"
