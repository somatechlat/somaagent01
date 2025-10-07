# 🏎️ Parallel Sprint Plan – SomaAgentHub (Enterprise Edition)

**Goal:** Deliver a production‑ready, enterprise‑grade AI‑agent platform while keeping the existing Kafka‑based event backbone. The plan runs **three sprints in parallel** (Sprints 1‑3) followed by dependent sprints (4‑5). Each sprint is a 4‑week timebox.

---

## 📅 Sprint Calendar (Weeks 1‑12)
| Week | Sprint | Parallel Track |
|------|--------|----------------|
| 1‑4  | **Sprint 1 – API Stabilisation** | ✅ (core) |
| 1‑4  | **Sprint 2 – Security & Governance** | ✅ (core) |
| 1‑4  | **Sprint 3 – Observability & Resilience** | ✅ (core) |
| 5‑8  | **Sprint 4 – Marketplace & Extensions** | ⬜ (depends on 1‑3) |
| 9‑12 | **Sprint 5 – Performance & Scaling** | ⬜ (depends on 1‑3, optional after 4) |

All three core sprints start **simultaneously**. Teams can be split into three sub‑teams (API, Security, Observability) or a single team rotating daily.

---

## 🗂️ Sprint 1 – API Stabilisation (Core)
**Owner:** `backend‑team`
**Key Deliverables**
- **OpenAPI generation** in `services/gateway/main.py` (`/openapi.json`).
- **Versioned API** (`/v1`, future `/v2`).
- **Full integration test suite** for all public endpoints (`/v1/health`, `/v1/models`, `/v1/sessions/*`).
- **CI pipeline** (GitHub Actions) that runs the test suite on every PR.
- **Documentation** update (`docs/SomaAgent01_API.md`) with auto‑generated spec.

**Tasks**
| # | Description | Owner | Dep. |
|---|-------------|-------|------|
| 1.1 | Add FastAPI `app.openapi()` route, mount static JSON file. | backend | – |
| 1.2 | Refactor all endpoint paths under `/v1/`. | backend | 1.1 |
| 1.3 | Write pytest integration tests (use `httpx.AsyncClient`). | qa | 1.2 |
| 1.4 | Create GitHub Action `ci.yml` (lint → test → coverage). | devops | 1.3 |
| 1.5 | Update docs with generated spec link. | docs | 1.1 |
| 1.6 | Add API version header middleware (optional). | backend | 1.2 |

**Acceptance Criteria**
- `curl http://localhost:8010/openapi.json` returns a valid OpenAPI v3 JSON.
- All integration tests pass (`100 %` pass on CI).
- Documentation reflects the new spec.

---

## 🛡️ Sprint 2 – Security & Governance (Core)
**Owner:** `security‑team`
**Key Deliverables**
- **JWT authentication** using the secret from Vault (`GATEWAY_JWT_SECRET`).
- **OPA policy middleware** integrated into the gateway (fallback to `POLICY_FAIL_OPEN`).
- **OpenFGA tenant & resource ACL checks** for every request.
- **Self‑service UI** for API‑key issuance (re‑use `agent‑ui` component).

**Tasks**
| # | Description | Owner | Dep. |
|---|-------------|-------|------|
| 2.1 | Add JWT validation dependency (`pyjwt`) and middleware in `gateway/main.py`. | security | – |
| 2.2 | Pull secret from Vault at startup (use `hvac` client). | security | – |
| 2.3 | Wrap OPA policy evaluation as FastAPI dependency (`depends`). | security | 2.1 |
| 2.4 | Integrate OpenFGA client; enforce `tenant_id` header on all routes. | security | 2.3 |
| 2.5 | Extend UI (`agent‑ui`) with “API Keys” page (POST to `/v1/keys`). | ui | 2.2 |
| 2.6 | Add audit logging (JSON lines) for auth failures and policy denials. | security | 2.4 |
| 2.7 | Write security‑focused tests (invalid JWT, denied policy). | qa | 2.1‑2.4 |

**Acceptance Criteria**
- Requests without a valid JWT receive **401**.
- Policy violations return **403** with a detailed audit entry.
- OpenFGA enforces tenant isolation; cross‑tenant requests are blocked.
- UI shows created API keys and allows revocation.

---

## 📈 Sprint 3 – Observability & Resilience (Core)
**Owner:** `ops‑team`
**Key Deliverables**
- **OpenTelemetry** tracing across gateway, conversation‑worker, tool‑executor.
- **Prometheus** exporters already exist – create Grafana dashboards for latency, error‑rate, Kafka lag.
- **Circuit‑breaker** around external tool calls (e.g., `tenacity` with exponential back‑off).
- **Load‑testing harness** (locust or k6) to validate 500 concurrent sessions.

**Tasks**
| # | Description | Owner | Dep. |
|---|-------------|-------|------|
| 3.1 | Install `opentelemetry‑instrumentation‑fastapi` and configure exporter (OTLP to localhost). | ops | – |
| 3.2 | Add tracing context propagation to Kafka messages (headers). | ops | 3.1 |
| 3.3 | Create Grafana dashboards (`gateway_latency`, `tool_execution_time`, `kafka_consumer_lag`). | ops | – |
| 3.4 | Implement circuit‑breaker decorator around tool‑executor calls. | ops | – |
| 3.5 | Write load‑test scenarios (chat creation, tool usage). | qa | 3.4 |
| 3.6 | Set up alert rules in Prometheus (latency > 2 s, error‑rate > 1 %). | ops | 3.3 |

**Acceptance Criteria**
- End‑to‑end traces appear in Jaeger/Grafana Tempo UI.
- Dashboard shows real‑time metrics; alerts fire on simulated failure.
- Load test passes with average latency < 2 s for 500 concurrent sessions.

---

## 📦 Sprint 4 – Marketplace & Extensions (Dependent)
**Owner:** `platform‑team`
**Depends on:** Completion of Sprints 1‑3 (API stable, auth enforced, observability in place).
**Key Deliverables**
- **Capsule registry service** (REST API) to publish, version, and sign capsules.
- **Artifact storage** (MinIO) with Cosign signatures.
- **SDK (`somaagent` Python)** enhancements for capsule discovery.
- **CI/CD pipeline** for capsule validation (lint, test, sign) before publishing.

**Tasks**
| # | Description | Owner | Dep. |
|---|-------------|-------|------|
| 4.1 | Design `capsule‑registry` API (POST /capsules, GET /capsules/{id}). | platform | – |
| 4.2 | Add MinIO bucket & Cosign integration (store .tar.gz + signature). | platform | – |
| 4.3 | Extend SDK with `client.publish_capsule()` and `client.list_capsules()`. | sdk | 4.1 |
| 4.4 | Create GitHub Action `capsule‑publish.yml` (lint → test → cosign). | devops | 4.2 |
| 4.5 | Update UI (`agent‑ui`) to browse marketplace and install capsules. | ui | 4.1 |
| 4.6 | Write end‑to‑end tests for capsule lifecycle. | qa | 4.1‑4.5 |

**Acceptance Criteria**
- A new capsule can be uploaded via API, stored in MinIO, and signed.
- SDK can discover and install the capsule in a running session.
- UI shows marketplace entries and installation status.

---

## 🚀 Sprint 5 – Performance & Scaling (Final)
**Owner:** `performance‑team`
**Depends on:** Sprints 1‑3 (core) and optionally on Sprint 4 if marketplace load is relevant.
**Key Deliverables**
- **Horizontal scaling** of Kafka (increase partitions, add replicas).
- **Autoscaling policies** for `gateway`, `conversation‑worker`, `tool‑executor` (Kubernetes HPA if deployed, otherwise Docker‑compose replica scaling).
- **Advanced caching**: add Redis‑based result cache for repeated tool calls.
- **Benchmark suite** (pytest‑benchmark) to measure end‑to‑end latency under varying loads.

**Tasks**
| # | Description | Owner | Dep. |
|---|-------------|-------|------|
| 5.1 | Increase `KAFKA_CFG_NUM_PARTITIONS` to 6, enable replication. | ops | – |
| 5.2 | Add Docker‑compose `scale` directives for gateway & workers (e.g., `gateway: 3`). | ops | – |
| 5.3 | Implement Redis cache wrapper in `tool_executor` (key = tool+args). | performance | – |
| 5.4 | Write benchmark scripts (load 1000 sessions, measure 95th‑pct latency). | qa | 5.3 |
| 5.5 | Create HPA manifests (if using K8s) and test rolling updates. | ops | – |
| 5.6 | Document scaling guide (`docs/scaling.md`). | docs | – |

**Acceptance Criteria**
- System can handle **1000 concurrent sessions** with 95th‑pct latency ≤ 3 s.
- Adding a replica of `gateway` results in linear throughput increase.
- Cache hit‑rate > 70 % for repeated tool calls reduces external calls.

---

## 📋 How to Track & Execute
1. **Create a GitHub Project Board** named *SomaAgentHub – Enterprise*.
   - Columns: `Backlog`, `In‑Progress`, `Review`, `Done`.
   - Add each task (e.g., `1.1 Add OpenAPI route`) as an Issue and assign to the appropriate team.
2. **Label Issues** with the sprint number (`sprint‑1`, `sprint‑2`, …) and the functional area (`api`, `security`, `observability`).
3. **Milestones** – one milestone per sprint (4‑week window). Issues auto‑move when the milestone is closed.
4. **CI/CD** – the `ci.yml` from Sprint 1 will automatically run on every PR; add additional jobs for security (`security.yml`) and observability (`otel.yml`).
5. **Daily Stand‑ups** – each sub‑team reports progress on its board column; blockers are raised as GitHub Issues.
6. **Demo Review** – at the end of each sprint hold a live demo (API spec, security flow, dashboards) and collect stakeholder sign‑off before moving to the next sprint.

---

## 📍 API Location (for all sprints)
All public endpoints are served by the **Gateway** service (`services/gateway/main.py`). The service runs on **port 8010** (exposed via Docker‑compose as `${GATEWAY_PORT:-8010}`). Key routes:
```
GET  /health                     → health check
GET  /metrics                    → Prometheus metrics
GET  /openapi.json               → OpenAPI v3 spec (Sprint 1)
GET  /v1/models                  → List LLM models
POST /v1/sessions                → Create chat / task session
GET  /v1/sessions/{id}           → Poll session status / streamed output
POST /v1/sessions/{id}/cancel    → Cancel a running session
GET  /v1/tools                   → List registered tool definitions
```
All routes are behind the optional JWT middleware (`GATEWAY_REQUIRE_AUTH`) and OPA policy checks (`POLICY_FAIL_OPEN`).

---

## ✅ Next Immediate Action
- **Run**: `git checkout -b sprint‑1‑api` and create the first issue for task 1.1 (Add OpenAPI route).
- **Add** the `ci.yml` workflow (copy from the repo template under `.github/workflows/`).
- **Create** the GitHub Project board and populate it with the tasks above.

Feel free to ask for any of the concrete files (e.g., `ci.yml`, `security.yml`, `otel.yml`) or for a more detailed breakdown of any sprint.
