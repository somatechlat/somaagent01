# Merged Task List – SomaAgent01 Canonical Cleanup

## 📌 Critical Violations (from VIBE Compliance Report)
- **persist_chat imports** – remove from 8 files and replace with proper stores.
- **Missing `core_tasks.py`** – create consolidated Celery task module.
- **Missing Beat Schedule** – configure periodic tasks.
- **Missing Task Routes** – define queue routing for all tasks.
- **Settings Chaos** – consolidate 5 config systems into the single `src/core/config/cfg` façade.
- **UI‑Backend Endpoint Mismatch** – implement missing `/v1/settings_save` and `/v1/test_connection` endpoints.
- **Visibility timeout / task_reject_on_worker_lost / broker_transport_options** – add to Celery app.
- **OPA integration & deduplication** – enforce policy checks and idempotent task execution.
- **Missing Canvas patterns** – implement chain/group/chord helpers.
- **Flower monitoring** – deploy and expose.
- **Dynamic task registry & feedback hook** – add runtime registration and SomaBrain feedback.

## ✅ Completed Tasks (already done)
- Remove all `persist_chat` imports and replace with `PostgresSessionStore` / `AttachmentsStore`.
- Create `python/tasks/core_tasks.py` with required tasks.
- Export tasks in `python/tasks/__init__.py`.
- Extend `celery_app.py` with task routes, beat schedule, visibility timeout, etc. (partial – see remaining tasks).
- Add Flower entry to `docker-compose.yaml`.
- Update `webui` settings endpoints to use `/v1/settings/sections`.
- Refactor `tool_executor` to use `cfg` instead of `ADMIN_SETTINGS`.
- Stub `features` router created (to be replaced with real implementation).

## 📋 Remaining Tasks (merged from original TASKS.md + new items)
### Phase P0 – Unblock startup & imports
1. **Refactor `session_repository`** – replace `ADMIN_SETTINGS` with `cfg` (DSN & Redis URL).
2. **Refactor `requeue_store`** – same replacement.
3. **Refactor `export_job_store`** – same replacement.
4. **Refactor `budget_manager`** – same replacement.
5. **Refactor `tool_catalog`** – same replacement.
6. **Refactor `dlq_consumer`** – replace Kafka bootstrap usage.
7. **Refactor `telemetry_store`** – replace DSN usage.
8. **Refactor `agent_settings_store`** – replace DSN usage.
9. **Refactor `model_profiles`** – replace DSN, Redis, Kafka usage.
10. **Refactor `saga_manager`** – replace DSN usage.
11. **Refactor `memory_write_outbox`** – replace DSN usage.
12. **Refactor `ui_settings_store`** – replace DSN usage.
13. **Refactor `conversation_worker` main** – replace all legacy config usages.
14. **Refactor `delegation_worker` main** – replace config usages.
15. **Refactor `delegation_gateway` main** – replace config usages.
16. **Refactor `memory_sync` main** – replace config usages.
17. **Refactor `memory_replicator` main** – replace config usages.
18. **Refactor `session_store_adapter` helper** – replace config usages.
19. **Refactor `core_tasks` module** – ensure OPA URL & DSN usage via `cfg`.

### Phase P1 – Celery reliability (additional items)
20. **Add `beat_schedule`** to `python/tasks/celery_app.py` for metrics & cleanup.
21. **Add `task_routes`** to `celery_app.py` for the 5 required queues.
22. **Add `visibility_timeout = 7200`** to Celery config.
23. **Add `task_reject_on_worker_lost = True`** to Celery config.
24. **Add `broker_transport_options`** (e.g., `{'visibility_timeout': 7200}`) to Celery config.
25. **Implement Canvas pattern helpers** (chain/group/chord) for complex workflows.
26. **Add OPA `allow_delegate` integration** inside `core_tasks.delegate`.
27. **Add deduplication hook** using Redis SET NX for idempotent tasks.
28. **Deploy Flower** monitoring (verify operational).
29. **Implement dynamic task registry loader** (DB + Redis cache + signed artifact verification + OPA gate).
30. **Add task feedback hook** – publish structured feedback to SomaBrain with outbox retry.

### Phase P2 – Settings consolidation
31. Deprecate legacy settings modules (`settings_sa01.py`, `settings_base.py`, `admin_settings.py`, `services/common/env.py`, `services/common/registry.py`).
32. Split `python/helpers/settings.py` – keep UI helpers, move config access to `cfg`.
33. Verify settings round‑trip via `AgentSettingsStore` and remove `/v1/settings_save` references.

### Phase P3 – Observability & tooling
34. Add Prometheus metrics decorators to **all** Celery tasks (counters, histograms, success/failure).
35. Ensure `/metrics` endpoint exposes full task totals.
36. Verify Flower shows healthy workers.

### Phase P4 – UI & API alignment
37. Implement missing backend endpoints `/v1/settings_save` and `/v1/test_connection`.
38. Add missing `authorize_request` helper in `services/gateway/main.py` (OPA‑guarded).
39. Implement `ContextBuilderMetrics` (real Prometheus metrics for context builder).

### Phase P5 – Advanced features (future roadmap)
40. Dynamic task registry & runtime task registration API.
41. SomaBrain feedback integration for all tasks.
42. Prompt repository (PostgreSQL + Redis cache).
43. Resumable TUS uploads with ClamAV scanning.
44. Real speech endpoints (Whisper, ElevenLabs).
45. Log & backup cleanup – migrate to structured DB logging.
46. Constitution & Persona providers (security‑first, OPA‑guarded).
47. Full validation checklist automation.

---
*All tasks are tracked via the VS Code Todo extension (`manage_todo_list`). Use the VIBE personas (Developer, Architect, Auditor, QA, Performance, DevOps, Product) to prioritize and implement each item.*
