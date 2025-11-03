# Model & LLM Config Audit

Generated: 2025-10-30
Scope: repo-wide search for `model`, `base_url`, `model_profiles`, related env vars, and legacy UI/run artifacts.

Summary
- Purpose: collect every occurrence of model/profile settings and base_url usage so we can centralize them in Gateway and produce a migration plan.
- Method: repo-wide search for key tokens and inspection of representative files.

High-level findings
- Model profiles are seeded via `conf/model_profiles.yaml` and backed by `services/common/model_profiles.py` (Postgres table `model_profiles`). The code uses `MODEL_PROFILES_PATH` env override.
- Multiple services (Gateway, Conversation Worker, Tool Executor) reference gateway/base URLs and model settings via env vars and fallbacks. There are many hard-coded fallbacks throughout tests and scripts.
- Workers currently read `SLM_MODEL` and sometimes include `base_url` in overrides (conversation_worker, tools). Gateway exposes `/v1/llm/invoke` and `/v1/llm/invoke/stream` and contains normalization logic (`_normalize_llm_base_url`).
- Several legacy UI artifacts exist (`run_ui.py`, `tmp/webui/`, `deploy-optimized.sh`) and already archived copies are present in `archive/`.

Key files & excerpts (representative)
- `services/common/model_profiles.py`
  - Creates `model_profiles` table and has upsert/get/list/sync_from_settings logic.

- `services/common/settings_base.py` & `services/common/settings_sa01.py`
  - Default `model_profiles_path` set to `conf/model_profiles.yaml` and environment override `MODEL_PROFILES_PATH` used.

- `services/gateway/main.py`
  - Exposes `/v1/llm/invoke` and `/v1/llm/invoke/stream` endpoints.
  - Reads `SOMA_BASE_URL` fallback and contains normalization logic and model/profile handling.

- `services/conversation_worker/main.py`
  - Worker uses `WORKER_GATEWAY_BASE` env var and calls Gateway invoke endpoints. Multiple locations form URLs like `{self._gateway_base}/v1/llm/invoke/stream`.
  - Worker reads `SLM_MODEL` fallback and sometimes constructs slm_kwargs including `model` and `base_url`.

  

- `webui/` and `webui/playwright.config.ts` and tests
  - Many tests and Playwright configs read `WEB_UI_BASE_URL`, `BASE_URL`, or derive from `GATEWAY_PORT`.

- `.env.example`
  - Contains `GATEWAY_BASE_URL` and `WEB_UI_BASE_URL` templates and `SLM_MODEL` default.

- `docker-compose.yaml`
  - Sets `WORKER_GATEWAY_BASE` to `http://host.docker.internal:${GATEWAY_PORT:-21016}` and `SLM_MODEL` environment mapping.

Concrete search hits (representative; not exhaustive)
- `GATEWAY_BASE_URL` referenced in: `docs/roadmap/canonical-roadmap.md`, `.env.example`, `scripts/e2e_quick.py`, `docs/user-manual/quick-start-tutorial.md`, tests under `tests/e2e` and `tests/playwright`.
- `WEB_UI_BASE_URL` referenced in: `.env.example`, `webui/playwright.config.ts`, `scripts/ui-smoke.sh`, many tests.
- `WORKER_GATEWAY_BASE` referenced in: `services/conversation_worker/main.py`, `services/tool_executor/tools.py`, `docker-compose.yaml`, tests that monkeypatch it.
- `MODEL_PROFILES_PATH` appears in `services/common/settings_sa01.py` and `services/common/settings_base.py`.
- `SLM_MODEL` appears in `.env.example`, `services/common/slm_client.py`, `services/conversation_worker/main.py`, and `docker-compose.yaml`.
- `/v1/llm/invoke` and `/v1/llm/invoke/stream` are in `services/gateway/main.py` and called from the worker.

Immediate issues to address (priority)
1. Empty or inconsistent `base_url` values in profiles: Gateway runtime settings reported `model_profile.base_url = ""` for the `dialogue` profile in DEV. This must be fixed by normalizing profiles and ensuring provider detection works for profiles with empty base_url.
2. Workers currently send `base_url` overrides in requests; they must stop and rely on Gateway resolution to avoid normalization conflicts.
3. Many tests and scripts still use hard-coded port/URL fallbacks — standardize on `GATEWAY_BASE_URL`/`WEB_UI_BASE_URL` to avoid divergence.
4. Legacy UI artifacts and `run_ui.py` references remain in docs/tests/Makefile — ensure these references are updated or removed now that `run_ui.py` is archived.

Recommendations / next steps
- Sprint 0 (immediate): finish this audit (this document), update `.env.example` with canonical vars (if not already), and archive legacy files (done for `run_ui.py` and `deploy-optimized.sh` but cross-check references). Marked tasks in the tracker.
- Sprint 1: implement Gateway CRUD for model profiles, centralize normalization rules, add `GATEWAY_MODEL_LOCK=warn` to detect worker overrides, and add `/v1/llm/test` to validate provider connectivity.
- Sprint 2: update workers to omit `base_url` in overrides and run migration scripts to copy profiles and credentials into Gateway.
- Add unit tests for normalization and integration tests for invoke/stream flows before flipping `GATEWAY_MODEL_LOCK` to `enforce`.

Planned artifacts I will create next
- `docs/audits/model_config_audit.md` (this file) — complete.
- `scripts/migrate_profiles_to_gateway.py` — migration helper (next sprint).
- `services/gateway/openapi_model_profiles.yaml` — API contract for profiles (Sprint 1).

If you'd like, I can now:
- (A) Run a focused script to print current Gateway runtime `model_profiles` via HTTP (`/v1/ui/settings`) and gather the exact JSON (requires Gateway up; dev stack is running), or
- (B) Start implementing the Gateway `/v1/model-profiles` CRUD endpoints immediately (no mocks) and accompanying unit tests.

Next immediate action I recommend: fetch runtime Gateway `GET /v1/ui/settings` and list Postgres `model_profiles` rows (if DB access is allowed) so we can plan the migration script precisely. Let me know which you'd prefer and I'll proceed.
