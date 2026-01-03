"""Prometheus metrics for tool executor service."""

import logging

from prometheus_client import Counter, Gauge, Histogram, start_http_server

import os

LOGGER = logging.getLogger(__name__)

TOOL_REQUEST_COUNTER = Counter(
    "tool_executor_requests_total",
    "Total tool execution requests processed",
    labelnames=("tool", "outcome"),
)
TOOL_FEEDBACK_TOTAL = Counter(
    "tool_executor_feedback_total",
    "Tool feedback delivery outcomes",
    labelnames=("status",),
)
POLICY_DECISIONS = Counter(
    "tool_executor_policy_decisions_total",
    "Policy evaluation outcomes for tool executions",
    labelnames=("tool", "decision"),
)
TOOL_EXECUTION_LATENCY = Histogram(
    "tool_executor_execution_seconds",
    "Execution latency by tool",
    labelnames=("tool",),
)
TOOL_INFLIGHT = Gauge(
    "tool_executor_inflight",
    "Current number of in-flight tool executions",
    labelnames=("tool",),
)
REQUEUE_EVENTS = Counter(
    "tool_executor_requeue_total",
    "Requeue events emitted by the tool executor",
    labelnames=("tool", "reason"),
)

_METRICS_SERVER_STARTED = False


def ensure_metrics_server(settings: object) -> None:
    """Start Prometheus metrics HTTP server if not already running."""
    global _METRICS_SERVER_STARTED
    if _METRICS_SERVER_STARTED:
        return

    default_port = int(os.environ.service.metrics_port)
    default_host = str(os.environ.service.metrics_host)

    port = int(os.environ.get("TOOL_EXECUTOR_METRICS_PORT", str(default_port)))
    if port <= 0:
        LOGGER.warning("Tool executor metrics disabled", extra={"port": port})
        _METRICS_SERVER_STARTED = True
        return

    host = os.environ.get("TOOL_EXECUTOR_METRICS_HOST", default_host)
    start_http_server(port, addr=host)
    LOGGER.info("Tool executor metrics server started", extra={"host": host, "port": port})
    _METRICS_SERVER_STARTED = True
