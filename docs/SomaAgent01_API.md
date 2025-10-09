⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real servers real data.

# SomaAgent 01 Gateway API (Sprint 1 Baseline)

The Gateway exposes SomaAgent’s public HTTP/WebSocket surface. This document captures the sprint‑1 hardening state and callouts for the security and observability layers that now ship by default.

## Base URL & Versioning
- **Local URL:** `http://localhost:8010`
- **Versioning:** All documented endpoints live under `/v1`. Legacy aliases (`/health`, `/capsules`, …) remain for backward compatibility but are excluded from the OpenAPI schema.
- **Version header:** Every successful response includes `X-API-Version: v1` (override via `GATEWAY_API_VERSION`).
- **Schema:** `GET /openapi.json` returns the cached OpenAPI v3 document generated from FastAPI at boot. The canonical versioned path is `/v1/openapi.json`.

## Security Overview
- **JWT authentication** – Enabled when `GATEWAY_REQUIRE_AUTH=true`. The gateway loads signing material from environment variables or HashiCorp Vault (`GATEWAY_JWT_VAULT_*`). Requests without a valid token receive `401`.
- **OPA policy evaluation** – If `OPA_URL` is configured, every authorised request is checked against Rego policies. Policy denials return `403` and emit structured warning logs.
- **OpenFGA enforcement** – Tenancy is determined from configured JWT claims (`GATEWAY_JWT_TENANT_CLAIMS`). OpenFGA checks prevent cross‑tenant access, returning `403` for denials.
- **Audit logging** – Auth failures, Vault issues, and policy denials are logged through the `gateway` logger with structured context for SIEM ingestion.

## Core Endpoints

### `GET /v1/health`
Returns a JSON payload summarising Postgres, Redis, Kafka, and optional HTTP dependency status. Useful for Kubernetes/Docker probes.

### `GET /v1/openapi.json`
Returns the full OpenAPI v3 schema. The same payload is mirrored at `/openapi.json` for tooling compatibility.

### `POST /v1/session/message`
Enqueue a user message. Payload:

```json
{
  "session_id": "optional-session-id",
  "persona_id": "optional-persona-id",
  "message": "User message text",
  "attachments": ["s3://..."],
  "metadata": {"tenant": "acme"}
}
```

- Kafka topic: `conversation.inbound`
- Redis cache: writes persona/tenant context via `session:{id}:meta`
- Postgres: appends event to session envelope store for replay/audit
- Response sample:

```json
{
  "session_id": "generated-or-provided",
  "event_id": "uuid"
}
```

### `POST /v1/session/action`
Triggers a predefined quick action (`summarize`, `next_steps`, `status_report`). Behaves like `/v1/session/message` but stamps metadata with the action name.

### `GET /v1/session/{session_id}/events`
Server-Sent Events (SSE) stream of outbound conversation updates. Provides a browser-friendly alternative to WebSockets.

### `WebSocket /v1/session/{session_id}/stream`
Realtime streaming for session responses. Streams JSON envelopes carrying `event_id`, `session_id`, `persona_id`, `role`, `message`, and `metadata`.

### Capsule Registry Proxies
- `GET /v1/capsules` – Lists capsules from the upstream registry.
- `GET /v1/capsules/{capsule_id}` – Downloads a capsule bundle.
- `POST /v1/capsules/{capsule_id}/install` – Triggers capsule installation.

Errors from the registry are proxied with the upstream status code; connectivity issues surface as `502`.

## Kafka Topics
| Topic | Producer | Consumer | Payload |
|-------|----------|----------|---------|
| `conversation.inbound` | Gateway | Conversation Worker | `{event_id, session_id, persona_id, message, attachments, metadata}` |
| `conversation.outbound` | Conversation Worker | Gateway | `{event_id, session_id, persona_id, role, message, metadata}` |

Trace context is injected into Kafka headers so downstream workers maintain OpenTelemetry spans automatically.

## Persistence & State
- **Redis:** stores hot session metadata (`session:{id}:meta`).
- **Postgres:** `session_events` table keeps ordered JSON envelopes for timeline replay. Helper utilities live in `services/common/session_repository.py`.

## Error Handling
- `401` – Missing/invalid JWT when auth is required.
- `403` – Policy or OpenFGA denials.
- `502` – Kafka publish failures or capsule registry connectivity issues.
- WebSocket closes with code `1011` on unexpected stream failures.

## Related Tooling
- **CI:** `.github/workflows/ci.yml` runs Ruff + pytest on each PR.
- **Security tests:** `.github/workflows/security.yml` executes dependency scans and policy checks.
- **OpenAPI contract tests:** `.github/workflows/openapi_contract.yml` ensures the schema remains stable.
- **Observability:** `docs/monitoring_quickstart.md` covers Prometheus alerts; OTLP/Trace helpers live in `services/common/tracing.py`.

## Known Follow-ups
- Expand documentation to cover the `/v1/models`, `/v1/tools`, and API-key endpoints when they graduate from private preview.
- Attach sample JWT/OPA configuration snippets once the reference environment is public.
- Reintroduce a maintained Grafana dashboard pack once the observability stack is standardised again.
