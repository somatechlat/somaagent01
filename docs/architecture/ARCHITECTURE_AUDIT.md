# SomaAgent01 — Architecture Audit Log (Living Document)

**Date:** 2025-12-20  
**Purpose:** Track deep-dive coverage while migrating to Temporal and enforcing full rollback/explainability. This file is append-only and records what has been audited and what remains.

## Coverage Map (in progress)

- LLM call path:
  - ✅ Gateway providers → `LLMAdapter` wiring (env-based base_url/api_key, SecretManager entry point)
  - ✅ Fixed `_build_url` indentation in `services/common/llm_adapter.py` (was blocking import).
  - 🔜 Trace conversation worker call-sites and model selection; verify token/usage metrics.
  - ✅ Integrate SecretManager per-call API key resolution in LLMAdapter; tool_executor now uses SecretManager for OpenAI key.
  - ✅ Added LLM success/failure metrics recording in `GenerateResponseUseCase` (tokens + latency).
  - ✅ Gateway now instantiates LLMAdapter with SecretManager resolver (no env-stale keys).
- Messaging:
  - ✅ Kafka bus creation in gateway/providers uses cfg settings; idempotency/outbox patterns to be enforced via Temporal plan.
  - ✅ Outbox added (services/common/outbox.py) and wired into DurablePublisher when SA01_USE_OUTBOX=true; rows retained on failure for retry.
  - ✅ DLQ now emits Prom metrics and can publish via outbox when enabled; still needs Temporal activity wrapping for rollback semantics.
- Describe/Explainability:
  - ✅ `/v1/describe/{session_id}` returns session events + saga entries + audit entries; optional workflow describe via Temporal host when workflow_id provided.
- Settings/Secrets:
  - ✅ SecretManager is the hook for LLM creds; verify no hardcoded secrets.
  - 🔜 Walk UI settings store and agent settings propagation to workers and feature flags endpoints (features.py).
- Uploads/Assets:
  - ✅ Reviewed `services/gateway/routers/uploads_full.py`: metadata-first, SHA256, ClamAV, Redis-backed TUS; needs compensations (delete/tombstone) and streaming scan handling.
  - ✅ AttachmentsStore now has explicit `delete()` API for compensations; next: wire Temporal delete/tombstone.
  - ✅ `services/common/asset_store.py` now includes `tombstone()` for soft delete; Temporal compensations must call delete or tombstone + audit event.
- Saga/State:
  - ✅ SagaManager schema/functionality reviewed; Temporal integration pending.
- Observability:
  - ✅ LLM metrics module reviewed; Prometheus-only plan captured in design.md.
  - 🔜 Add compensations/rollback metrics across services and workers.
## Immediate Defects / Risks

1. Temporal migration not yet wired across all runtime paths.
2. LLM call chain still needs end-to-end audit (gateway overrides, model selection, SSE, error handling) for rollback/audit readiness.
3. Compensation/rollback metrics not yet added across services.

## Next Audit Steps

1) Wire Temporal workflows/activities and update compose/config; retire remaining legacy task paths.  
2) Trace LLM call chain end-to-end and add rollback/error instrumentation.  
3) Add rollback/compensation metrics across services and workflows.  
4) Wire outbox usage into Temporal activities and add flush/retry on startup.  
5) Extend describe endpoint with Temporal history after workflows land.

## Notes
- Keep Prometheus-only observability (no Grafana).  
- All state-changing operations must emit structured audit with correlation_id/workflow_id.  
- Dev stack uses singletons; prod must follow HA/replication requirements captured in `requirements.md`.
