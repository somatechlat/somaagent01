# SomaAgent 01 Architecture Blueprint (Initial Version)

> Status: Draft v0.1 – generated from codebase scan (Nov 9 2025). Will iterate as cross‑cutting concern assessment progresses.

## 1. High‑Level Layering

1. Edge & API Layer
   - `gateway`: Public FastAPI service (HTTP+WebSocket/SSE), auth, rate limiting, policy enforcement, uploads, notifications, LLM invoke streaming proxy, speech endpoints.
   - `delegation_gateway`: Narrow FastAPI surface for asynchronous delegation task submission & status.
2. Worker & Orchestration Layer
   - `conversation_worker`: Consumes `conversation.inbound`, produces `conversation.outbound`; policy filtering, background recall, orchestration of tool calls via Gateway streaming or non-stream fallback.
   - `tool_executor`: Consumes `tool.requests`, produces `tool.results` + UI facing tool lifecycle events; sandboxed execution, resource management, auditing.
   - `delegation_worker`: Consumes delegation tasks, persists them for downstream processing.
   - `memory_sync`: Retries failed memory writes from Postgres outbox → publishes `memory.wal` upon success.
   - `memory_replicator`: Consumes `memory.wal` → persists replica rows → publishes DLQ on failure.
   - `outbox_sync`: Publishes generic durable outbox rows to Kafka (backpressure aware; health adaptive).
3. Core Domain / Data Layer
   - External SomaBrain memory/LLM backend (HTTP) integrated via Gateway & workers.
   - Policy (OPA) & optional OpenFGA (authorization + deny by fail‑closed design).
   - Postgres stores: sessions, memory write outbox, memory replica, notifications, attachments, tool catalog, model profiles, audit, delegation, export jobs, DLQ.
   - Redis: session cache, budget manager, rate limiting buckets, requeue store, Celery broker/result (where Celery used).
   - Kafka: durable event bus topics (see §2).
4. Cross‑Cutting Subsystems
   - Observability: per‑service Prometheus exporter, rich metric families (latency, counts, gauges, backlog, DLQ depth, tool execution, replication lag).
   - Tracing: OTLP instrumentation (FastAPI + httpx + manual spans).
   - Policy Enforcement: Gateway middleware (OPA), worker policy client checks for `conversation.send`, `memory.write`, `tool.execute`.
   - Durable Publishing & Outbox: `DurablePublisher` + Postgres outbox with `outbox_sync` & memory write outbox with `memory_sync`.
   - DLQ Pattern: Kafka DLQ topic + Postgres DLQ store (replicator).
   - Idempotency: `generate_for_memory_payload` used across memory writes/tool result capture.
   - Settings: `SA01Settings` (env), UI settings document (`UiSettingsStore`), runtime overlays used for uploads, AV, speech, etc.
   - Telemetry: structured tool/memory metrics publisher + TelemetryStore for historical analysis.
   - Security & Content Hygiene: API key store, JWT cookie decoding, masking / sensitive key scrubbing, optional ClamAV scanning, rate limiting middleware, sandboxed tool execution.
   - Tool Runtime: `ToolRegistry` + `ExecutionEngine` + `SandboxManager` + `ResourceManager` for deterministic bounded execution.

## 2. Event & Topic Topology

| Topic | Producers | Consumers | Purpose |
|-------|-----------|-----------|---------|
| `conversation.inbound` | Gateway (user messages) | conversation_worker | User -> LLM orchestration path |
| `conversation.outbound` | conversation_worker, tool_executor (UI tool events), memory recall updates | Gateway SSE (stream to clients) | Downstream chat / context events |
| `tool.requests` | conversation_worker (tool orchestration), manual system events | tool_executor | Execute tool functions |
| `tool.results` | tool_executor | Gateway SSE / conversation_worker (poll via session store) | Return tool outcomes |
| `memory.wal` | memory_sync (after successful remember), conversation_worker (direct writes), tool_executor (tool result capture), attachment ingest flows | memory_replicator | Persist memory replica & provide replication metrics |
| `memory.wal.dlq` | memory_replicator (on failure) | ops consumers / DLQ inspection | Failure isolation |
| `config_updates` | (future) config service or admin ops | Gateway (_config_update_listener) | Hot reload runtime settings |
| `ui.notifications` | notifications API endpoints | Gateway SSE clients | UI notification propagation |
| `somastack.delegation` | delegation_gateway | delegation_worker | Asynchronous task distribution |

(Additional internal topics may appear in future revisions – maintain a versioned schema registry proposal.)

## 3. Principal Data Flows

A. User Message → Assistant Reply
1. Client -> Gateway `/v1/conversation/...` (HTTP) → validates, publishes `conversation.inbound`.
2. `conversation_worker` consumes event, applies policy, persists session event.
3. Worker streams LLM via Gateway internal invoke endpoint; emits `assistant.stream` events to `conversation.outbound`.
4. Tool orchestration: worker detects tool calls, publishes `tool.requests`; awaits `tool.results` (polling session store) → reinvokes LLM if needed.
5. Gateway SSE endpoint streams `conversation.outbound` events back to client.

B. Tool Execution & Memory Capture
1. `tool_executor` consumes `tool.requests` → policy check → sandboxed execution.
2. Publishes result to `tool.results` and UI stream (`conversation.outbound` tool lifecycle events).
3. Captures successful tool result into SomaBrain memory (policy gated) → publishes `memory.wal`.
4. `memory_replicator` persists replica row; replication metrics updated.

C. Memory Write Reliability
1. Direct writes (conversation_worker / tool_executor) may fail → enqueue into Postgres memory write outbox.
2. `memory_sync` retries outbox items with exponential backoff; upon success publishes `memory.wal`.
3. Replicator persists; DLQ used for irrecoverable events.

D. Configuration Hot Reload
1. (Future) Config admin updates produce `config_updates` events.
2. Gateway listener applies validated settings overlay (via `set_settings`).

E. Notifications
1. Notification CRUD endpoints persist rows & emit Kafka `ui.notifications` events.
2. Gateway SSE merges notifications into live client stream.

## 4. Cross‑Cutting Concerns (Current State)

- Observability: Each service starts its own metrics HTTP server; duplication risk for port collisions handled with fallback strategies (e.g. tool_executor increments port). Consider central sidecar pattern or single pushgateway in K8s.
- Tracing: OTLP endpoint configurable; httpx & FastAPI automatically instrumented. Need unified trace IDs across Kafka hops (inject/extract in message headers missing currently).
- Policy: Fail‑closed pattern ensures memory writes/tool executions blocked on OPA outage; health fallback for conversation messages returns explicit denial message.
- Reliability Patterns: Outbox, DLQ, exponential backoff, health-adjusted batch sizing (`outbox_sync`). Add circuit breakers around external SomaBrain calls on gateway.
- Security: JWT cookie parsing with multiple alg support; API key store, rate limiting, sandboxed tools. Need mTLS / ingress controller integration plan for production.
- Settings & Overlays: Central SA01Settings + dynamic UI document overlays. Missing versioned rollout & staged environment layering.
- Data Privacy: Masking logic in settings diff & audit diff; SENSITIVE_KEYS scrubbing. Need encryption at rest for secrets & tool credentials (Vault / KMS integration).

## 5. Production Hardening Recommendations (Preview)

| Area | Gap | Recommendation |
|------|-----|---------------|
| Deployment Health | Mixed health endpoints | Standardize `/health` & `/ready` + readiness gating on dependencies |
| Graceful Shutdown | Few explicit close hooks | Implement cancellation signals & drain Kafka consumers before exit |
| Backpressure | Manual sleep loops | Introduce consumer lag gauges + dynamic batch sizing (already for outbox) across all workers |
| Schema Governance | Inline JSONSchema only | External schema registry (e.g. Git + CI validation or Redpanda/Confluent) |
| Secrets | Env vars only | Vault/Kubernetes Secrets integration + rotation policy |
| Tracing | Missing Kafka span propagation | Add message headers for trace context; wrap publish/consume with span linking |
| Resource Isolation | Tool sandbox local only | Containerized / VM sandbox option, CPU/mem quotas enforced by cgroups in K8s |
| Configuration | Ad‑hoc overlays | Central config service (CRD or GitOps) + versioned update pipeline |
| Multi‑Tenancy | Tenant IDs present | Formal tenant isolation layers (namespaces, quotas) & FGA model expansion |
| Memory Storage | External SomaBrain dependency | Introduce circuit breaker + bulkhead isolation; evaluate fallback local cache |
| Rate Limiting | Per-IP fixed window | Token bucket / sliding window; incorporate tenant + API key dimensions |

## 6. Kubernetes Mapping (Outline)

| Service | K8s Kind | Notes |
|---------|----------|-------|
| gateway | Deployment + Service (ClusterIP) | HTTP ingress (Ingress/Nginx/Envoy); config & secret mounted; HPA by CPU/RPS |
| conversation_worker | Deployment | Consumer group scaling; PodDisruptionBudget |
| tool_executor | Deployment | Needs ephemeral scratch volume for sandbox; securityContext tightened |
| memory_sync | Deployment | Lower replica count; backoff tuning via env ConfigMap |
| memory_replicator | Deployment | Single replica or partitioned; WAL lag metric exported |
| outbox_sync | Deployment | Could merge with memory_sync for simplicity (arg) |
| delegation_gateway | Deployment + Service | Separate ingress path; optional merging into gateway if traffic low |
| delegation_worker | Deployment | Lightweight consumer |
| OPA | Deployment + Service | Sidecar or central; policy bundles via ConfigMap |
| Redis / Postgres / Kafka | Managed / StatefulSets | Evaluate cloud managed vs self-hosted; backup & retention policies |
| Prometheus/Grafana | Helm chart | Scrape all metrics ports; service monitors |

Config via ConfigMaps (non-sensitive) & Secrets (JWT keys, API keys, provider credentials). Use `Deployment` annotations for config checksum to trigger rolling restarts.

## 7. Terraform Baseline Components

- Network: VPC, subnets, SG rules for Kafka/Postgres/Redis/OPA.
- Data: Managed Postgres (point-in-time restore), Redis (cache tier), Kafka cluster (MSK / Redpanda).
- Observability: Managed Prometheus (AMP) + Grafana (AG), OTLP collector (OpenTelemetry).
- Security: Secrets Manager / Vault, KMS CMKs for envelope encryption; IAM roles per service pod.
- CI/CD: Artifact registry (Docker), Terraform state backend (S3 + DynamoDB lock), IAM least-privilege.

## 8. Schema & Interface Governance Roadmap (Next Iteration)

- Adopt versioned JSONSchema files per event type (`schemas/events/<name>.v1.json`).
- Pre‑commit validation & CI check for breaking changes (semantic diff tool).
- Introduce compatibility matrix document enumerating allowed evolution rules (additive only until major bump).

## 9. Future Centralization Targets

1. Unified Config Service: gRPC/HTTP publishing config versions → produces `config_updates` + maintains audit log.
2. Message Envelope Standard: Add headers {trace_id, span_id, tenant_id, schema_version} for every Kafka message.
3. Telemetry Correlation: Link tool execution → memory write → user response chain via shared trace.
4. Vector Store Abstraction: Pluggable embedding/memory backend interface (SomaBrain default; add alternatives).
5. Unified Policy Layer: Consolidate OPA/FGA decisions into a single composite engine with caching & metrics.

## 10. Immediate Action Backlog (Derivable from Blueprint)

- Implement Kafka trace header propagation.
- Standardize health readiness endpoints across services.
- Add graceful shutdown (SIGTERM handlers) draining consumers & closing httpx clients.
- Introduce schema registry folder + CI validator.
- Build config service MVP (emit `config_updates`).
- Harden tool sandbox (resource caps + timeouts central policy).
- Add encryption (at rest) strategy doc & Vault integration scaffold.
- Expand rate limiting to tenant/API key dimension.
- Create K8s Helm chart prototypes per service with values schema.

---
_This blueprint will evolve; subsequent versions will add diagrams, explicit sequence charts, and performance SLO definitions._
