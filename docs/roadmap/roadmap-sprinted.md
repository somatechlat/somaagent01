## Sprinted Roadmap — Notifications First, then Scheduler (Q4 2025)

Scope: Convert the Celery integration (canonical) into actionable sprints focusing first on centralized Notifications, then unified Scheduler API and Celery enablement under a feature flag.

Timebox: 4 sprints × 2 weeks (≈8 weeks total)

Sprint 0 (Prep – first 2 days)
- Runtime config surfaces: `notifications.enabled`, `scheduler.enabled`, `scheduler.use_celery` via `/v1/runtime/config` and `/v1/ui/settings/sections` (read‑only).
- UI conditional rendering for Notifications & Scheduler panels.
- Acceptance: Flags show in REST & UI; no functional regressions.

Sprint 1 — Notifications System (Backend + UI)
- Backend:
  - Table `ui_notifications` (id, tenant_id, user_id?, type, title, body, severity, created_at, read_at, ttl_at, meta JSONB).
  - REST: `GET /v1/ui/notifications`, `POST /v1/ui/notifications`, `POST /v1/ui/notifications/{id}/read`, `DELETE /v1/ui/notifications/clear` (filter + pagination).
  - SSE event `ui.notification` (create/read/clear) with lightweight payload; metrics `ui_notifications_total{severity,type}`.
  - TTL janitor job (APScheduler) deleting expired rows.
- Frontend:
  - Store `notificationsStore.js` (list, markRead, clear, subscribe SSE).
  - Modal/panel + toast helper; unread badge; ARIA roles.
- Security: Auth scope check; optional OPA policy on create.
- Tests: Pytest (CRUD + TTL), Playwright (badge, live push, mark read).
- Acceptance: REST create appears via SSE < 1s; unread counter accurate; TTL purges; tests green.

Sprint 2 — Unified Scheduler API (APScheduler backend)
- Backend:
  - Endpoints: `GET/POST/PUT/DELETE /v1/ui/scheduler/jobs`, `POST /v1/ui/scheduler/jobs/{id}/run`, `GET /v1/ui/scheduler/runs`.
  - Adapter interface `IScheduler`; APScheduler implementation; Celery stub returns 501 when flag on but not provisioned.
  - JWT scopes: `scheduler:read`, `scheduler:write`, `scheduler:run`; audit log entries.
  - Metrics: `scheduler_jobs_total`, `scheduler_runs_started_total`, `scheduler_runs_success_total`, `scheduler_runs_failure_total`, histogram `scheduler_run_duration_seconds`.
- Frontend: Scheduler panel (list/create/edit/delete/run-now); reads runtime flags to show mode.
- Docs: API reference, scope matrix, migration notes.
- Tests: Unit (validators/adapter), integration (CRUD + run), Playwright (create + run + delete).
- Acceptance: Full CRUD & run-now on APScheduler; metrics exposed; UI operational; scopes enforced.

Sprint 3 — Celery Integration (Flag OFF by default)
- Infra: docker-compose add `celery_worker`, `celery_beat`; env `SCHEDULER_USE_CELERY`; Redis broker/backend.
- Backend: `celery_app/` factory; Celery adapter mapping unified API to Beat + ad‑hoc tasks; task wrapper `scheduler.run_job`.
- Migration tooling: Export APScheduler jobs → JSON; transform → Celery Beat; dry-run apply.
- Tests: Integration compose test (create job, beat enqueue, worker execute, status visible); unit for adapter.
- Acceptance: Flag ON routes through Celery; run-now works; rollback by flag toggle validated.

Sprint 4 — Migration & Hardening
- Staging parallel run (APScheduler control vs Celery) 48h; compare success/failure metrics.
- Cutover procedure documented; rollback tested.
- Load tests for p95/p99 durations; queue depth gauges; retry/backoff verified.
- Security: Final scope review; OPA tenant policies; audit log sampling.
- Ops: Dashboards (Grafana) & runbooks (alerts: failed jobs spike, queue depth, long duration).
- Acceptance: Celery mode stable in staging & prod; SLOs met; runbooks + dashboards delivered; all tests green.

Cross‑Cutting Risks & Mitigations
- Redis saturation: add queue depth gauges + alert thresholds.
- Job duplication on migration: idempotent transform, dry‑run diff before apply.
- Scope misconfiguration: enforce deny default, explicit 403 with actionable message.
- Large notification volume: pagination + severity filtering; SSE payload kept lean.

Definition of Done (Program)
- Notifications live in production, used by UI flows.
- Unified Scheduler API released; Celery behind feature flag proven in staging.
- Migration path executed; rollback documented; observability & security baselines established.

Post‑Program Backlog (Nice to Have)
- Task chaining demo (Celery chords) with UI visualization.
- Dead‑letter queue surfacing in Scheduler panel.
- Multi‑tenant throttling policies (rate per tenant).
- WebSocket optional upgrade for high‑frequency job status streams.

Ownership (Placeholder)
- Sprint 1: Backend Engineer A + Frontend Engineer B
- Sprint 2: Backend Engineer A
- Sprint 3: DevOps Engineer C + Backend Engineer A
- Sprint 4: DevOps Engineer C + QA Engineer D

Tracking & Metrics Source of Truth
- Prometheus metrics names as listed; Grafana dashboard IDs reserved (`scheduler-overview`, `notifications-lag`).

Notes
- Keep feature flags read‑only in UI initially to avoid accidental production toggles.
- Reuse existing Redis; size check before enabling Celery result backend (may omit if not required for UI history).
