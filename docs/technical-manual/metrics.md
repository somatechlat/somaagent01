# Metrics and Observability

This document describes the metrics and observability mechanisms used in the Agent Zero application.

## Prometheus Metrics

The Agent Zero application uses the `prometheus_client` library to expose a variety of metrics for monitoring and observability. These metrics are defined in the `python/observability/metrics.py` module.

### Key Metrics

The following are some of the key metrics exposed by the application:

- **`fast_a2a_requests_total`**: The total number of FastA2A requests made.
- **`fast_a2a_latency_seconds`**: The latency of FastA2A requests in seconds.
- **`fast_a2a_errors_total`**: The total number of FastA2A errors encountered.
- **`system_active_connections_gauge`**: The number of active connections.
- **`service_info`**: Information about the service, such as its version and name.
- **`context_tokens_*`**: Gauges for tracking the number of tokens in the context before and after budget trimming and redaction.
- **`thinking_*_seconds`**: Histograms for tracking the duration of various stages of the thinking process.
- **`event_published_total`**: The total number of events published.
- **`somabrain_*`**: Counters, gauges, and histograms for tracking requests, latency, errors, and memory operations related to the SomaBrain.
- **`system_health_gauge`**: A gauge for tracking the health status of various components.
- **`system_uptime_seconds`**: A counter for tracking the uptime of the system.

### Production Metrics

The `ProductionMetrics` class defines a set of advanced metrics for comprehensive monitoring in a production environment. These include metrics for SLA compliance, business operations, resource utilization, and more.

## Metrics Exporter

The `ensure_metrics_exporter()` function starts a standalone Prometheus exporter to expose the metrics. This is an opt-in feature that can be enabled by setting the `CIRCUIT_BREAKER_METRICS_PORT` environment variable.

## SLA Monitoring

The `SLAMonitor` class provides functionality for monitoring and tracking service level agreement (SLA) compliance. It checks metrics such as response time, availability, and error rate against predefined targets.
