# Settings & Credentials Routes Catalog (Canonical)

Date: 2025-11-09
Scope: Authoritative list of Gateway settings/credentials endpoints, purpose, method, auth/policy, and notes.

Legend
- Auth: require_auth? (Y/N), Policy gate via OPA/OpenFGA? (Y/N)
- Notes: short behavioral expectations; no secrets exposure rules

## Runtime-config and UI Settings

- GET `/v1/runtime-config`
  - Auth: N (safe boot hints)
  - Notes: Returns UI-safe config; no secrets; reflects SSE/uploads flags and tool counts.

- GET `/v1/ui/settings/sections`
  - Auth: N (read-only config for UI)
  - Notes: Normalized sections for SPA; source `UiSettingsStore`.

- POST `/v1/ui/settings/sections`
  - Auth: Y when `REQUIRE_AUTH` and OPA enabled (policy enforced)
  - Notes: Atomic write of UI sections, model profile upsert, and provider credential updates (keys prefixed `api_key_`). Emits masked audit diff and Kafka `config_updates` event.

## Model Profiles & LLM

- GET `/v1/llm/test` (if present)
  - Auth: Y (policy)
  - Notes: Connectivity test; returns validation result; no raw secrets.

- POST `/v1/llm/invoke` and `/v1/llm/invoke/stream`
  - Auth: Y (policy)
  - Notes: Gateway resolves model/provider/base_url; workers/clients do not send base_url.

## Credentials Surface

- GET `/v1/ui/settings/credentials` (if present)
  - Auth: Y (policy)
  - Notes: Returns presence and timestamps only; never raw secret values.

- POST `/v1/ui/settings/credentials` (if present)
  - Auth: Y (policy)
  - Notes: Stores/updates provider secrets (encrypted). Emits masked audit diff + events.

## Audit & Drift (planned)

- GET `/v1/config/drift` (planned M7)
  - Auth: Y (policy)
  - Notes: Compares registry/db/cache versions; returns status ok|warning|critical.

- GET `/v1/audit/settings` (planned)
  - Auth: Y (policy)
  - Notes: Returns masked diffs history for settings writes.

## Metrics (relevant names)
- `settings_read_total` – increments on settings reads.
- `settings_write_total` – increments on settings writes.
- `settings_write_latency_seconds` – histogram for write path.

## References
- Gateway: `services/gateway/main.py`
- Stores: `services/common/ui_settings_store.py`, `services/common/llm_credentials_store.py`, `services/common/model_profiles.py`
- Metrics: `observability/metrics.py`
- Audit schema: `schemas/audit/settings_write_diff.v1.schema.json`
