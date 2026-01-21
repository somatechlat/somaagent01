"""Shared Prometheus metrics for chat service modules.

Single source of truth for metrics to avoid duplicate registration errors.
"""

from prometheus_client import Counter, Histogram

# Request counter — single registration
CHAT_REQUESTS = Counter(
    "chat_service_requests_total",
    "Total ChatService requests",
    ["method", "result"],
)

# Latency histogram — single registration
CHAT_LATENCY = Histogram(
    "chat_service_duration_seconds",
    "ChatService request latency",
    ["method"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Token counter — single registration
CHAT_TOKENS = Counter(
    "chat_tokens_total",
    "Total tokens processed",
    ["direction"],
)

__all__ = ["CHAT_REQUESTS", "CHAT_LATENCY", "CHAT_TOKENS"]
