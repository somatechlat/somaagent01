# SomaBrain Integration Guide

Date: 2025-11-03

This document describes how SomaAgent01 integrates with SomaBrain across memory, recall, persona, policy, and ops. It covers API contracts we honor, runtime behaviors, and operator endpoints.

## Overview

- Client: `python/integrations/somabrain_client.py` (re-exported via `integrations/somabrain.py`) implements spec-compliant calls with defensive fallbacks and metrics.
- Runtime: Conversation Worker enriches memory writes with persona metadata; Gateway performs write-through when configured.
- Policy: Gateway evaluates OPA and (when configured) OpenFGA; decision receipts are recorded to the audit store.
- Ops: Admin endpoints expose SomaBrain memory metrics and migration (export/import) passthroughs.

## API Contracts

- remember: POST `/memory/remember`
  - No `coord` in the request (spec). Deterministic keys via payload/idempotency hashing.
  - Universe is set via `metadata.universe_id` or client default `SOMA_NAMESPACE`.
- recall: POST `/memory/recall`
  - Prefer `?payload=<json>` query param. Fallback to JSON body. Legacy `/recall` fallback supported.
- recall stream: POST `/memory/recall/stream`
  - SSE-style event iterator. Prefer `?payload=<json>` first.
- persona: GET/PUT/DELETE `/persona/{id}` with ETag/If-Match semantics.
- constitution + OPA policy: `/constitution/*`, `/opa/policy` supported by the client and CLI.
- ops: `/memory/metrics`, `/migrate/export`, `/migrate/import`.

## Persona-aware Memory Metadata

File: `services/conversation_worker/main.py`

- New helpers with TTL cache:
  - `_get_persona_cached(persona_id)`: fetches persona from SomaBrain and caches for `SOMABRAIN_PERSONA_TTL_SECONDS` (default 10s).
  - `_augment_metadata_with_persona(meta, persona)`: adds `persona_name`, `persona_updated_at`, and `persona_tags` (up to 8).
- Applied to both user and assistant memory writes in the Conversation Worker.
- Fail-safe: if persona fetch fails, enrichment is skipped; core behavior unchanged.

## Gateway Admin Endpoints

File: `services/gateway/main.py`

- GET `/v1/admin/memory/metrics`
  - Params: `tenant` (required), `namespace` (default `wm`)
  - Authorization: admin scope required; optional admin rate limiting.
  - Proxies SomaBrain `/memory/metrics`.

- POST `/v1/admin/migrate/export`
  - Body: `{ include_wm: bool = true, wm_limit: int = 128 }`
  - Authorization: admin scope required; rate limited.
  - Proxies SomaBrain `/migrate/export`.

- POST `/v1/admin/migrate/import`
  - Body: `{ manifest: object, memories: object[], wm?: object[], replace?: bool }`
  - Authorization: admin scope required; rate limited.
  - Proxies SomaBrain `/migrate/import`.

## Policy Decision Receipts

File: `services/gateway/main.py`

- `_evaluate_opa(...)` now returns a decision receipt `{ allow, url, status_code, decision }` and blocks on deny.
- `authorize_request(...)` emits an audit event `auth.decision` with:
  - OPA receipt (or `skipped` when OPA is disabled)
  - OpenFGA enforcement result `{ enforced: bool, allowed?: bool }`
  - `tenant`, `subject`, `scope`, request path, IP, user-agent
- Logging is best-effort; failures to write audit events do not impact the request flow.
- OpenFGA behavior in dev/unit contexts: if not configured (missing `OPENFGA_STORE_ID`), enforcement is skipped but a receipt is still emitted with `enforced=false`.

### Metrics

- `gateway_auth_opa_decisions_total{outcome}`: OPA policy outcomes
  - outcomes: `allow`, `deny`, `skipped`, `error`
- `gateway_auth_fga_decisions_total{enforced,outcome}`: OpenFGA outcomes
  - `enforced`: `true` or `false`
  - `outcome`: `allowed`, `denied`, `skipped`, `error`

## Constitution Pass-Through Endpoints (Gateway)

File: `services/gateway/main.py`

- `GET /constitution/version`: proxies SomaBrain version/metadata.
- `POST /constitution/validate`: proxies validation of a constitution document; post body forwarded verbatim.
- `POST /constitution/load`: proxies load of a constitution; after success, Gateway performs a best‑effort OPA policy regeneration via `POST /opa/policy`.

Auth & Policy
- All three routes require authentication and admin scope; OPA is evaluated with `{ action: "constitution.manage", resource: "somabrain" }` in the request context.
- Default OPA decision path: `/v1/data/soma/policy/allow` (override with `OPA_DECISION_PATH`).

## Audit Decision Receipts (Gateway)

- Gateway emits `auth.decision` audit events for every authorized request with structured details:
  - `details.opa`: `{ allow, url, status_code, decision }` or `{ skipped: true }` when OPA_URL is unset.
  - `details.openfga`: `{ enforced: true, allowed }` or `{ enforced: false, reason: "not_configured" }`.
  - `details.scope`: captured scope string (if any) from the JWT.

- Admin API to list recent decision receipts:
  - `GET /v1/admin/audit/decisions?tenant=&session_id=&request_id=&subject=&from_ts=&to_ts=&after=&limit=`
  - Returns `{ items: [ { id, ts, tenant, subject, resource, details, ... } ], next_cursor }`.
  - Requires admin scope when auth is enabled.

## Web UI (Admin) Wiring

The Web UI exposes lightweight admin tools wired to the endpoints above.

- Decisions Viewer
  - Open the left sidebar and click “Decisions” to launch the modal at `webui/components/admin/decisions.html`.
  - The grid lists recent `auth.decision` receipts fetched from `GET /v1/admin/audit/decisions` with filter fields (tenant, session_id, request_id, subject, from_ts, to_ts) and pagination via `next_cursor`.
  - Use “Export NDJSON” to download an NDJSON stream from `GET /v1/admin/audit/export?action=auth.decision` with the same filters applied, including the time range and subject.
  - Authorization: requires admin scope when `GATEWAY_REQUIRE_AUTH=true`. UI surfaces 401/403 as an inline banner.

- Constitution Tools
  - Click “Constitution” to open `webui/components/admin/constitution.html`.
  - Version: calls `GET /constitution/version` and shows the current SomaBrain constitution metadata.
  - Validate: paste a JSON document, posts `{ document: <json> }` to `POST /constitution/validate`.
  - Load: posts `{ document: <json> }` to `POST /constitution/load` and, on success, Gateway triggers an OPA policy regeneration (`POST /opa/policy`).
  - Authorization: admin scope required when auth is enabled; OPA decision path defaults to `/v1/data/soma/policy/allow`.

## Optional Semantics & Planning Hooks

File: `services/tool_executor/main.py`

- After successful tool result memory write, optional calls to SomaBrain `link` and `plan_suggest` are performed.
- Guarded by `SOMABRAIN_ENABLE_LINK_PLAN` environment flag; failures do not affect main flow.

## CLI Enhancements (where present)

- `scripts/constitution_admin.py` (if present)
  - Payload dual-shape for validate/load: `{ input: doc, document: doc }`
  - `load` triggers OPA policy regeneration via `POST /opa/policy`
  - New `status` command shows constitution version and OPA policy hash.

- `scripts/persona_admin.py` (if present)
  - Persona CAS CLI for GET/PUT/DELETE with ETag/If-Match support and conflict handling.

## Testing

- Unit tests added for admin endpoints:
  - `tests/unit/test_admin_somabrain_endpoints.py`
- Existing tests cover constitution CLI and persona CLI behaviors.
- Note: E2E tests require optional multimedia deps; unit tests cover new features without those deps.

## Configuration

- `SOMA_BASE_URL` default: `http://localhost:9696`
- `SOMA_NAMESPACE`: universe_id fallback; included in memory metadata.
- `SOMABRAIN_PERSONA_TTL_SECONDS`: persona cache TTL (default 10s)
- `GATEWAY_ADMIN_RPS`, `GATEWAY_ADMIN_BURST`: admin endpoint rate limit
- `OPA_URL`, `OPA_DECISION_PATH`: OPA location and decision entrypoint
- `OPENFGA_STORE_ID`: enable OpenFGA enforcement; when omitted, enforcement is skipped with a decision receipt

## Runbooks (brief)

- Metrics: `GET /v1/admin/memory/metrics?tenant=<id>&namespace=wm`
- Export: `POST /v1/admin/migrate/export` with `{ "include_wm": true, "wm_limit": 128 }`
- Import: `POST /v1/admin/migrate/import` with `{ manifest, memories, wm?, replace? }`

## Non-goals

- No local constitution storage or signing in this repo; all constitution concerns remain in SomaBrain.
- No RAG; retrieval is via SomaBrain recall endpoints only.
