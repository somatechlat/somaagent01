# Canonical Architecture Cleanup – Action Tracker
Owner: Codex (all VIBE personas)  
Status Legend: [ ] open | [~] in progress | [x] done

## Phase P0 – unblock startup & imports
- [x] remove all `persist_chat` imports (8 files) → replace with PostgresSessionStore / AttachmentsStore and verify `python -m compileall`.
- [x] create `python/tasks/core_tasks.py` with delegate/build_context/evaluate_policy/store_interaction/feedback_loop/rebuild_index/publish_metrics/cleanup_sessions tasks (shared_task config, OPA checks, metrics, dedupe).
- [x] export tasks in `python/tasks/__init__.py`; ensure Celery worker discovers them.

## Phase P1 – Celery reliability
- [x] extend `celery_app.py`: task_routes (5+ queues), beat_schedule (metrics 60s, cleanup 3600s), visibility_timeout 7200, task_reject_on_worker_lost True, broker transport options; add dedupe hook.
- [~] add Prometheus metrics decorators/counters to all tasks; validate `/metrics` (counters added; validation pending).
- [x] add Flower deployment entry to docker-compose/helm (monitoring).
- [x] add dynamic task registry loader (DB + Redis cache + reload signal) with signed artifact/hash verification and OPA gate.
- [x] expose runtime task APIs: `/v1/tasks/register`, `/v1/tasks`, `/v1/tasks/reload` with audit events, OPA allow/deny, and Celery reload hook.
- [x] add SomaBrain task_feedback hook with outbox retry on DOWN and tagging for recall (tasks + tool executor).
- [x] add planner priors fetch from SomaBrain into task/tool planning prompts.

## Phase P1 – Settings single source of truth
- [x] deprecate `settings_sa01.py`, `settings_base.py`, `admin_settings.py`, `services/common/env.py`, `services/common/registry.py`; reroute callers to `src/core/config/cfg`.
- [x] split `python/helpers/settings.py`: keep UI converters; move config access to cfg/AgentSettingsStore/UiSettingsStore; remove file-based backups.

## Phase P1 – Web UI alignment
- [x] update `webui/config.js` & `webui/js/settings.js` to use `/v1/settings/sections` (PUT) and implement backend `/v1/test_connection`.
- [ ] verify settings save/ load roundtrip via AgentSettingsStore; remove `/v1/settings_save` legacy endpoint references (code refs removed; integration test to be run in env with Postgres).

## Phase P1 – Tool unification
- [ ] finalize UnifiedToolRegistry wiring (agent tools + executor + MCP); enforce OPA tool.view/request/enable; schema validation; Redis caches.
- [ ] seed/verify tool catalog (`infra/sql/tool_catalog_seed.sql`); ensure tool resolution path in agent and executor uses registry.

## Phase P2 – Prompt repository
- [ ] implement PromptRepository (PostgreSQL + Redis cache), schema, migration script to import `prompts/*.md`; update agent prompt loading to repository-only.

## Phase P2 – Upload/TUS & attachments
- [ ] implement resumable uploads (tusd or aiohttp-tus), SHA-256 hashing, ClamAV scan (pyclamd), PostgreSQL BYTEA storage, Range downloads; ensure attachment-session linkage and cascade delete.

## Phase P2 – Speech real implementations
- [ ] replace fake `/v1/speech/*` with real STT (Whisper), TTS (Kokoro/ElevenLabs), realtime WS; keep feature flag; remove placeholder responses.

## Phase P2 – Backup/log cleanup
- [ ] remove file-path backups/logs (`tmp/**`, `logs/*.html`); migrate to PostgreSQL data and structured logging.

## Phase P2 – Context Builder polish
- [ ] add preload hook for ContextBuilder; implement Presidio redactor; optional optimal token budgeting; extend feedback payload; add missing tests.
- [~] add SomaBrain auto-summary storage and reuse; include coordinates/tags in session events (auto-summary storage done; reuse/tags pending).

## Phase P0.5 – Constitution & Persona Prompting
- [ ] implement ConstitutionPromptProvider: fetch/verify signed Constitution from SomaBrain; TTL cache; reload hook; fail-closed.
- [ ] implement PersonaProvider: per-tenant/persona prompt overlays + tool prefs; OPA-guarded updates; version tagging.
- [ ] wire PromptBuilder: Constitution base + persona + priors + health/safety; inject versions; no file I/O.
- [ ] enforce Constitution/OPA tool filtering in prompt tool lists; tag prompts/events with `constitution_version`.

## Validation checklist (run per milestone)
- [ ] `python -m compileall .`
- [ ] `pytest` (unit + integration touched modules)
- [ ] Celery worker/beat dry-run (`celery -A python.tasks.celery_app worker -l info`)
- [ ] `/metrics` exposes task/tool counters; Flower shows healthy workers
- [ ] UI settings save/test-connection flows succeed end-to-end
