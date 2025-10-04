⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 – Sprint 0A & 0B Execution Plan

## Sprint Goals
- Provision the full OSS infrastructure baseline required by SomaAgent 01 (Kafka/KRaft, Redis, Postgres, Qdrant, ClickHouse, Whisper, vLLM, OPA/OpenFGA, Vault, Prometheus/Loki/Tempo).
- Establish GitOps/CI pipelines and developer tooling for deterministic environments.
- Deliver a FastAPI gateway skeleton wired to Kafka with Redis/Postgres session repositories and WebSocket/SSE streaming stubs.

## Sprint 0A (Weeks 0–1) – Infrastructure Bootstrap

### Deliverables
1. **Platform Deployments**
   - Helm charts / Argo CD applications for:
     - Kafka/KRaft (Strimzi) with required topics and ACL templates.
     - Redis cluster (TLS + ACL) for session cache & requeue store.
     - Postgres (primary + replica) with RLS policies scaffolded.
     - Qdrant vector DB, ClickHouse analytics cluster.
     - Whisper ASR (FasterWhisper GPU) & fallback CPU deployment.
     - vLLM serving Llama 3 8B Instruct (with GPU node selectors & autoscaling rules).
     - OPA + OpenFGA, HashiCorp Vault.
   - Terraform/Kustomize overlays for dev/test/prod clusters.

2. **Observability Baseline**
   - Prometheus, Alertmanager, Loki, Tempo via Helm; service monitors for Kafka, Redis, Postgres, vLLM, Whisper.
   - Seed Grafana/SomaSuite dashboards (cluster health, Kafka lag, GPU utilization).

3. **Developer Tooling**
   - `docker-compose.somaagent01.yaml` standing up Kafka, Redis, Postgres, Qdrant, ClickHouse, vLLM CPU, Whisper CPU.
   - `docs/development/LOCAL_ENV.md` with environment variables, seed credentials, smoke test commands.

4. **Documentation Update**
   - Rename legacy references to **SomaAgent 01** across README and architecture docs.
   - Add infrastructure diagram for control plane/data plane layout.

### Acceptance Criteria
- Dev cluster running all required services with readiness/liveness checks passing.
- Local docker-compose stack executes smoke test (publish → consume Kafka → persist to Postgres).
- Prometheus scraping all services; dashboard screenshot attached to sprint review notes.
- Documentation PR merged with new naming + infra diagram.

### Risks & Mitigations
- **GPU availability**: Provide CPU fallback deployments; document configuration flags.
- **Secrets**: Ensure Vault integrates before enabling prod credentials; rotate bootstrap secrets immediately.

## Sprint 0B (Week 2) – Event Skeleton & Session Repositories

### Deliverables
1. **Gateway Skeleton (FastAPI)**
   - `POST /v1/session/message`: validates JWT + constitution hash via OPA, enqueues to `conversation.inbound`, logs audit event.
   - `GET /v1/session/{id}/stream`: WebSocket/SSE endpoint consuming `conversation.outbound` for correlated session messages.
   - Middleware for tenant extraction, request IDs, Redis-backed rate limiting, OTEL spans.

2. **Session Repository Abstractions**
   - `SessionCache` (Redis) storing current persona ID, model profile override, history pointers, pending tool requests.
   - `SessionStore` (Postgres) persisting conversation turns, tool events, policy verdicts, attachment metadata; includes alembic migrations.
   - Unit tests ensuring read/write consistency and TTL handling.

3. **Kafka Client Library**
   - `infrastructure/event_bus` Python package with producer/consumer wrappers (idempotent writes, retries, DLQ support, JSON Schema validation).
   - Shared message contract defined in `schemas/conversation_event.json` & `schemas/tool_event.json`.

4. **Streaming Stubs**
   - Gateway WebSocket aggregates partial messages and progress updates; SSE fallback for browsers without WS.
   - Debug CLI (`scripts/send_message.py`) publishing sample events and verifying roundtrip through queue + repository.

5. **Documentation**
   - `docs/SomaAgent01_API.md` describing new endpoints, event schemas, authentication, correlation IDs.
   - Update runbooks for Ops (Kafka topic creation, schema evolution, monitoring).

### Acceptance Criteria
- Automated tests cover gateway, session repositories, event bus serialization.
- Manual smoke test: send message via CLI → observe event in Kafka → persisted session record.
- CI pipeline (Dagger + GitHub Actions) runs lint/tests/build for gateway service.
- Documentation merged with API specs and operational notes.

### Risks & Mitigations
- **Schema drift**: enforce JSON Schema validation and compatibility checks in CI.
- **Latency**: measure publish/consume latency; adjust Redis TTL/cache sizing accordingly.

---
This plan defines the exact scope for the first two sprints of SomaAgent 01, ensuring real infrastructure and event-driven foundations are in place.
