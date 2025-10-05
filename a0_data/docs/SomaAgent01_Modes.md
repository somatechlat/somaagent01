⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Runtime Modes

## Purpose
SomaAgent 01 must adapt its infrastructure footprint, policy posture, and learning behaviour to the environment in which it runs. This document defines the four canonical runtime modes—`LOCAL`, `DEVELOPMENT`, `TRAINING`, and `PRODUCTION`—and describes the OSS infrastructure, messaging guarantees, and safety rails required for each. Personas remain constant across modes; these settings govern the agent *runtime* or "code mode".

## Mode Matrix

| Mode | Primary Use | Infrastructure Footprint (OSS Only) | Messaging & Offline Guarantees | Policy & Governance | Model Profiles / Learning |
|------|-------------|--------------------------------------|--------------------------------|----------------------|---------------------------|
| **LOCAL** | Solo developer experimentation on a workstation | Docker Compose stack with Kafka, Redis, Postgres, Qdrant, ClickHouse, Whisper (CPU), OPA in permissive mode, consuming the managed Soma SLM API via `SLM_BASE_URL`. Vault disabled; `.env` secrets only. | Kafka retains all events locally; requeue store persisted to local Postgres. Workers may restart without data loss. CLI tools to inspect queues. | Policy engine runs in "warn" mode. Logs every decision but allows fail-open to prevent blocking local work. | Default model profiles favour fast OSS models (Phi-3 Mini, Mistral 7B). Continuous learning enabled but scoped to local storage. |
| **DEVELOPMENT** | Shared non-production cluster for feature work | Kubernetes namespace with full OSS stack (Kafka/KRaft, Redis, Postgres, Qdrant, ClickHouse, Whisper GPU, Vault, OPA/OpenFGA, Prometheus stack) plus secure outbound access to the managed Soma SLM API. GitOps via Argo CD. | Kafka retention ≥7 days; WebSocket/SSE clients auto-reconnect; DLQ pipeline for debugging. Offline states recorded in Postgres and surfaced in dashboards. | Policy engine runs in "observe" mode: warnings generated, decisions logged, optional manual enforcement. Vault-managed test secrets rotated regularly. | Model profiles allow small→large escalation; scoring telemetry recorded. Learning rate moderately constrained; writes go to SomaBrain DEV namespace. |
| **TRAINING** | Persona capture with human experts | Isolated SKM cluster or VPC. Kafka topics prefixed `training.*`. SomaBrain training sandbox; Vault issues one-time credentials per trainer. GPU pools available for fine-tuning. | Conversation and tool events recorded immutably; backlog allowed but flagged. Requeue entries must be manually acknowledged. Attachments stored in encrypted object storage. | Policy engine runs in strict guided mode: sensitive tools require explicit trainer approval. Training locks prevent automation outside the supervised session. All data tagged with session IDs. | Training persona learns continuously during session. After "Close Training", persona pack is synthesized, reviewed, and sealed. Automatic learning in production is constrained to configured adaptation weights for that persona. |
| **PRODUCTION** | Multi-tenant live deployment | Multi-region Kubernetes. Kafka/KRaft with tiered storage and MirrorMaker. Redis Cluster with replication; Postgres HA (Patroni/Citus). Qdrant + ClickHouse multi-AZ. Managed Soma SLM API endpoints with autoscaling alongside Whisper GPU pools. Vault, OPA/OpenFGA, Kong/Envoy with mTLS, Prometheus/Thanos metrics stack. | Bulletproof messaging: transactional outbox, DLQ, requeue dashboards, SLA monitoring. WebSocket/SSE buffering to survive worker restarts. Cross-region replication ensures RPO < 1 minute. | Policy engine enforced fail-closed. Blocks require signed overrides (recorded to audit). Secrets rotated via Vault; Kyverno/Falco enforce runtime policies. SOC2/SOX audit logs persisted. | Model profiles tuned per tenant/persona. High-cost models only used when scoring threshold met. Continuous learning limited to approved SomaBrain areas; adaptation metrics audited. |

## Mode Implementation Hooks
- Environment variable `SOMA_AGENT_MODE` controls runtime behaviour. Loader sets:
  - Kafka topic prefixes/suffixes and retention policies.
  - Redis TTL and failover strategy.
  - Postgres schema namespace and connection pool sizes.
  - Policy engine enforcement level (warn, observe, strict).
  - Default model profiles and allowed escalation.
  - SomaBrain namespace (local/dev/training/prod).
- Configuration stored in `config/modes.yaml` with separate GitOps overlays per environment.
- Application code should never branch on personas when deciding infrastructure; branch on mode only.

## Observability & Alerts per Mode
- LOCAL: Console logging, optional Prometheus scrape via docker-compose. Alerts disabled.
- DEVELOPMENT: Alerts on Kafka lag, worker crashes, policy errors. Warning-only budgets.
- TRAINING: Alerts on stalled sessions, unreviewed requeue entries, high-risk tool calls.
- PRODUCTION: Full SLA alerting (latency, refusal rate, token spikes, audio failures), budget breach alerts, policy violation pages.

## Security & Compliance
- All modes honour the "no mocks" doctrine: tests use real OSS services, though scaled down in LOCAL.
- Training data retention follows compliance requirements; persona packs digitally signed before promotion.
- Production mode enforces per-tenant isolation (Kafka ACLs, Postgres RLS, Vault policies).

## Next Steps
1. Implement `config/modes.py` and propagation of mode-specific settings.
2. Create GitOps manifests for each mode (dev/test/training/prod) referencing the OSS stack.
3. Update documentation and UI to display active mode and warnings when in permissive states.
4. Integrate mode awareness into policy client, model selector, telemetry exports, and SomaBrain namespace handling.

## Infrastructure Reference
For detailed OSS infrastructure stacks per mode (Docker Compose for LOCAL, Kubernetes overlays for DEVELOPMENT/TRAINING/PRODUCTION), see `docs/SomaAgent01_Infrastructure.md`.
