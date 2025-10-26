---
title: SomaAgent01 Canonical Roadmap
version: 2.1.0
last-reviewed: 2025-10-26
owner: platform
status: source-of-truth
---

**Purpose**
- Establish a single, canonical plan to wire all memory operations through the Gateway to SomaBrain, guarantee durability (WAL → Kafka → Postgres replica + DLQ), and expose production-grade metrics for Voyant. UI never calls SomaBrain directly.

**Scope & Principles**
- Single front door: UI and external clients only talk to the Gateway (`services/gateway`).
- Single memory backend: SomaBrain (dev default SOMA_BASE_URL=http://host.docker.internal:9696; health: /health or /healthz).
- Durability-first writes: Gateway write-through → publish `memory.wal` → `memory_replicator` persists to Postgres; DLQ on failure.
- Read path for UI: Postgres `memory_replica` via Gateway admin endpoints (fast filters/pagination).
- Security: JWT + OPA/OpenFGA at the Gateway; no SomaBrain secrets in browsers.
- Observability: Prometheus-only here; Voyant (separate project) renders dashboards and alerts.

**Key Metrics (consumed by external dashboards)**
- `gateway_dlq_depth{topic}` – DLQ size (Gateway Gauge; refreshed periodically).
- `memory_replicator_lag_seconds` – WAL→replica lag (Replicator Gauge).
- `gateway_write_through_attempts_total{path}`; `gateway_write_through_results_total{path,result}`; `gateway_write_through_wal_results_total{path,result}` – write-through health (Gateway Counters).
- `somabrain_request_seconds_bucket{method,path,status}` (+ `_sum/_count`) and `somabrain_requests_total{method,path,status}` – client heatmap and request mix (SomaClient Histogram/Counter).
- Supporting: `outbox_sync_effective_batch_size`, `somabrain_health_state{state}`, `memory_replicator_events_total{result}`, `memory_replicator_replication_seconds`.

**Current State (2025-10-26)**
- Gateway write-through, WAL emit, DLQ admin, health aggregation present.
- SomaClient hardened (retries/backoff; honors Retry-After; circuit breaker; OTEL; logging redaction; correct universe vs. namespace).
- Replicator writes `memory_replica`; emits lag/throughput metrics; stores DLQ rows.
- DLQ depth gauge exported; docs and Compose cleaned of legacy SKM.
- UI Gateway mode enabled: `/message_async` forwards to Gateway; SSE via `/gateway_stream?session_id=…` renders streamed events.
- UI health now proxies Gateway `/healthz`; status indicator reflects Gateway/SomaBrain health; Send is gated when unhealthy. Local-agent fallback in the UI message path has been removed.
-- Wave B admin APIs implemented in Gateway: list/detail/export/delete/batch, with OpenAPI tags and optional admin rate limiting. Replica schema/indexes ensured by store.
-- Wave C harness added: `scripts/load/soak_gateway.py` plus Make targets (`make load-smoke`, `make load-soak`) and docs in `docs/technical-manual/load-testing.md`.

**Target Architecture (steady state)**
- UI → Gateway (`/v1/*`).
- Gateway (auth/OPA/idempotency) → SomaBrain HTTP for writes/recalls; publishes `memory.wal` on successful writes.
- Replicator → Postgres replica table for browse/audit; DLQ store + Kafka *.dlq topic on errors.
- External monitoring scrapes Gateway/Replicator/Outbox metrics and renders dashboards/alerts.

**Waves (Major Phases)**

Wave A – Foundations & Hardening (security, correctness, metrics)
- Lock universe vs. namespace semantics end-to-end.
- Ensure sensitive header redaction everywhere; disable noisy prints (done).
- Add background DLQ depth refresher task in Gateway (periodic Gauge update).
- Expose `/ui/config.json` from Gateway for runtime UI config (api base, defaults, feature flags).
- Verify Prometheus scrape ports and service discovery across envs.
- Remove UI local-agent fallback; Gateway errors surface to UI (done).
- Gate Send on Gateway/SomaBrain health; use UI `/health` → Gateway `/healthz` proxy (done).

Wave B – Memory Admin API + UI Contract
- Add Gateway endpoints for UI:
  - `GET /v1/admin/memory` (list from `memory_replica` with filters/pagination)
  - `GET /v1/admin/memory/{event_id}` (detail)
  - `GET /v1/memory/export` (streamed; filters)
  - `DELETE /v1/memory/{id}` (scoped delete via SomaClient)
  - `POST /v1/memory/batch` (bulk remember/update; server idempotency)
- Document scopes and OPA policy decisions; rate-limit and size-limit admin actions.

Status: delivered in Gateway; optional token-bucket rate limit via `GATEWAY_ADMIN_RPS`/`GATEWAY_ADMIN_BURST`.

Wave C – E2E & Capacity
- Kafka+Postgres Testcontainers e2e for WAL→replica (happy path) and DLQ on forced error. (done)
- Add outage→recovery e2e for memory_sync. (done)
- Soak/load tests for write-through + WAL; prove zero-loss and bounded lag under chaos. (harness available; execute/tune pending)
- Recording rules for Voyant (latency quantiles, error rates, lag maxima) – defined in Voyant repo. (external)

Wave D – Production Hardening
- Enable `GATEWAY_REQUIRE_AUTH=true`, `GATEWAY_WRITE_THROUGH=true`, `GATEWAY_WRITE_THROUGH_ASYNC=true` in prod. (auth enforced in code; compose defaults vary by profile)
- JWT via header or cookie: `GATEWAY_JWT_COOKIE_NAME` supported for browser sessions; CSRF middleware available via env flags. (done)
- OPA evaluation and optional OpenFGA tenant checks enforced when `REQUIRE_AUTH=true`. (present)
- TLS/mTLS to SomaBrain as required (config/env-driven). (pending env)
- Secret rotation runbooks; rate-limits; incident playbooks; disaster recovery path. (pending docs)

Wave E – Scalability & UX Extras (optional)
- Partition tuning for `memory.wal`; HPA for Replicator and Gateway.
- Optional: SSE/WS for “memory changes” feed (post-replica) if UI needs live updates.
- Optional: Envoy/Traefik as edge proxy in front of Gateway for TLS/circuit-breaking.

**Sprint Overview (brief)**
- S1: Remove UI fallback; health proxy wiring; Send gating (done).
- S2: Config endpoint and DLQ refresher verification (done).
- S3–S4: Wave B endpoints + indexes; OpenAPI; rate/size limits.
- S5: Wave C e2e and initial load tests; tune knobs (`OUTBOX_SYNC_*`, SomaClient retries, partitions). (partially done: e2e complete; load test pending)
- S6: Wave D security hardening; prod flags on; runbooks and alerts validated.
- S7–S8: Wave E scalability and optional UX streams in parallel as needed.

**Environment & Ports (defaults)**
- SomaBrain (dev): `SOMA_BASE_URL=http://host.docker.internal:9696` (health: `/health` or `/healthz`).
- Gateway metrics: `GATEWAY_METRICS_PORT` (recommend 9400).
- Replicator metrics: `REPLICATOR_METRICS_PORT` (default ~9403).
- Outbox Sync metrics: `OUTBOX_SYNC_METRICS_PORT` (default 9469).

**Definition of Done (per Wave)**
- A: No sensitive logs; DLQ Gauge refresh visible without calling `/v1/health`; `/ui/config.json` returns correct runtime config.
- B: UI can list/filter/detail/delete/export/batch via Gateway only; performance acceptable at realistic volumes.
- C: E2E/chaos tests prove zero-loss; recording rules validated in Voyant.
- D: Security gates enforced; alerts firing thresholds proven in staging.
- E: Throughput SLOs sustained under scaled traffic; optional UX streaming validated if implemented.

**Source of Truth**
- This file supersedes prior roadmap documents. Any sprint or milestone docs MUST align with this plan.

---

# Attachments Architecture (No Local Files) – Canonical Plan

Purpose
- Enable file uploads with antivirus and strict admin controls without writing to local disk. Persist attachments in Postgres, reference them from memory events, and stream downloads/exports directly from the DB.

Constraints
- No local filesystem writes anywhere in the app, except user-initiated Settings backup download (server does not persist a backup file).
- Antivirus scanning must occur without temp files (clamd INSTREAM).
- Admin Settings are the single control plane.

Data Model (Postgres)
- Table: attachments
  - id UUID PRIMARY KEY
  - tenant TEXT
  - session_id TEXT
  - persona_id TEXT NULL
  - filename TEXT
  - mime TEXT
  - size INTEGER
  - sha256 TEXT
  - status TEXT CHECK ('clean','quarantined')
  - quarantine_reason TEXT NULL
  - created_at TIMESTAMPTZ DEFAULT NOW()
  - content BYTEA NULL (NULL when using external_ref or strict quarantine policy that drops bytes)
- Indexes: (session_id, created_at DESC), (tenant, created_at DESC), (sha256)
- Optional dedup (per-tenant) by sha256 if enabled.

Gateway Flows
- Upload (POST /v1/uploads)
  - Enforce: uploads_enabled, uploads_max_mb, uploads_max_files, allowed/denied MIME.
  - Stream to ClamAV via INSTREAM; compute sha256 while reading; no temp files.
  - On strict AV error → 502; non-strict → status=quarantined with reason.
  - Storage policy:
    - If size ≤ uploads_inline_max_mb → store bytes in BYTEA; save metadata; return descriptor.
    - If size > inline cap → either 413 (default) or accept only external_ref if enabled and domain allowlisted.
  - Memory integration: message events include ["att://<uuid>"] references.
- Download (GET /v1/attachments/{id})
  - Authz via authorize_request (+OPA when enabled); tenant/session scoping.
  - Quarantined behavior:
    - store_and_block → 403 until cleared.
    - drop_bytes_keep_meta → content unavailable by design.
  - If external_ref → 302 to URL or signed proxy URL (future optional).

Admin Settings (extends existing sections)
- Uploads
  - uploads_enabled: bool (default false in prod; true in dev)
  - uploads_max_mb: number (default 25)
  - uploads_max_files: int (default 10)
  - uploads_allowed_mime / uploads_denied_mime: CSV/lines
  - uploads_ttl_days: number (default 7)
  - uploads_janitor_interval_seconds: number (default 3600)
  - uploads_storage_backend: "postgres" (read-only)
  - uploads_inline_max_mb: number (default 16)
  - uploads_allow_external_ref: bool (default false)
  - uploads_external_ref_allowlist: CSV domains
  - uploads_dedup_sha256: bool (default false)
  - uploads_quarantine_policy: enum {store_and_block, drop_bytes_keep_meta}
  - uploads_download_token_ttl_seconds: int (optional; for signed URLs)
- Antivirus
  - av_enabled: bool (default false)
  - av_strict: bool (default false)
  - av_host: string (default "clamav")
  - av_port: number (default 3310)
  - av_test: test action (EICAR via INSTREAM)

Janitor & Metrics
- Replace filesystem janitor with DB purge by TTL.
- Metrics: attachments_deleted_total, attachments_quarantined_total, uploads_janitor_errors_total, uploads_janitor_last_run_timestamp.

Exports (Admin)
- Replace local NDJSON files with streamed NDJSON over HTTP directly from Postgres (memory_replica and optional attachment metadata). No server file artifacts.

Security & Privacy
- No local files; AV INSTREAM only; external URLs gated by allowlist when enabled; optional signed download tokens; OPA policy points for upload/download.

Waves Addendum (Attachments)
- Wave A: INSTREAM AV helper, minimal schema/store, feature flags off by default.
- Wave B: Upload endpoint refactor to Postgres storage; Download endpoint; Settings wiring; unit tests.
- Wave C: DB janitor and metrics; streamed exports; e2e tests incl. AV strict/non-strict.
- Wave D: Prod hardening (OPA rules for attachments, signed URLs if enabled), runbooks.
- Wave E: Optional external_ref proxying & quotas (per-tenant caps), dedup toggle.

Success Criteria (Attachments)
- Uploads function with AV without local disk usage.
- Attachments referenced in events; downloads authorized and policy-compliant.
- TTL purge and metrics observable; export streams work without temp files.

Risks & Mitigations
- DB bloat → Enforce TTL; optional sha256 dedup per tenant; observability on table growth.
- AV downtime → strict mode blocks; non-strict quarantines; alert on AV connectivity.
- Large files → hard caps; optional external_ref allowlist; never buffer on disk.

Rollback
- Feature flag off disables uploads; existing attachments remain accessible until TTL purge.
