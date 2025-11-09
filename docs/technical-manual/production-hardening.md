# Production Hardening Plan (Phase: Pre-K8s → K8s → Terraform)

## Objectives
- Establish consistent health/readiness/liveness endpoints across services.
- Guarantee graceful shutdown and background task cancellation (no orphaned tasks, clean closing of Kafka & HTTP clients).
- Standardize observability: metrics, structured logs, OpenTelemetry traces, Kafka trace headers (traceparent) for cross-service correlation.
- Harden configuration & secrets management for container and cluster deployment.
- Provide Kubernetes deployment primitives (Helm charts scaffold) with probes, resource requests/limits, security context, and topology hints.
- Prepare Terraform baseline for cloud infra (Kafka, Postgres, Redis, object storage buckets, secret stores) and CI integration hooks.

## Scope
Services: `gateway`, `delegation_gateway`, `delegation_worker`, `conversation_worker`, `tool_executor`, `memory_sync`, `memory_replicator`, `outbox_sync`, `celery_worker` (+ any future `memory_service`).

## Readiness & Liveness Standardization
Checklist per HTTP service:
- Endpoint: `GET /live` returns `{status: "alive"}` (fast path, no external deps).
- Endpoint: `GET /ready` probes critical dependencies (DB schema ensure, Kafka metadata fetch, cache ping). Failure ⇒ HTTP 503.
- Endpoint: `GET /health` retains richer component detail (already present in `gateway`).
- Worker processes (non-HTTP): Provide a lightweight HTTP sidecar or expose periodic heartbeat metric (e.g., `worker_last_heartbeat_timestamp`).

Action Items:
1. Add `/ready` + `/live` to any remaining HTTP apps (verify `conversation_worker` if it exposes HTTP; else document alternative).
2. Introduce a shared readiness helper in `services/common/readiness.py` (probe functions: postgres, kafka, redis, optional external) to remove duplication.
3. Document readiness contract in OpenAPI and Helm values.

## Graceful Shutdown
Current state: lifecycle helper integrated for several workers; gateway tracks tasks and cancels on lifespan shutdown.
Required:
- Ensure each service closes: Kafka producer/consumer, HTTP clients, async DB pools, background tasks (janitors, exporters, listeners).
- Add signal handlers (SIGINT/SIGTERM) via shared helper across workers (`service_lifecycle.py`).
- Emit shutdown trace span and log marker for correlation.

Action Items:
1. Audit each worker for running tasks without cancellation tokens; wrap in stop Event.
2. Gateway: add termination timeout enforcement (e.g., 20s) before forced exit.
3. Add unit test simulating cancellation for one worker (mock bus + dummy loop). (Low priority if environment constraints.)

## Observability Enhancements
Completed: trace headers (`trace_id`, `span_id`, `traceparent`) and payload injection.
Next:
- Add metrics: startup duration (`service_startup_seconds`), last successful readiness timestamp, graceful shutdown duration.
- Structured logging: ensure `trace_id` and `span_id` included in all top-level log records (logging filter).
- Add `ServiceMonitor` annotations example in Helm chart for Prometheus scraping.

## Configuration & Secrets
Currently: environment variables + direct secret fetch helper (`vault_secrets`).
Target:
- Central config registry abstraction with layered precedence: default → environment → remote dynamic overrides (Kafka topic `config_updates`).
- Schema validation for config documents (JSONSchema versioned).
- Staged rollout: publish new config version, consumer validates & acknowledges; revert on failure.
- Secrets: reference by key (e.g., `${secret:openai}`) resolved at runtime through secret provider interface; no raw secrets in config files.

Action Items:
1. Draft `services/common/config_registry.py` (load, validate, subscribe, ack model).
2. Add `schemas/config/registry.v1.schema.json` for structural validation.
3. Extend existing `_config_update_listener` to send ack events / metrics.

## Kubernetes (Helm) Scaffold
Chart Structure (proposed):
```
helm/
  Chart.yaml
  values.yaml
  templates/
    deployment-gateway.yaml
    deployment-delegation-gateway.yaml
    deployment-workers.yaml
    service.yaml
    configmap-env.yaml
    secret-env.yaml
    ingress.yaml
    servicemonitor.yaml (optional)
```
Key Values:
- `image.repository`, `image.tag`.
- `resources.{requests,limits}` per component.
- `autoscaling.enabled`, HPA metrics (CPU/memory, custom latency metric optional).
- `env`: list of key/value, plus secretRefs.
- `readinessProbe` and `livenessProbe` hitting `/ready` & `/live`.
- `podSecurityContext` (runAsNonRoot, fsGroup). `securityContext` (drop capabilities, readOnlyRootFilesystem).
- `topologySpreadConstraints` for HA.

Action Items:
1. Scaffold chart and minimal templates referencing readiness endpoints.
2. Add `NOTIFICATIONS_JANITOR_ENABLED=false` override capability via values.
3. Document example `values-production.yaml` with tightened resource limits.

## Terraform Baseline
Components:
- VPC / networking (if not managed separately).
- Postgres (managed service) + Redis (Elasticache/Valkey) + Kafka (MSK / Redpanda / Aiven) + Object storage bucket.
- Secret store (AWS Secrets Manager / Vault integration).
- IAM roles (pod service accounts) & security groups for DB/Kafka.

Action Items:
1. Define module layout `infra/terraform/` with environments: `dev`, `prod`.
2. Add remote state (`backend.tf`) pattern placeholder.
3. Variables for sizing, engine versions, retention, encryption.
4. Output endpoints and ARNs consumed by Helm chart values (CI pipeline artifact).

## Reliability & Backpressure
- Implement circuit breakers (already using `pybreaker`) consistently for all outbound calls (LLM, SomaBrain, config fetch).
- Add retry with jitter for publishing when Kafka temporarily unavailable (in DurablePublisher fallback path already present). Confirm exponential backoff.
- Memory pipeline: add WAL lag metric, compaction job schedule via cron-like worker.

Action Items:
1. Add `memory_wal_lag_seconds` metric (difference between now and last WAL timestamp).
2. Add background compaction placeholder in `memory_replicator` (feature-flagged).

## Security Posture (Preview)
Will be detailed in separate security review document; key early tasks:
- Ensure no secrets logged; add log filter to redact known patterns.
- Validate JWT algorithms enforced (already fail-fast for missing PyJWT).
- Policy enforcement metrics (exists) – add decision latency histogram.

## Developer Mode Parity
- Provide `docker-compose.dev.yaml` layering optional services & mock dependencies.
- Seed scripts for model profiles, tool catalog entries, test tenants.
- Enable watch mode (reload) for FastAPI services.

## Metrics Backlog Summary
| Metric | Type | Purpose |
|--------|------|---------|
| service_startup_seconds | Histogram | Measure startup initialization cost |
| service_shutdown_seconds | Histogram | Ensure graceful shutdown bounded |
| readiness_last_success_timestamp | Gauge | Track last successful readiness probe |
| memory_wal_lag_seconds | Gauge | Monitor replication freshness |
| config_update_apply_total | Counter (labels: result) | Track config rollout success/failure |
| policy_decision_latency_seconds | Histogram | Observe authorization performance |

## Prioritized Next Steps (Execution Queue)
1. Shared readiness helper & apply to all HTTP services.
2. Config registry scaffold + schema + ack metrics.
3. Helm chart initial commit with gateway + delegation + one worker (conversation_worker) deployments.
4. Startup/shutdown metrics instrumentation.
5. memory WAL lag metric + compaction placeholder.
6. Policy decision latency histogram.
7. Terraform directory scaffold + variable definitions.
8. Developer mode compose profile enhancements.

## Risk & Mitigations
| Risk | Mitigation |
|------|------------|
| Inconsistent readiness logic | Central helper + tests |
| Secret leakage in logs | Redaction filter + scanning CI job |
| Trace correlation gaps | Mandatory headers (implemented) + docs |
| Unbounded shutdown | Timeout + structured shutdown spans |
| Config drift across envs | Registry with versioned schema + ack metrics |

## Acceptance Criteria (Phase Completion)
- All HTTP services respond to `/ready` and `/live` within <200ms when healthy.
- Helm chart deploys gateway & delegation services with passing probes.
- Traceparent visible in Kafka messages and spans link across publish/consume.
- Config registry publishes and validates a sample update end-to-end.
- Startup and shutdown metrics exposed and observable in Prometheus scrape.
- Terraform scaffold defines core infra modules and variables (no full apply required yet).
- Security review doc placeholder created referencing redaction and policy latency goals.

---
Version: 0.1.0
Last Updated: (auto-fill in future CI step)
