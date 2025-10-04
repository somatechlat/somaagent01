# SomaAgent 01 – Production Architecture Blueprint

## 1. Vision & Scope

SomaAgent 01 is the flagship tenant-aware automation agent that sits at the heart of **SomaStack**. It unifies Agent Zero’s orchestration logic with SomaBrain’s cognitive memory, delivers dynamic LLM/SLM routing, and exposes reliable multi-tenant APIs capable of millions of requests per day. The agent must:

- Serve interactive and asynchronous requests with strict SLOs.
- Persist every action (chat, tool run, routing decision) into auditable memory streams.
- Autonomously delegate subtasks to other agents via the upcoming **SomaAgent Server** fabric.
- Operate across clouds/kubernetes clusters while remaining deterministic, testable, and secure.

## 2. High-Level Architecture

### 2.1 Control Plane

| Component | Responsibility |
|-----------|----------------|
| **Envoy/Istio Ingress** | mTLS termination, rate limiting, JWT/OIDC validation, tenant routing |
| **SomaAgent API (FastAPI / Uvicorn)** | Chat & task entry point, exposes REST/gRPC, performs authorization, emits events |
| **Router Service** | Litellm-backed dynamic LLM/SLM selector; enforces cost, latency, policy, and tenant budgets |
| **Canvas Service** | Manages multi-pane UI state (code, HTML, logs). Stores layout per conversation |
| **Delegation Gateway** | Publishes tasks to SomaAgent Server (Kafka topic `somastack.delegation`) and tracks status |
| **Background Workers (Celery/Arq)** | Execute code runs, memory consolidations, reconciliation, retry queue |
| **Admin Console** | Real-time dashboards for routing policy, spend, queue depth, tenant controls |

### 2.2 Data & Messaging Plane

| Store / Bus | Purpose |
|-------------|---------|
| **Kafka** | Canonical event stream (`agent.messages`, `agent.memory`, `agent.audit`, `agent.routing`) |
| **Redis Cluster** | Low-latency caches (session state, working memory scratchpad, rate limiting) |
| **Postgres HA** | Conversations, canvas layout, routing policies, tenant metadata, audit snapshots |
| **SomaBrain Stack** | Long-term hyperdimensional memory, graph transport, feedback adaptation |
| **Qdrant / PGVector** | Vector store that SomaBrain uses for LTM shards |
| **Object Storage (S3/GCS)** | Artifact storage (files, code outputs), constitution snapshots, event archives |
| **Enterprise Control Switch** | Feature flag + event bus to toggle enterprise mode across services, enabling stricter OSS-only stacks, extended logging, audit exports |

## 3. Request Lifecycle

1. **Ingress & Auth** – Request hits Envoy. JWT verified, tenant & role derived.
2. **Policy Check** – OPA policy (per tenant) decides allowed tools/models.
3. **Audit Event** – `agent.audit` record emitted (Kafka with JSON schema validation).
4. **Context Assembly** – SomaBrain `/context/evaluate` produces memory bundle, residual stream, governance tags.
5. **Routing Decision** – Router Service scores providers (Groq, HF, OpenAI, SLMs) using live metrics, policy, and budget state. Decision logged to `agent.routing`.
6. **SLM/LLM Invocation** – Agent call executed (Litellm). Results streamed to Canvas panes and stored in Postgres.
7. **Tool Execution / Delegation** – Tool call or sub-agent task enqueued (`agent.tool` topic). Workers execute locally or forward to SomaAgent Server via delegation gateway.
8. **Feedback Loop** – Agent posts `/context/feedback` to SomaBrain. Memory event saved; routing outcome appended to preference dataset.
9. **Observation & Alerts** – Metrics/traces/logs shipped through OTEL collector to Prometheus/Loki/Tempo.

## 4. Dynamic Routing & Learning

### 4.1 Provider Tiers

| Tier | Provider | Purpose |
|------|----------|---------|
| Premium | OpenAI GPT-4o / Claude Opus | Complex reasoning, premium tenants |
| Standard | Groq LPU models, Claude Sonnet, GPT-4o mini | General workloads with cost/latency balance |
| SLM | Llama 3.1 8B, Phi-3 Mini, Mistral 7B | Offline, low-cost, task-specific runs |

### 4.2 Autonomic Mode Switching
- **State Detection**: heartbeat monitors for SomaBrain, external LLM providers, network reachability, and local subsystem health.
- **Modes**:
  - `CONNECTED` – full cloud path; SomaBrain synced, premium routing available.
  - `DEGRADED` – partial outage (e.g., SomaBrain down, network healthy). Agent automatically routes cognition through SLM tier, queues memory events locally, UI shows amber indicator.
  - `LOCAL_ONLY` – no outbound connectivity. Agent remains fully functional using SLM + local queue, UI shows red indicator.
- **Recovery**: queue replay & reconciliation when connectivity returns; state flips back to `CONNECTED` with audit trail.
- **Logging**: every state transition, queued message, and replayed event emits audit entries for traceability.
- **Policy Hooks**: OPA rules can restrict tool usage or certain providers when in degraded/local modes.
- **Enterprise Controls**: `ENTERPRISE_MODE` enforces OSS/self-hosted providers only, disables training, raises audit verbosity, and requires approvals for capsule/tool changes.

### 4.2 Router Inputs
- Task embedding & classification (from SomaBrain planner)
- Policy metadata (tenant, data sensitivity, jurisdiction)
- Live metrics (p50/p95 latency, error rate, spend)
- User/tenant preferences (stored in Postgres, learned from feedback)

### 4.3 Learning Loop
1. Routing decision + context hashed → stored in `agent.routing` topic.
2. SomaBrain feedback event or manual rating appended with success metadata.
3. Offline trainer updates preference weights (e.g., Bayesian bandit or contextual bandit) and writes new policy row.
4. Router service hot-reloads policy (Redis pub/sub) without downtime.

## 5. Multi-Tenancy & Governance

| Aspect | Mechanism |
|--------|-----------|
| Data Isolation | Tenant IDs propagate through Kafka keys, Redis prefixes, Postgres schemas |
| Spend Limits | Per-tenant budget table; router denies premium models beyond threshold |
| Memory Segregation | SomaBrain namespace per tenant (`somabrain_ns:<tenant>`); vector shards segregated |
| Delegation Permissions | OPA policy decides which tenants can spawn sub-agents |
| Canvas Visibility | Canvas panes tagged with tenant/session; WebSocket endpoints require scoped JWT |

### 5.1 Privileged Host Operations
- Containers run as `root` by default (Debian base) so the agent can manage system tasks, install packages, and operate like a power user when policies allow.
- For environments where host-level control is required (e.g., maintenance on the underlying VM), deploy the API/worker pods with elevated capabilities (`SYS_ADMIN`, host PID namespace) behind explicit OPA approvals and audit logging.
- Provide a safeguarded “Privileged Mode” toggle in admin console; all elevations generate audit events (`agent.audit` with action=`privilege_escalation`).
- Host access commands (apt, systemctl, docker, podman) executed via dedicated tool wrappers that enforce tenant/role policy before running.

## 6. Message Queue & Event Store

- **Queue Implementation**: Kafka with idempotent producers. Each API call writes to Postgres (transaction) + Kafka. Debezium optional for CDC.
- **Consumers**: Memory worker, audit archiver, routing trainer, SLA monitor. All consumers acknowledge via offsets; failures logged & retried.
- **Replay & Recovery**: On startup or after outage, workers seek from last committed offset to rehydrate state. SomaBrain reconciliation worker compares Redis/Qdrant/Postgres to Kafka log.
- **JSON Everywhere**: All events and API payloads use versioned JSON schemas (validated at publish time) to keep the pipeline consistent, auditable, and language-agnostic.

## 7. Deployment Blueprint

| Layer | Technology |
|-------|------------|
| Container Runtime | Docker images (Debian base) with root user inside. |
| Orchestration | Kubernetes (managed). Helm charts for each service. |
| Autoscaling | HPA (CPU, queue length), KEDA for Kafka-driven workers. |
| CI/CD | GitHub Actions → image registry → ArgoCD/Flux. Terraform provisions infra. |
| Secrets | Vault or cloud secrets manager (CSI driver). |
| Observability | OTEL collector → Prometheus/Grafana + Loki/Tempo. |
| Chaos | Litmus or custom jobs hitting Kafka/Redis/SomaBrain to verify resilience. |

## 8. Modes & Deployment Profiles

SomaAgent runs in distinct modes to match the lifecycle of development and operations. All services read the active mode from configuration (`SOMAGENT_MODE`) and listen for `mode.changed` events so toggling is instant and auditable.

| Mode | Purpose | Characteristics |
|------|---------|-----------------|
| `DEVELOPER` | Local hacking, feature spikes | Looser auth, mock providers, verbose logs, training allowed, OSS defaults |
| `TRAINING` | Capturing domain knowledge / persona shots | Training locks enabled, lineage tracking, writes to training sandbox only |
| `TEST` | Deterministic integration/CI | Frozen personas and tools, mock outputs, no external calls, training disabled |
| `PRODUCTION` | Customer-facing runtime | Full policies, budgets enforced, premium routing allowed, audit strict |
| `PRODUCTION-ENTERPRISE` | OSS-only, compliance-focused enterprise tenant | Same as production but forces OSS/self-hosted providers, disables training by default, extended logging/retention |

Mode impacts: router provider allowlist, training availability, logging verbosity, feature toggles in Admin UI, and deployment manifests. Enterprise mode applies suite-wide (SomaAgent + SomaGent + SomaBrain/SomaFractalMemory) to guarantee consistent compliance posture.

## 9. Math & Traceability Touchpoints

- **Hyperdimensional Memory Metrics**: monitor unbind epsilon, density-matrix eigenvalues, recall margins per tenant. Alert on deviations.
- **Graph Transport Analytics**: track effective resistance, flow distribution (once FRGO implemented). Use these to understand task routing structure.
- **Router Decisions**: log probability scores per provider → analyze success vs. cost. Feed into bandit algorithm.
- **Delegation Graphs**: represent sub-agent orchestration as flows, enabling mathematical analysis of delegation efficiency.
- **Audit Integrity**: formal hashes (SHA3-512) and Ed25519 signatures stored alongside flows to guarantee invariants.

## 10. Scaling Strategy

1. Stateless API pods behind load balancer.
2. Shard working memory by tenant hash (consistent hashing ring) to keep locality.
3. Offload rarely accessed LTM segments to secondary persistence (object storage) with lazy hydrate.
4. Use role spectrum disk cache (mmap) shared per node to amortize generation.
5. Gradually increase HRR dim in dark launch (duplicate bind/unbind internally, compare cosine before switch).
6. Autonomic throttling: when state != CONNECTED, prefer SLM tier, reduce external LLM concurrency, expand local queue buffers, and raise alerts.
7. Enterprise switch propagation: `enterprise.mode.changed` events fan out to services so toggling OSS-only/compliance settings is a one-click operation.

## 11. Interfaces & APIs

- `/chat/stream` – streaming agent responses + canvas updates.
- `/admin/routing` – CRUD for routing policies, budget knobs, provider toggles.
- `/canvas/*` – create/update/delete panes, subscribe to updates.
- `/delegation/task` – enqueue tasks to SomaAgent Server; includes callback URLs and governance metadata.
- `/context/evaluate`, `/feedback` – SomaBrain context cycle.
- `/memory/**` – direct LTM operations (restricted to internal usage).

## 11. Reliability Targets

| SLO | Target |
|-----|--------|
| Availability | 99.9% monthly |
| /chat latency | p95 < 2.5s |
| Recall latency | p95 < 100ms |
| Routing accuracy | > 90% match to optimal (measured via feedback) |
| Audit delivery | 100% events persisted (Kafka + S3) |

## 12. Security Controls

- Enforce mTLS between all services (SPIFFE IDs).
- OPA Rego policies for tool usage, delegation, data residency.
- Rate limiting & anomaly detection (Redis + Prometheus rules).
- Detailed audit & compliance logs for every operation (exposed to SIEM).
- Tenant-scoped encryption keys (KMS), optional differential privacy layer for exported memories.

## 13. Future Enhancements

- Implement FRGO transport learning + reconciliation worker (pending SomaBrain roadmap).
- Multi-region active-active replication (Kafka MirrorMaker, Redis CRDB, Postgres logical replication).
- Differential privacy for tenant analytics.
- Delegation graph analytics & visualization in admin UI.
- Automated LLM evaluation harness (fuzz prompts, regression detection).
- Brain enrichment hooks: summarize canvas panes, tool outputs, audio analytics, and routing outcomes into structured SomaBrain events so the brain’s graph stays fully synced with agent state.

---
Use this document as the living baseline for SomaAgent 01. Update sections as components evolve or new capabilities ship.
