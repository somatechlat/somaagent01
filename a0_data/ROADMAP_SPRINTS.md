# 🗺️ Canonical Sprint Roadmap – SomaAgentHub (Enterprise Edition)

## Vision
Create a production‑ready, enterprise‑grade AI‑agent platform that scales, is secure, observable, and extensible while keeping the existing **Kafka‑based event backbone**.

---

## 📆 Sprint Structure
We organize work into **4‑week sprints**. Each sprint has a **Goal**, **Key Deliverables**, **Owner(s)**, and **Acceptance Criteria**.

### Sprint 1 – Foundations & Core API Stabilisation
**Goal**: Harden the core gateway/orchestrator stack, add full test coverage, and publish a stable OpenAPI spec.
- ✅ Refactor `services/gateway/main.py` to expose a **complete OpenAPI schema** (`/openapi.json`).
- ✅ Add **integration tests** for all public endpoints (`/v1/health`, `/v1/models`, `/v1/sessions/*`).
- ✅ Implement **API versioning** (`/v1`, future `/v2`).
- ✅ Harden **environment validation** (fail fast if required env vars missing).
- ✅ Document all endpoints in `docs/SomaAgent01_API.md` (auto‑generated from FastAPI.
- **Acceptance**: `curl http://localhost:8010/openapi.json` returns a valid JSON schema; 100 % test pass.

### Sprint 2 – Security & Governance Layer
**Goal**: Enable enterprise‑grade authentication, authorization, and policy enforcement.
- ✅ Integrate **OPA** policy evaluation directly in the gateway middleware (fallback to `POLICY_FAIL_OPEN`).
- ✅ Add **JWT** validation using `vault`‑stored keys (`GATEWAY_JWT_SECRET`).
- ✅ Implement **OpenFGA** tenant & resource ACL checks for every request.
- ✅ Provide a **self‑service UI** for managing API keys and policies.
- **Acceptance**: Requests without a valid JWT are rejected (401); policy violations return 403 with detailed audit logs.

### Sprint 3 – Observability, Scaling & Resilience
**Goal**: Make the platform observable, autoscale‑ready, and tolerant to failures.
- ✅ Export **OpenTelemetry traces** from gateway, orchestrator, and tool‑executor (correlate via `trace_id`).
- ✅ Deploy **Prometheus** + **Grafana** dashboards (already in compose) with alerts for latency > 2 s, error‑rate > 1 %.
- ✅ Implement **Kafka consumer groups** with dynamic partition scaling (increase `KAFKA_CFG_NUM_PARTITIONS`).
- ✅ Add **circuit‑breaker** pattern around external tool calls (via `tenacity`).
- **Acceptance**: Dashboard shows live metrics; load‑test with 500 concurrent sessions shows < 2 s average latency.

### Sprint 4 – Enterprise Extensions & Marketplace
**Goal**: Provide a marketplace for reusable capsules and enable custom tool onboarding.
- ✅ Create **capsule‑registry** service (REST API) to publish, version, and sign capsules.
- ✅ Implement **artifact storage** in `vault`/MinIO with **cosign** signatures.
- ✅ Add **SDK enhancements** (`somaagent` Python package) for capsule discovery and execution.
- ✅ Provide **CI/CD pipelines** (GitHub Actions + Dagger) that automatically lint, test, and publish new capsules.
- **Acceptance**: A new capsule can be uploaded via API, appears in the UI marketplace, and is consumable by agents.

### Sprint 5 – Global Deployments & Multi‑Region Support (Optional Future)
- Deploy the stack via **Helm** to Kubernetes clusters across regions.
- Enable **cross‑region Kafka MirrorMaker** for event replication.
- Add **geo‑aware routing** in the gateway.
- Provide **IaC** (Terraform) for provisioning cloud resources.

---

## 📦 Canonical Files & Locations
- **Roadmap** – `ROADMAP_SPRINTS.md` (this file).
- **API implementation** – `services/gateway/main.py` (FastAPI entry point).
- **OpenAPI spec** – generated at runtime at `http://<host>:8010/openapi.json`.
- **Service definitions** – Docker‑compose file `docker-compose.somaagent01.yaml`.
- **Documentation** – `docs/` folder (API docs, architecture, quickstart).

---

## 📡 Where the API Lives
All public HTTP endpoints are served by the **Gateway service** (`services/gateway/main.py`). The service runs on port **8010** (exposed as `localhost:8010` in Docker‑compose). Key routes:
```
GET  /health                     – health check
GET  /metrics                    – Prometheus metrics
GET  /openapi.json               – OpenAPI schema
GET  /v1/models                  – List available LLM models
POST /v1/sessions                – Create a new chat / task session
GET  /v1/sessions/{id}           – Poll session status / streamed output
POST /v1/sessions/{id}/cancel    – Cancel a running session
GET  /v1/tools                  – List registered tool definitions
POST /v1/tool_executor           – Direct tool invocation (internal use)
```
All routes are protected by the optional JWT middleware and OPA policy checks (configurable via `GATEWAY_REQUIRE_AUTH` and `POLICY_FAIL_OPEN`).

---

## ✅ Next Steps
1. **Commit this roadmap** – the file is now part of the repository.
2. **Kick‑off Sprint 1** – start by adding the OpenAPI generation and test suite.
3. **Create a GitHub project board** with the sprint tickets listed above.
4. **Verify the API location** by running:
   ```bash
   curl http://localhost:8010/openapi.json | jq .info.title
   ```
   You should see the FastAPI app title.

Feel free to adjust sprint priorities or add additional tickets. The foundation is in place; we keep **Kafka** as the backbone because it provides reliable, ordered event streaming essential for enterprise workloads.
