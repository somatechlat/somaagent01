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
2. **Refactor `requeue_store`** – same replacement. *(in-progress)*
3. **Refactor `export_job_store`** – same replacement. *(in-progress)*
4. **Refactor `budget_manager`** – same replacement. *(in-progress)*
5. **Refactor `tool_catalog`** – same replacement. *(in-progress)*
6. **Refactor `dlq_consumer`** – replace Kafka bootstrap usage. *(in-progress)*
7. **Refactor `telemetry_store`** – replace DSN usage. *(in-progress)*
8. **Refactor `agent_settings_store`** – replace DSN usage. *(in-progress)*
9. **Refactor `model_profiles`** – replace DSN, Redis, Kafka usage. *(in-progress)*
10. **Refactor `saga_manager`** – replace DSN usage. *(in-progress)*
11. **Refactor `memory_write_outbox`** – replace DSN usage. *(in-progress)*
12. **Refactor `ui_settings_store`** – replace DSN usage. *(in-progress)*
13. **Refactor `conversation_worker` main** – replace all legacy config usages. *(in-progress)*
14. **Refactor `delegation_worker` main** – replace config usages. *(in-progress)*
15. **Refactor `delegation_gateway` main** – replace config usages. *(in-progress)*
16. **Refactor `memory_sync` main** – replace config usages. *(in-progress)*
17. **Refactor `memory_replicator` main** – replace config usages. *(in-progress)*
18. **Refactor `session_store_adapter` helper** – replace config usages. *(in-progress)*
19. **Refactor `core_tasks` module** – ensure OPA URL & DSN usage via `cfg`. *(in-progress)*

### Phase P1 – Celery reliability (additional items)
20. **Add `beat_schedule`** to `python/tasks/celery_app.py` for metrics & cleanup. *(in-progress)*
21. **Add `task_routes`** to `celery_app.py` for the 5 required queues. *(in-progress)*
22. **Add `visibility_timeout = 7200`** to Celery config. *(in-progress)*
23. **Add `task_reject_on_worker_lost = True`** to Celery config. *(in-progress)*
24. **Add `broker_transport_options`** (e.g., `{'visibility_timeout': 7200}`) to Celery config. *(in-progress)*
25. **Implement Canvas pattern helpers** (chain/group/chord) for complex workflows. *(in-progress)*
26. **Add OPA `allow_delegate` integration** inside `core_tasks.delegate`. *(in-progress)*
27. **Add deduplication hook** using Redis SET NX for idempotent tasks. *(in-progress)*
28. **Deploy Flower** monitoring (verify operational). *(in-progress)*
29. **Implement dynamic task registry loader** (DB + Redis cache + signed artifact verification + OPA gate). *(in-progress)*
30. **Add task feedback hook** – publish structured feedback to SomaBrain with outbox retry. *(in-progress)*

### Phase P2 – Settings consolidation
31. Deprecate legacy settings modules (`settings_sa01.py`, `settings_base.py`, `admin_settings.py`, `services/common/env.py`, `services/common/registry.py`). *(in-progress)*
32. Split `python/helpers/settings.py` – keep UI helpers, move config access to `cfg`. *(in-progress)*
33. Verify settings round‑trip via `AgentSettingsStore` and remove `/v1/settings_save` references. *(in-progress)*

### Phase P3 – Observability & tooling
34. Add Prometheus metrics decorators to **all** Celery tasks (counters, histograms, success/failure). *(in-progress)*
35. Ensure `/metrics` endpoint exposes full task totals. *(in-progress)*
36. Verify Flower shows healthy workers. *(in-progress)*

### Phase P4 – UI & API alignment
37. Implement missing backend endpoints `/v1/settings_save` and `/v1/test_connection`. *(in-progress)*
38. Add missing `authorize_request` helper in `services/gateway/main.py` (OPA‑guarded). *(in-progress)*
39. Implement `ContextBuilderMetrics` (real Prometheus metrics for context builder). *(in-progress)*

### Phase P5 – Advanced features (future roadmap)
40. Dynamic task registry & runtime task registration API. *(in-progress)*
41. SomaBrain feedback integration for all tasks. *(in-progress)*
42. Prompt repository (PostgreSQL + Redis cache). *(in-progress)*
43. Resumable TUS uploads with ClamAV scanning). *(in-progress)*
44. Real speech endpoints (Whisper, ElevenLabs). *(in-progress)*
45. Log & backup cleanup – migrate to structured DB logging). *(in-progress)*
46. Constitution & Persona providers (security‑first, OPA‑guarded). *(in-progress)*
47. Full validation checklist automation). *(in-progress)*

---
*All tasks are tracked via the VS Code Todo extension (`manage_todo_list`). Use the VIBE personas (Developer, Architect, Auditor, QA, Performance, DevOps, Product) to prioritize and implement each item.*
