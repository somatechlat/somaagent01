---
title: SomaAgent01 Sprint & Wave Plan
version: 2.0.0
last-reviewed: 2025-10-25
owner: platform
status: synchronized-with-ROADMAP_CANONICAL
---

**How to read this**
- Waves are major phases; Sprints are two-week execution windows. Backend (Gateway/Replicator), UI, and Infra/Observability can run in parallel where dependencies allow.

**Wave A – Foundations & Hardening**

Sprint S1 (Weeks 1–2)
- Gateway: add `/ui/config.json` (runtime config). DoC: example payload + env mapping.
- Gateway: DLQ Gauge refresher task (`GATEWAY_DLQ_POLL_SECONDS`, `DLQ_TOPICS`).
- SomaClient: confirm Retry-After handling, logging redaction, universe vs. namespace (done; add tests).
- Observability: verify Prometheus scrapes in dev/staging; document ports.
- Exit: config endpoint returns expected fields; DLQ gauge changes without `/v1/health` calls.

Sprint S2 (Weeks 3–4)
- Gateway: finalize CORS and (if cookies used) CSRF token flow.
- Security: document OPA decision points and scopes for upcoming admin endpoints.
- Infra: seed recording-rule names in your dashboards project; align labels and cardinality.
- Exit: security checklist green; Prometheus shows all key metrics families.

**Wave B – Memory Admin API + UI Contract**

Sprint S3 (Weeks 5–6)
- Gateway: `GET /v1/admin/memory` (list) backed by `memory_replica`; implement filters/pagination and DB indexes.
- Gateway: `GET /v1/admin/memory/{event_id}` (detail).
- Docs: OpenAPI fragments; examples for filters.
- Exit: list/detail serve 10–100k rows responsively.

Sprint S4 (Weeks 7–8)
- Gateway: `DELETE /v1/memory/{id}` (scoped) and `POST /v1/memory/batch` (bulk edits); server computes idempotency.
- Gateway: `GET /v1/memory/export` streamed with size limits/rate limits.
- Security: enforce admin scopes; rate limiting; audit logs.
- Exit: UI contract frozen; latency within target; rate/size limits enforced.

Status: Completed (admin endpoints delivered; OpenAPI tags added; optional admin rate limit shipped).

**Wave C – E2E & Capacity**

Sprint S5 (Weeks 9–10)
- E2E: Testcontainers (Kafka+Postgres): WAL→replica (ok) and forced error→DLQ.
- Load/soak: gateway write-through + WAL knobs; measure replication lag and error rate.
- Exit: zero-loss proven; lag steady ≤ 2s at baseline; chaos recovery drains backlog.
	- Harness: `scripts/load/soak_gateway.py`; run via `make load-soak` with env overrides. Pending: execute in CI/staging and capture baselines.

**Wave D – Production Hardening**

Sprint S6 (Weeks 11–12)
- Enable prod flags: `GATEWAY_REQUIRE_AUTH`, `GATEWAY_WRITE_THROUGH`, `GATEWAY_WRITE_THROUGH_ASYNC`.
- TLS/mTLS to SomaBrain as required; finalize OPA/OpenFGA; runbooks.
- Alerts: DLQ, lag, error-rate; staging fire drills.
- Exit: canary rollout plan approved; alerts validated in staging.

**Wave E – Scalability & UX Extras (optional, parallelizable)**

Sprint S7 (Weeks 13–14)
- Scaling: Kafka partitions for `memory.wal`; Replicator HPA; Gateway HPA.
- Optional: SSE/WS “memory changes” feed (post-replica) if UI requires live updates.
- Exit: throughput SLOs sustained; feed prototype validated (if applicable).

Sprint S8 (Weeks 15–16)
- Edge: consider Envoy/Traefik in front of Gateway for TLS/circuit-breaking.
- Optimization: caching/pagination refinements; index tune-up.
- Exit: edge proxy decision made; tuning documented.

**Parallelization Matrix**
- Backend (Gateway/Replicator) can deliver Wave B while Infra/Observability completes S2.
- UI wiring (separate repo) starts after S3 API list/detail stabilize; delete/batch/export in S4.
- Dashboards work can begin once metrics families are verified in S2 and iterate alongside S5.

**Acceptance Gates per Sprint**
- Each sprint includes: unit/integration tests; docs updated; performance checks for changed paths; Prometheus scrape verified; security checks (headers, redaction).

**Dependencies**
- SomaBrain dev endpoint (health: /health or /healthz).
- Kafka/Postgres reachable for WAL and replica.
