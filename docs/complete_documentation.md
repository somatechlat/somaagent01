# Agent Zero – Complete Documentation

> **Audience:** Architects, operators, and developers who need a single, comprehensive reference for the Agent Zero platform.
> 
> **Scope:** Project vision, architecture, deployment, configuration, development workflow, observability, security, roadmap, and supporting resources.

---

## 1. Executive Summary

Agent Zero is an enterprise-grade, multi-agent automation framework. It combines a FastAPI gateway, Kafka event backbone, Redis cache, PostgreSQL persistence, and a collection of worker services that execute LLM-driven conversations, tool calls, and governance workflows. The platform runs entirely in Docker and supports both a UI-first mode and a programmable API surface. Recent updates introduced Docker Compose profiles, CI/Security automation, and a consolidated roadmap to streamline enterprise adoption.

---

## 2. Solution Architecture

### 2.1 Runtime Topology
| Layer | Component | Responsibility |
|-------|-----------|----------------|
| **Edge** | `gateway` (FastAPI + Uvicorn) | Public REST API, websocket streaming, auth/policy enforcement, OpenAPI spec. |
| **Messaging** | `kafka` | Pub/Sub hub for conversation messages, tool requests, delegation events. |
| **State** | `postgres` | Durable session storage, telemetry, tenant metadata. |
|  | `redis` | Ephemeral cache, session acceleration, rate limiting. |
| **Workers** | `conversation-worker`, `tool-executor`, `settings-service`, `router` | Consume Kafka topics, execute agent loops, manage configuration and routing. |
| **Optional Services** | `openfga`, `opa`, `delegation`, `audio-service`, `canvas-service`, `scoring-job`, `agent-ui`, etc. | Provide fine-grained authorization, policy enforcement, delegation UI, audio/canvas features, scoring automation. |

> A detailed component description is available in [`docs/architecture.md`](architecture.md).

### 2.2 Deployment Modes
- **Core profile** – Minimal, production-ready stack: Kafka, Redis, Postgres, gateway, conversation-worker, tool-executor, settings-service, router.
- **Optional profiles** – Enable analytics (`clickhouse`), metrics (`prometheus`, `grafana`), vector store (`qdrant`), or feature services (`audio-service`, `canvas-service`, `delegation`, `openfga`, etc.).
- **Dev profile** – Adds `agent-ui` for local UI experimentation.

Compose profiles keep the footprint lean while allowing operators to enable extra services on demand.

---

## 3. Deployment Guide

### 3.1 Prerequisites
- Docker Engine / Docker Desktop 24+
- Docker Compose v2
- macOS, Linux, or Windows 11 with WSL2
- Optional: GitHub CLI (`gh`) for automated issue/project creation

### 3.2 Build & Launch
```bash
# Build all images (fresh install)
docker compose -f docker-compose.somaagent01.yaml build --no-cache

# Start the minimal core stack
docker compose -f docker-compose.somaagent01.yaml --profile core up -d

# (Optional) include UI or other profiles
docker compose -f docker-compose.somaagent01.yaml --profile core --profile dev up -d
```

### 3.3 Health Verification
```bash
# List running containers
docker compose -f docker-compose.somaagent01.yaml ps

# Gateway health
curl http://localhost:8010/health

# OpenAPI schema (after Sprint 1)
curl http://localhost:8010/openapi.json
```

### 3.4 Teardown
```bash
docker compose -f docker-compose.somaagent01.yaml down --remove-orphans
```

---

## 4. Configuration & Settings

### 4.1 Environment Variables
The `x-agent-env` block in `docker-compose.somaagent01.yaml` centralizes runtime configuration:

| Variable | Default | Purpose |
|----------|---------|---------|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka bootstrap URL. |
| `REDIS_URL` | `redis://redis:6379/0` | Redis cache DSN. |
| `POSTGRES_DSN` | `postgresql://soma:soma@postgres:5432/somaagent01` | Primary database DSN. |
| `CONVERSATION_INBOUND` / `OUTBOUND` | `conversation.*` | Kafka topics for agent traffic. |
| `TOOL_REQUESTS_TOPIC` / `TOOL_RESULTS_TOPIC` | `tool.requests` / `tool.results` | Tool execution RPC flow. |
| `GATEWAY_JWT_SECRET` | `changeme` | Shared secret for JWT auth. |
| `OPA_URL`, `POLICY_DATA_PATH` | `http://opa:8181`, `/v1/data/soma/allow` | Policy decision point. |
| `SOMA_BASE_URL` | Host call-back URL | Used by services contacting host resources. |

> Expand/override via `.env` or Compose overrides. Sensitive values should be injected through secrets managers in production (Vault, AWS Secrets Manager).

### 4.2 Settings Service
`settings-service` exposes admin configuration APIs on port `8011`. Use it to:
- Configure tenants (`TENANT_CONFIG_PATH`)
- Toggle delegation modes
- Register custom tools/instruments

Documentation: [`docs/SomaAgent01_Settings.md`](./SomaAgent01_Settings.md) *(create if missing – see TODOs).* 

### 4.3 Profiles & Feature Flags
Enable optional workloads by adding profiles at launch:
```bash
# Add OpenFGA & OPA for fine-grained auth
docker compose -f docker-compose.somaagent01.yaml --profile core --profile optional up -d

# Add analytics & metrics stacks
--profile analytics --profile metrics
```

---

## 5. Development Workflow

### 5.1 Branching Strategy
- Feature branches per sprint (`sprint-1-api`, `sprint-2-security`, `sprint-3-observability`)
- Open PRs to `main` / `V0.1.1`
- Use GitHub Project board (*SomaAgentHub – Parallel Sprints*) with columns: Backlog → In-Progress → Review → Done.

### 5.2 Testing & Tooling
| Command | Purpose |
|---------|---------|
| `pytest -q` | Core unit/integration tests. |
| `ruff check .` | Python linting. |
| `bandit -r . -ll` | Security static analysis. |
| `safety check --full-report` | Dependency vulnerability scan. |

### 5.3 GitHub Actions
Three workflows live in `.github/workflows/`:
- **`ci.yml`** – Install deps, run Ruff + Pytest on push/PR.
- **`security.yml`** – Run Bandit and Safety scans.
- **`otel.yml`** – Validates OTEL instrumentations and gateway import path.

> These pipelines provide immediate feedback for all parallel sprint branches.

### 5.4 Local Tooling
- `make` support can be added (optional) to wrap common Compose operations.
- Use `docker exec somaAgent01_gateway pytest -q` for in-container testing.

---

## 6. Observability & Operations

### 6.1 Metrics & Dashboards
- **Prometheus** (port `9090`) scrapes gateway metrics via `/metrics` endpoint.
- **Grafana** (port `3000`, `metrics` profile) includes prebuilt dashboards under `infra/observability/grafana/`.
- Configure alerts in `infra/observability/alerts.yml` (latency, error-rate thresholds).

### 6.2 Tracing
Sprint 3 introduces OpenTelemetry:
- Install `opentelemetry-instrumentation-fastapi`, export via OTLP.
- Set env vars: `OTEL_TRACES_EXPORTER=otlp`, `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4317` (or similar).
- Propagate Kafka headers for trace continuity (`conversation-worker`, `tool-executor`).

### 6.3 Logging
- Services log to stdout; aggregate via Docker logging driver or Fluent Bit.
- Audit logs (security sprint) capture JWT failures, policy denials.

---

## 7. Security & Governance

Key controls implemented or planned:
- **JWT Authentication** – Gateway middleware validates bearer tokens. Secrets sourced from Vault (or `.env` in dev).
- **OPA Policies** – Reusable policy enforcement via REST calls to OPA (`POLICY_DATA_PATH`).
- **OpenFGA** – Optional ABAC/RBAC store. Migration job (`openfga-migrate`) runs when optional profile enabled.
- **Audit Trail** – JSON log lines for denied requests; integrate with ELK/Splunk.
- **API Key Self-Service** – UI module for key lifecycle (Sprint 2 deliverable).

Refer to `SPRINT_PLAN.md` for exact acceptance criteria.

---

## 8. Product Roadmap & Sprints

### 8.1 Canonical Roadmap
`ROADMAP_SPRINTS.md` outlines multi-quarter initiatives:
- Vision & milestones
- Integration with marketplaces
- Scaling strategies

### 8.2 Active Parallel Sprints (Weeks 1–4)
| Sprint | Focus | Owner | Key Deliverables |
|--------|-------|-------|------------------|
| **Sprint 1** | API Stabilisation | Backend team | `/openapi.json`, versioned endpoints, test suite, CI. |
| **Sprint 2** | Security & Governance | Security team | JWT auth, OPA middleware, OpenFGA ACLs, API key UI, audit logs. |
| **Sprint 3** | Observability & Resilience | Ops team | OTEL tracing, Grafana dashboards, circuit breaker, load tests. |

Dependent sprints (Marketplace, Performance) are detailed in `SPRINT_PLAN.md`.

---

## 9. Repository Structure

```
agent-zero/
├── docker-compose.somaagent01.yaml      # Compose with profiles
├── DockerfileLocal                      # Local build with PyJWT, aiokafka, etc.
├── docs/                                # Documentation (this file, architecture, quickstart, etc.)
├── services/
│   ├── gateway/main.py                  # FastAPI entrypoint
│   ├── conversation_worker/main.py
│   └── tool_executor/main.py
├── infra/                               # Docker/K8s manifests, observability config
├── prompts/                             # Agent prompt templates
├── python/                              # Core Python libraries/tools
├── .github/workflows/                   # CI, security, OTEL pipelines
└── requirements.txt                     # Python dependencies (PyJWT, aiokafka, redis, etc.)
```

> See `docs/architecture.md` for a more exhaustive directory breakdown.

---

## 10. Operational Runbook (Quick Reference)

| Topic | Command / Link |
|-------|----------------|
| Start core stack | `docker compose -f docker-compose.somaagent01.yaml --profile core up -d` |
| Start full stack | `docker compose -f docker-compose.somaagent01.yaml up -d` |
| Tear down | `docker compose -f docker-compose.somaagent01.yaml down --remove-orphans` |
| Health check | `curl http://localhost:8010/health` |
| Logs (gateway) | `docker logs -f somaAgent01_gateway` |
| Tests | `pytest -q` |
| Lint | `ruff check .` |
| Security scan | `bandit -r . -ll` |
| Update roadmap | `docs/ROADMAP_SPRINTS.md`, `SPRINT_PLAN.md` |

---

## 11. Next Steps & TODOs

1. **Document settings API** (`docs/SomaAgent01_Settings.md`) with common endpoints, payloads.
2. **Add Makefile** targets for common Compose/Lint/Test flows.
3. **Automate OTEL exporters** via environment templates.
4. **Add end-to-end tests** for optional profiles (audio, canvas, delegation).

---

## 12. References
- [`docs/architecture.md`](architecture.md) – Detailed component architecture.
- [`docs/quickstart.md`](quickstart.md) – UI and CLI quick start guides.
- [`docker-compose.somaagent01.yaml`](../docker-compose.somaagent01.yaml) – Deployment definition with profiles.
- [`ROADMAP_SPRINTS.md`](../ROADMAP_SPRINTS.md) – Strategic roadmap.
- [`SPRINT_PLAN.md`](../SPRINT_PLAN.md) – Detailed sprint tasks & acceptance criteria.
- [`requirements.txt`](../requirements.txt) – Python dependency list.

---

**Maintainers:** Update this file whenever the architecture, deployment process, or sprint plans change to ensure a single source of truth for the Agent Zero platform.
