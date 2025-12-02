"""
Observability module for SomaAgent01 with FastA2A integration.
Provides comprehensive metrics and monitoring capabilities.
"""

from .metrics import (
    # FastA2A Metrics
    fast_a2a_requests_total,
    fast_a2a_latency_seconds,
    fast_a2a_errors_total,
    # Event Publisher Metrics
    event_published_total,
    event_publish_latency_seconds,
    event_publish_errors_total,
    # Context Builder Metrics
    tokens_received_total,
    tokens_before_budget_gauge,
    tokens_after_budget_gauge,
    tokens_after_redaction_gauge,
    thinking_tokenisation_seconds,
    thinking_policy_seconds,
    thinking_retrieval_seconds,
    thinking_salience_seconds,
    thinking_ranking_seconds,
    thinking_redaction_seconds,
    thinking_prompt_seconds,
    thinking_total_seconds,
    # SomaBrain Metrics
    somabrain_requests_total,
    somabrain_latency_seconds,
    somabrain_errors_total,
    somabrain_memory_operations_total,
    # System Metrics
    system_health_gauge,
    system_uptime_seconds,
    system_active_connections_gauge,
)

__all__ = [
    # FastA2A Metrics
    "fast_a2a_requests_total",
    "fast_a2a_latency_seconds",
    "fast_a2a_errors_total",
    # Event Publisher Metrics
    "event_published_total",
    "event_publish_latency_seconds",
    "event_publish_errors_total",
    # Context Builder Metrics
    "tokens_received_total",
    "tokens_before_budget_gauge",
    "tokens_after_budget_gauge",
    "tokens_after_redaction_gauge",
    "thinking_tokenisation_seconds",
    "thinking_policy_seconds",
    "thinking_retrieval_seconds",
    "thinking_salience_seconds",
    "thinking_ranking_seconds",
    "thinking_redaction_seconds",
    "thinking_prompt_seconds",
    "thinking_total_seconds",
    # SomaBrain Metrics
    "somabrain_requests_total",
    "somabrain_latency_seconds",
    "somabrain_errors_total",
    "somabrain_memory_operations_total",
    # System Metrics
    "system_health_gauge",
    "system_uptime_seconds",
    "system_active_connections_gauge",
]
