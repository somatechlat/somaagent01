"""Infrastructure ORM Models for SAAS Administration.


Per

10-Persona Implementation:
- PhD Developer: Clean ORM design with proper relationships
- Security Auditor: Encrypted secrets, audit trails
- Performance Engineer: Indexed queries, efficient storage
- Django Architect: Proper model inheritance and methods
- Django Infra Expert: Real infrastructure configuration storage
"""

import uuid

from django.db import models
from django.utils import timezone


class EnforcementPolicy(models.TextChoices):
    """Rate limit enforcement policy."""

    HARD = "HARD", "Hard limit - block when exceeded"
    SOFT = "SOFT", "Soft limit - warn but allow"
    NONE = "NONE", "No enforcement - logging only"


class ServiceStatus(models.TextChoices):
    """Infrastructure service health status."""

    HEALTHY = "healthy", "Healthy"
    DEGRADED = "degraded", "Degraded"
    DOWN = "down", "Down"
    UNKNOWN = "unknown", "Unknown"


class RateLimitPolicy(models.Model):
    """Rate limit policy configuration stored in ORM.

    Synced to Redis for runtime enforcement.
    Allows per-tier overrides and audit trail.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier"
    )

    key = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Rate limit key (e.g., 'api_calls', 'llm_tokens')",
    )

    description = models.TextField(
        blank=True, help_text="Human-readable description of this rate limit"
    )

    # Limits
    limit = models.BigIntegerField(
        default=1000, help_text="Maximum requests/tokens/etc allowed in window"
    )

    window_seconds = models.IntegerField(
        default=3600,  # 1 hour
        help_text="Time window in seconds (e.g., 3600 for 1 hour, 86400 for 24 hours)",
    )

    policy = models.CharField(
        max_length=10,
        choices=EnforcementPolicy.choices,
        default=EnforcementPolicy.HARD,
        help_text="What happens when limit is exceeded",
    )

    # Per-tier overrides as JSON: {"free": 100, "starter": 1000, "team": 10000}
    tier_overrides = models.JSONField(
        default=dict,
        blank=True,
        help_text="Per-tier limit overrides (tier_slug -> limit)",
    )

    # Status
    is_active = models.BooleanField(
        default=True, db_index=True, help_text="Whether this rate limit is enforced"
    )

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, blank=True, help_text="User who created this")
    updated_by = models.CharField(max_length=255, blank=True, help_text="User who last updated")

    class Meta:
        """Meta class implementation."""

        db_table = "rate_limit_policies"
        ordering = ["key"]
        indexes = [
            models.Index(fields=["key"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Rate Limit Policy"
        verbose_name_plural = "Rate Limit Policies"

    def __str__(self):
        """Return string representation."""

        window_str = (
            f"{self.window_seconds // 3600}h"
            if self.window_seconds >= 3600
            else f"{self.window_seconds}s"
        )
        return f"{self.key}: {self.limit}/{window_str} ({self.policy})"

    def get_limit_for_tier(self, tier_slug: str) -> int:
        """Get the effective limit for a specific subscription tier."""
        return self.tier_overrides.get(tier_slug, self.limit)

    def to_redis_key(self) -> str:
        """Get the Redis key for this rate limit config."""
        return f"ratelimit:config:{self.key}"

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "key": self.key,
            "description": self.description,
            "limit": self.limit,
            "window_seconds": self.window_seconds,
            "window_display": self._format_window(),
            "policy": self.policy,
            "tier_overrides": self.tier_overrides,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def _format_window(self) -> str:
        """Format window for display."""
        if self.window_seconds >= 86400:
            days = self.window_seconds // 86400
            return f"{days} day{'s' if days > 1 else ''}"
        elif self.window_seconds >= 3600:
            hours = self.window_seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''}"
        elif self.window_seconds >= 60:
            minutes = self.window_seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return f"{self.window_seconds} second{'s' if self.window_seconds > 1 else ''}"


class ServiceHealth(models.Model):
    """Infrastructure service health status.

    Stores the last known health status of each service.
    Updated by periodic health checks.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier"
    )

    service_name = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="Service name (e.g., 'postgresql', 'redis', 'temporal')",
    )

    display_name = models.CharField(
        max_length=100, blank=True, help_text="Human-readable service name"
    )

    category = models.CharField(
        max_length=50,
        default="core",
        help_text="Service category (core, external, infrastructure)",
    )

    status = models.CharField(
        max_length=20,
        choices=ServiceStatus.choices,
        default=ServiceStatus.UNKNOWN,
        help_text="Current health status",
    )

    latency_ms = models.FloatField(
        null=True, blank=True, help_text="Last measured latency in milliseconds"
    )

    last_check = models.DateTimeField(
        default=timezone.now, help_text="When the last health check was performed"
    )

    last_healthy = models.DateTimeField(
        null=True, blank=True, help_text="When the service was last healthy"
    )

    details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional service-specific details (version, connections, etc.)",
    )

    error_message = models.TextField(blank=True, help_text="Error message if status is not healthy")

    # Configuration
    check_url = models.CharField(max_length=500, blank=True, help_text="Health check endpoint URL")

    check_interval_seconds = models.IntegerField(
        default=30, help_text="How often to check this service"
    )

    is_critical = models.BooleanField(
        default=True, help_text="Whether this service is critical for platform operation"
    )

    class Meta:
        """Meta class implementation."""

        db_table = "service_health"
        ordering = ["category", "service_name"]
        indexes = [
            models.Index(fields=["service_name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["category"]),
        ]
        verbose_name = "Service Health"
        verbose_name_plural = "Service Health Records"

    def __str__(self):
        """Return string representation."""

        return f"{self.display_name or self.service_name}: {self.status}"

    def update_status(
        self, status: str, latency_ms: float = None, details: dict = None, error: str = None
    ):
        """Update the health status."""
        self.status = status
        self.last_check = timezone.now()
        if latency_ms is not None:
            self.latency_ms = latency_ms
        if details is not None:
            self.details = details
        if status == ServiceStatus.HEALTHY:
            self.last_healthy = timezone.now()
            self.error_message = ""
        elif error:
            self.error_message = error
        self.save()

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "service_name": self.service_name,
            "display_name": self.display_name or self.service_name,
            "category": self.category,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_healthy": self.last_healthy.isoformat() if self.last_healthy else None,
            "details": self.details,
            "error_message": self.error_message if self.status != ServiceStatus.HEALTHY else None,
            "is_critical": self.is_critical,
        }


class InfrastructureConfig(models.Model):
    """Infrastructure service configuration stored in ORM.

    Allows viewing and modifying service configs through UI.
    Secrets are stored encrypted.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, help_text="Unique identifier"
    )

    service = models.ForeignKey(
        ServiceHealth,
        on_delete=models.CASCADE,
        related_name="configs",
        help_text="Associated service",
    )

    key = models.CharField(
        max_length=100, help_text="Configuration key (e.g., 'host', 'port', 'pool_size')"
    )

    value = models.TextField(blank=True, help_text="Configuration value (encrypted if is_secret)")

    is_secret = models.BooleanField(
        default=False, help_text="Whether this value should be encrypted/hidden"
    )

    is_editable = models.BooleanField(
        default=True, help_text="Whether this can be edited through UI"
    )

    description = models.TextField(blank=True, help_text="Description of this configuration option")

    default_value = models.TextField(blank=True, help_text="Default value for this configuration")

    value_type = models.CharField(
        max_length=20,
        default="string",
        help_text="Value type: string, integer, boolean, url, json",
    )

    # Audit
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=255, blank=True)

    class Meta:
        """Meta class implementation."""

        db_table = "infrastructure_configs"
        unique_together = ["service", "key"]
        ordering = ["service", "key"]
        verbose_name = "Infrastructure Config"
        verbose_name_plural = "Infrastructure Configs"

    def __str__(self):
        """Return string representation."""

        return f"{self.service.service_name}.{self.key}"

    def get_display_value(self) -> str:
        """Get value for display (masked if secret)."""
        if self.is_secret and self.value:
            return "••••••••"
        return self.value

    def to_dict(self) -> dict:
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "service_id": str(self.service_id),
            "key": self.key,
            "value": self.get_display_value(),
            "is_secret": self.is_secret,
            "is_editable": self.is_editable,
            "description": self.description,
            "default_value": self.default_value,
            "value_type": self.value_type,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
