# Code vs Docs Inconsistencies Audit (Nov 10, 2025)

Scope: Align all documentation with the current codebase, making the code the single source of truth. No runtime code changes were made.

## Summary of Fixes

- mkdocs nav indentation fixed for "UI Notifications" under Technical Manual.
- Monitoring doc updated:
  - Use env-driven metrics ports; Gateway default `GATEWAY_METRICS_PORT=8000`.
  - Replace generic `http_requests_total` with canonical metrics: `gateway_requests_total`, `gateway_request_duration_seconds`, `gateway_sse_connections`, `sse_messages_sent_total`.
  - Correct health endpoints: `/v1/health`, and root aliases `/ready`, `/live`, `/healthz`.
- Somabrain integration doc corrected:
  - Client path is `python/integrations/somabrain_client.py` (aliased by `integrations/somabrain.py`).
  - Mark CLI scripts as "if present" rather than guaranteed.
- Settings routes doc corrected:
  - `POST /v1/llm/test` noted (internal token required).
  - Removed legacy `POST /v1/ui/settings/credentials`; use sections flow only.
- User Installation doc updated:
  - Replace external Docker image quick start with `make dev-up` based workflow.
  - Clarify `.env` usage is optional and not for provider secrets.
  - Remove duplicate UI port row; confirm UI under Gateway `/ui` in dev.
- Root README updates:
  - Remove DeepWiki badge; point to local docs.
  - Strengthen single settings surface statement; remove legacy helper script.
  - Remove parity/baseline Playwright section and external capture server refs.
  - Replace Docker image quick start with local stack quick start.
  - Correct UI access to `http://localhost:${GATEWAY_PORT:-21016}/ui`.

## Notable Inconsistencies Found

1) Parity tests and baseline UI references (README) pointed to non-existent `webui/tests/ui` and external capture server at :7001.
   - Action: Removed section; clarified local UI access only.

2) Docker quick start referenced `agent0ai/agent-zero` image.
   - Action: Replaced with Makefile-driven local stack instructions.

3) Monitoring ports table claimed static ports; code uses env-driven ports and Gateway default 8000.
   - Action: Document env-driven behavior; list observed defaults; fix health paths.

4) Somabrain client path incorrect in docs.
   - Action: Corrected to `python/integrations/somabrain_client.py` and noted re-export.

5) Settings credentials POST endpoint documented but not implemented.
   - Action: Removed; direct to `/v1/ui/settings/sections` flow only.

## Items Reviewed vs Code

- Gateway endpoints verified in `services/gateway/main.py`:
  - `/v1/health`, `/ready`, `/live`, `/healthz`
  - `/v1/session/{session_id}/events` (SSE)
  - `/v1/llm/invoke`, `/v1/llm/invoke/stream`, `/v1/llm/test`
  - `/v1/ui/settings*` (get/put/sections/credentials)
  - Admin: `/v1/admin/memory/metrics`, `/v1/admin/migrate/export`, `/v1/admin/migrate/import`, `/v1/admin/audit/decisions`
- Runtime config facade in `services/common/runtime_config.py` reflected accurately; centralization language in README limited strictly to provider credentials and profiles.
- Metrics names validated against `observability/metrics.py` and gateway collectors.

## Open Gaps (left as-is, code-first truth)

- The repo still contains legacy Agent Zero marketing content and historical changelog sections. These are not functionally incorrect but are non-authoritative for SomaAgent01 specifics.
- Extensive `os.getenv` usage remains across services for infrastructure configuration. Docs now avoid claiming full env centralization beyond credentials/profiles.

## Verification

- mkdocs.yml now parses the Technical Manual nav correctly.
- Documentation pages reference only endpoints and files present in the codebase.

## Next Steps (optional)

- If desired, streamline README branding to focus solely on SomaAgent01 and link into the mkdocs site structure.
- Add a docs page enumerating `*_METRICS_PORT` env vars per service by reading defaults from each service entry point.
