"""Flink Sink Tables Migration.


PostgreSQL tables for Flink streaming output.

7-Persona Implementation:
- Django Architect: ORM models for Flink sinks
- DevOps: Table structure for stream processing
- PM: Analytics dashboards data source
"""

from __future__ import annotations

import uuid

from django.db import models

# =============================================================================
# CONVERSATION ANALYTICS (from Flink)
# =============================================================================


class FlinkConversationMetrics(models.Model):
    """Real-time conversation metrics from Flink.

    Tumbling window: 1 minute.
    Source: soma.conversations.events Kafka topic.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    window_start = models.DateTimeField(db_index=True)
    window_end = models.DateTimeField()

    # Aggregated metrics
    total_conversations = models.BigIntegerField(default=0)
    total_messages = models.BigIntegerField(default=0)
    total_tokens = models.BigIntegerField(default=0)
    avg_latency_ms = models.FloatField(default=0.0)
    unique_users = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta class implementation."""

        db_table = "flink_conversation_metrics"
        unique_together = [["tenant_id", "window_start"]]
        indexes = [
            models.Index(fields=["tenant_id", "window_start"]),
            models.Index(fields=["window_start"]),
        ]
        ordering = ["-window_start"]

    def __str__(self):
        """Return string representation."""

        return f"{self.tenant_id} @ {self.window_start}"


# =============================================================================
# USAGE AGGREGATES (from Flink)
# =============================================================================


class FlinkUsageAggregate(models.Model):
    """Hourly usage aggregates from Flink for billing.

    Tumbling window: 1 hour.
    Source: soma.usage.metering Kafka topic.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    resource_type = models.CharField(max_length=50)  # tokens, api_calls, storage
    window_start = models.DateTimeField(db_index=True)

    # Aggregated usage
    total_quantity = models.BigIntegerField(default=0)
    event_count = models.BigIntegerField(default=0)

    # Billing metadata
    unit_price = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    total_cost = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    billed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta class implementation."""

        db_table = "flink_usage_aggregates"
        unique_together = [["tenant_id", "resource_type", "window_start"]]
        indexes = [
            models.Index(fields=["tenant_id", "window_start"]),
            models.Index(fields=["tenant_id", "billed"]),
        ]
        ordering = ["-window_start"]

    def __str__(self):
        """Return string representation."""

        return f"{self.tenant_id}: {self.resource_type} @ {self.window_start}"


# =============================================================================
# ANOMALY ALERTS (from Flink)
# =============================================================================


class FlinkAnomalyAlert(models.Model):
    """Security anomaly alerts from Flink detector.

    Tumbling window: 5 minutes.
    Source: soma.permissions.audit Kafka topic.
    """

    SEVERITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]

    ALERT_TYPES = [
        ("HIGH_DENIAL_RATE", "High Permission Denial Rate"),
        ("BRUTE_FORCE", "Brute Force Attack"),
        ("UNUSUAL_ACTIVITY", "Unusual Activity Pattern"),
        ("DATA_EXFILTRATION", "Potential Data Exfiltration"),
        ("PRIVILEGE_ESCALATION", "Privilege Escalation Attempt"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    user_id = models.CharField(max_length=255, db_index=True)

    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    details = models.TextField()

    detected_at = models.DateTimeField(db_index=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.CharField(max_length=255, blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta class implementation."""

        db_table = "flink_anomaly_alerts"
        indexes = [
            models.Index(fields=["tenant_id", "detected_at"]),
            models.Index(fields=["severity", "acknowledged"]),
            models.Index(fields=["alert_type"]),
        ]
        ordering = ["-detected_at"]

    def __str__(self):
        """Return string representation."""

        return f"{self.severity} {self.alert_type} for {self.user_id}"


# =============================================================================
# AGENT METRICS (from Flink)
# =============================================================================


class FlinkAgentMetrics(models.Model):
    """Real-time agent performance metrics from Flink.

    Tumbling window: 1 minute.
    Source: soma.agents.events Kafka topic.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    agent_id = models.CharField(max_length=255, db_index=True)
    window_start = models.DateTimeField(db_index=True)
    window_end = models.DateTimeField()

    # Performance metrics
    total_requests = models.BigIntegerField(default=0)
    successful_requests = models.BigIntegerField(default=0)
    failed_requests = models.BigIntegerField(default=0)
    avg_response_time_ms = models.FloatField(default=0.0)
    p95_response_time_ms = models.FloatField(default=0.0)
    tokens_consumed = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta class implementation."""

        db_table = "flink_agent_metrics"
        unique_together = [["agent_id", "window_start"]]
        indexes = [
            models.Index(fields=["tenant_id", "window_start"]),
            models.Index(fields=["agent_id", "window_start"]),
        ]
        ordering = ["-window_start"]

    def __str__(self):
        """Return string representation."""

        return f"{self.agent_id} @ {self.window_start}"


# =============================================================================
# SYSTEM METRICS (from Flink)
# =============================================================================


class FlinkSystemMetrics(models.Model):
    """System-wide metrics aggregated by Flink.

    Tumbling window: 1 minute.
    Source: soma.system.metrics Kafka topic.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    window_start = models.DateTimeField(db_index=True)
    window_end = models.DateTimeField()

    # System metrics
    total_api_requests = models.BigIntegerField(default=0)
    total_active_conversations = models.BigIntegerField(default=0)
    total_active_agents = models.BigIntegerField(default=0)
    total_active_users = models.BigIntegerField(default=0)
    avg_api_latency_ms = models.FloatField(default=0.0)
    error_rate = models.FloatField(default=0.0)

    # Resource usage
    total_tokens_consumed = models.BigIntegerField(default=0)
    total_storage_bytes = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta class implementation."""

        db_table = "flink_system_metrics"
        indexes = [
            models.Index(fields=["window_start"]),
        ]
        ordering = ["-window_start"]

    def __str__(self):
        """Return string representation."""

        return f"System @ {self.window_start}"


# =============================================================================
# LLM TOKEN METRICS (from Flink)
# =============================================================================


class FlinkLLMTokenMetrics(models.Model):
    """LLM token usage metrics from Flink.

    Tumbling window: 1 minute.
    Source: soma.llm.tokens Kafka topic.

    PhD Dev: Token tracking for cost optimization.
    PM: Billing and usage dashboards.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)  # gpt-4, claude-3, etc.
    window_start = models.DateTimeField(db_index=True)
    window_end = models.DateTimeField()

    # Token counts
    prompt_tokens = models.BigIntegerField(default=0)
    completion_tokens = models.BigIntegerField(default=0)
    total_tokens = models.BigIntegerField(default=0)

    # Request counts
    request_count = models.BigIntegerField(default=0)
    successful_requests = models.BigIntegerField(default=0)
    failed_requests = models.BigIntegerField(default=0)

    # Latency metrics
    avg_latency_ms = models.FloatField(default=0.0)
    p95_latency_ms = models.FloatField(default=0.0)
    p99_latency_ms = models.FloatField(default=0.0)

    # Cost tracking (calculated based on model pricing)
    estimated_cost_usd = models.DecimalField(max_digits=12, decimal_places=6, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta class implementation."""

        db_table = "flink_llm_token_metrics"
        unique_together = [["tenant_id", "model_name", "window_start"]]
        indexes = [
            models.Index(fields=["tenant_id", "window_start"]),
            models.Index(fields=["model_name", "window_start"]),
            models.Index(fields=["tenant_id", "model_name"]),
        ]
        ordering = ["-window_start"]

    def __str__(self):
        """Return string representation."""

        return f"{self.tenant_id}: {self.model_name} @ {self.window_start}"


# =============================================================================
# LLM MODEL USAGE (from Flink)
# =============================================================================


class FlinkLLMModelUsage(models.Model):
    """Daily LLM model usage aggregation.

    Tumbling window: 1 day.
    Source: soma.llm.completions Kafka topic.

    PM: Model selection and cost analysis.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=255, db_index=True)
    agent_id = models.CharField(max_length=255, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    date = models.DateField(db_index=True)

    # Usage counts
    total_requests = models.BigIntegerField(default=0)
    total_tokens = models.BigIntegerField(default=0)
    prompt_tokens = models.BigIntegerField(default=0)
    completion_tokens = models.BigIntegerField(default=0)

    # Performance
    avg_response_time_ms = models.FloatField(default=0.0)
    error_rate = models.FloatField(default=0.0)

    # Cost
    total_cost_usd = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta class implementation."""

        db_table = "flink_llm_model_usage"
        unique_together = [["tenant_id", "agent_id", "model_name", "date"]]
        indexes = [
            models.Index(fields=["tenant_id", "date"]),
            models.Index(fields=["model_name", "date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        """Return string representation."""

        return f"{self.agent_id}: {self.model_name} on {self.date}"
