"""Usage Record Model.

VIBE COMPLIANT - Lago billing integration, append-only for audit.
Per SAAS_ADMIN_SRS.md Section 4.7
"""

import uuid

from django.db import models

from admin.saas.models.agents import Agent
from admin.saas.models.tenants import Tenant


class UsageRecord(models.Model):
    """Metered usage data for billing integration.

    Records sent to Lago for usage-based billing.
    Append-only for audit compliance.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="usage_records")

    agent = models.ForeignKey(
        Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="usage_records"
    )

    metric_code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Billable metric code (e.g., 'voice_minutes', 'api_calls')",
    )

    quantity = models.DecimalField(max_digits=20, decimal_places=6, help_text="Usage quantity")

    unit = models.CharField(max_length=20, default="units", help_text="Unit of measurement")

    # Lago Integration
    lago_event_id = models.CharField(
        max_length=100, blank=True, db_index=True, help_text="Lago event transaction ID"
    )

    lago_synced = models.BooleanField(
        default=False, db_index=True, help_text="Whether synced to Lago"
    )

    # Metadata
    metadata = models.JSONField(
        default=dict, blank=True, help_text="Additional context for the usage event"
    )

    # Timestamps
    recorded_at = models.DateTimeField(
        auto_now_add=True, db_index=True, help_text="When usage was recorded"
    )

    period_start = models.DateTimeField(null=True, blank=True, help_text="Start of usage period")

    period_end = models.DateTimeField(null=True, blank=True, help_text="End of usage period")

    class Meta:
        db_table = "usage_records"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["tenant", "metric_code"]),
            models.Index(fields=["tenant", "recorded_at"]),
            models.Index(fields=["lago_synced"]),
            models.Index(fields=["metric_code", "recorded_at"]),
        ]
        verbose_name = "Usage Record"
        verbose_name_plural = "Usage Records"

    def __str__(self):
        return f"{self.metric_code}: {self.quantity} {self.unit}"

    def to_dict(self):
        """Serialize for API response."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "agent_id": str(self.agent_id) if self.agent_id else None,
            "metric_code": self.metric_code,
            "quantity": float(self.quantity),
            "unit": self.unit,
            "lago_event_id": self.lago_event_id,
            "lago_synced": self.lago_synced,
            "metadata": self.metadata,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }
