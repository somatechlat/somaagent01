⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 – Sprint 0A & 0B Execution Plan

## Sprint Goals
- Provision the full OSS infrastructure baseline required by SomaAgent 01 (Kafka/KRaft, Redis, Postgres, Qdrant, ClickHouse, Whisper, Soma SLM API connector, OPA/OpenFGA, Vault, Prometheus stack).
- Establish GitOps/CI pipelines and developer tooling for deterministic environments.
- Deliver a FastAPI gateway skeleton wired to Kafka with Redis/Postgres session repositories and WebSocket/SSE streaming stubs.

## Status Snapshot (Codebase as of Sprint 1B)
- Local development relies on Docker Desktop and the existing `infra/docker-compose.somaagent01.yaml`, but Kubernetes/GitOps artefacts are not yet in the repository.
- FastAPI gateway (`services/gateway/main.py`) is operational with Kafka wiring, Redis/Postgres persistence, and WebSocket streaming; JWT/OPA integration and rate limiting remain TODOs.
- Session cache/store abstractions and the shared event bus live under `services/common`, yet JSON schemas and automated tests outlined in the plan are still missing.

## Sprint 0A (Weeks 0–1) – Infrastructure Bootstrap

### Deliverables
1. **Platform Deployments** – *Not started*
   - No Helm/Argo/Terraform artefacts are present in `infra/`.

2. **Observability Baseline** – *Not started*
   - Prometheus stack and dashboards not yet committed.

3. **Developer Tooling** – *Partially delivered*
   - `infra/docker-compose.somaagent01.yaml` exists; dedicated local-env documentation and smoke tests remain to be written.

4. **Documentation Update** – *In progress*
   - Core docs reference SomaAgent 01, but infra diagrams and cross-file updates are still pending.

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
1. **Gateway Skeleton (FastAPI)** – *Partially delivered*
   - Core endpoints with WebSocket + SSE streaming, JWT verification (secret/public key/JWKS), and optional OPA policy evaluation are implemented. Rate limiting and OTEL spans remain TODOs.

2. **Session Repository Abstractions** – *Partially delivered*
   - `services/common/session_repository.py` implements Redis/Postgres stores; migrations and automated tests still outstanding.

3. **Kafka Client Library** – *In progress*
   - `services/common/event_bus.py` provides producer/consumer wrappers; JSON schemas for conversation/tool events now live under `schemas/`, with DLQ support still pending.

4. **Streaming Stubs** – *Partially delivered*
   - WebSocket streaming exists; SSE fallback, aggregated progress updates, and replay CLI are pending (only `scripts/send_message.py` is available).

5. **Documentation** – *Partially delivered*
   - API doc exists, but runbooks and schema references are incomplete.

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
