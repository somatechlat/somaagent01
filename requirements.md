# SomaAgent01 — Requirements Addendum (Transactional Integrity & Explainability)

**Date:** 2025-12-20  
**Scope:** Whole agent (gateway, workers, tool executor, A2A, multimodal, uploads)  
**Goal:** Enterprise-grade rollback and explainability for every operation (DB, Kafka, external APIs, auth/login), aligned with Temporal-based orchestration.

## RQ-TX-001 — ACID per datastore
- All Postgres mutations MUST be wrapped in explicit transactions; failures roll back automatically. No partial commits.
- Redis is cache-only; state must be reconstructable if a Redis write is lost or reversed.

## RQ-TX-002 — Cross-service rollback via Sagas
- Every workflow step MUST define a compensation step; failures/cancels trigger compensations in reverse order.
- Workflow/activity IDs and idempotency keys MUST be deterministic to allow safe retries and dedupe.

## RQ-TX-003 — Outbox & messaging integrity
- Side effects to Kafka MUST use outbox or equivalent: DB commit + event publish are coupled; compensations emit void/tombstone events when needed.
- Kafka producers MUST be idempotent; message keys must be deterministic (request/session/workflow IDs).

## RQ-TX-004 — Auth/Login atomicity
- Session/token issuance MUST occur only after the surrounding transaction commits; failed policy/2FA blocks MUST roll back all session artifacts.

## RQ-TX-005 — Explainability
- The system MUST expose a “describe run/failure” view that combines: Temporal history, saga/audit rows, last error, and compensations applied.
- Audit records MUST include: workflow_id, activity, correlation_id, tenant, actor, outcome, error, compensation_applied flag.

## RQ-TX-006 — Cancellation semantics
- User/operator cancel MUST map to Temporal cancel and run compensations; long-running activities must heartbeat for prompt cancellation.

## RQ-TX-007 — Observability for rollbacks
- Prometheus metrics MUST cover: compensations_total, rollback_latency_seconds, failure_reason counts; high rollback rate MUST feed degradation monitor.

## RQ-TX-008 — External side-effects
- Calls to irreversible external systems MUST be gated by pre-flight validation/OPA; if irreversibility is detected, earlier steps MUST remain uncommitted.

## RQ-TX-009 — Reconciliation
- A periodic reconciliation workflow MUST detect orphaned/unfinished compensations by comparing saga records, DB state, and Kafka outbox, and auto-heal or escalate.

## RQ-TX-010 — Secrets & policy
- OPA checks MUST execute before side effects. Secrets MUST be fetched inside activities (Vault/secret loaders) and NEVER serialized in workflow inputs, outputs, or logs.

## Messaging, Storage, Replication, Backup (cross-cutting)

### RQ-MSG-001 — Messaging durability
- Kafka producers MUST be idempotent with acks=all and appropriate retries; consumers MUST be idempotent.
- Topic configs MUST be set for RF≥3 in prod; dev may use RF=1 with explicit note.
- Message keys MUST be deterministic (tenant/session/request/workflow ids) to ensure ordering and dedupe.

### RQ-UPL-001 — Upload/asset safety
- Uploads MUST write metadata first, then binary; failures MUST leave no orphaned metadata without tombstone.
- Assets MUST support delete/tombstone compensations; checksum dedupe required.
- Large objects SHOULD live in object storage (S3/MinIO); DB holds metadata only.

### RQ-REP-001 — Data replication & backups
- Postgres prod MUST be deployed HA with WAL archiving and PITR; nightly validated backups; restore tests quarterly.
- Redis prod MUST be clustered/sentinel; caches are reconstructable; session data MUST survive single-node loss.
- Kafka data MUST be replicated across AZs (RF≥3) with rack-aware placement in prod.

### RQ-OBS-002 — Degradation-aware ops
- Backups, compactions, reindexing, and bulk exports MUST run under Temporal workflows with rate limits and compensations (pause/resume) to avoid impact on live traffic.

### RQ-AUD-001 — Audit coverage
- All state-changing operations (DB, Kafka publish, asset create/delete, auth/login) MUST emit structured audit events with correlation_id and workflow_id.

## Deployment Resource Envelope (Dev with Prod Parity)

### RQ-DEP-015 — 15 GB RAM budget
- Entire dev stack (all containers) MUST respect a 15 GB total memory limit; per-service `mem_limit`/`mem_reservation` MUST be set to fit within this budget with headroom for Docker overhead.
- CPU/GPU profiles MUST be declared per capability; GPU devices stay disabled unless explicitly enabled via capability registry flags.

### RQ-DEP-016 — Production-grade settings in dev
- Dev compose/helm MUST mirror prod hardening (health probes, restart=always, pinned images/tags, read-only fs where possible, non-root users, ulimits, circuit breakers, TLS between services where supported).
- Persistent volumes MUST be defined for Postgres, Kafka/ZooKeeper, Redis, Temporal, ClamAV signatures, and attachment storage; temp scratch paths MUST be tmpfs.

### RQ-DEP-017 — Enforcement & observability
- Resource limits MUST be validated in CI with `docker compose config` + lint to ensure no service exceeds the 15 GB budget; Prometheus must scrape cgroup memory/cpu per container to enforce the envelope.
- Degradation monitor MUST factor “out-of-budget” conditions into capability health to prevent model/tool selection that would breach the budget.

## End-to-End Flow Integrity (Learning, Multimodal, Speed)

### RQ-FLOW-018 — Correlated lineage everywhere
- Every hop (gateway event log, Kafka message, Temporal workflow/activity, tool execution, SomaBrain memory) MUST carry `workflow_id`, `event_id`, `session_id`, `tenant`, `persona`, `capsule`, `capability_id`, `selection_id`, and `policy_id`; audit/describe views MUST reconstruct a single trace without extra joins.

### RQ-FLOW-019 — Multimodal ingest with derived artifacts
- For any attachment (image/audio/video/doc), ingest path MUST create hash-deduped metadata, run AV scan, and produce derived artifacts (transcript for audio/video, OCR/vision summary for images, text summary for docs). All artifacts are referenced (not duplicated) in SomaBrain `remember` payloads.

### RQ-FLOW-020 — Intent/policy-driven selection only
- No hardcoded model/tool IDs. Selector MUST use capability registry + OPA to pick/rank providers based on intent, modalities, tenant/persona/capsule, latency/cost hints, and health/degradation; decisions cached to keep added latency < 5 ms P95.

### RQ-FLOW-021 — Latency budget with streaming
- End-to-end chat P95 (text-only) ≤ 2 s; vision ≤ 5 s; TTS start ≤ 800 ms. SSE/WS streaming MUST begin as soon as first token/audio chunk is ready; no buffering for full responses.

### RQ-FLOW-022 — Async-first, zero blocking fan-ins
- Gateway and workers MUST remain async; no sync SomaBrain calls or blocking file reads on hot paths. Temporal activities MUST heartbeat; fan-in steps MUST stream partial results when possible.

### RQ-FLOW-023 — Mandatory memory + feedback
- After every user/assistant/tool/A2A step, system MUST call SomaBrain `/remember` with full provenance and `/context/feedback` with quality/latency/cost; adaptation state MUST be fetched and applied on next selection for that workflow/session.

### RQ-FLOW-024 — Tenant/persona/capsule enforcement
- All flows (ingest, selection, tool use, memory read/write, provenance lookup) MUST call OPA with tenant/persona/capsule context; unauthorized paths must fail fast before side effects.

### RQ-FLOW-025 — Decision trace UX
- API and UI MUST expose a concise “Decision Trace” per message: chosen capability/model, fallback reason, cost/latency, health state, and memory/feedback status. No verbose logs shown to end users.

### RQ-FLOW-026 — Degradation-aware fallbacks
- Degradation monitor MUST feed selector; if a provider is unhealthy or over budget, selector MUST choose an allowed fallback and record `fallback_reason`. No silent downgrades.

### RQ-FLOW-027 — Attachment hygiene and tombstones
- Attachments must be hash-deduped; deletes/tombstones must cascade to provenance and SomaBrain memories via compensations. Orphan detection/reconciliation MUST run periodically.

### RQ-FLOW-028 — Importance filtering without data loss
- Importance scoring may be LLM-assisted but MUST be policy-gated; low-importance items are still stored with minimal metadata + pointer, never dropped silently.

### RQ-FLOW-029 — Privacy & minimization
- PII/secret detection MUST run on ingest; retention/classification flags MUST be stored with memory records; redaction paths MUST be available via compensation/rollback.

### RQ-FLOW-030 — Health checks for multimodal providers
- Real health probes (latency, error rate, quota) for STT/TTS/Vision/Video providers MUST feed capability health; probes run out-of-band to avoid hot-path delays.

## Tool Registry, Selection, and Learning

### RQ-TOOL-031 — Unified capability registry for tools
- Tools MUST be represented in the same Capability Registry schema as models (provider, modalities, constraints, cost/latency SLOs, GPU/CPU profile, health, tenant/persona/capsule allowlists). No parallel registries.

### RQ-TOOL-032 — OPA-gated, intent-driven tool selection
- Tool invocation MUST flow through the selector + OPA (`tool.use`) with intent, modalities, tenant/persona/capsule, and capability health; direct ToolRegistry dispatch is forbidden. Selector returns `selection_id` and ranked candidates with reasons.

### RQ-TOOL-033 — Provenance and audit for every tool call
- Every tool execution MUST emit: workflow_id, event_id, session_id, tenant, persona, capsule, capability_id, selection_id, policy_id, tool version, inputs hash, outputs hash, latency, cost, quality_gate result. These fields must appear in audit, saga, and Decision Trace.

### RQ-TOOL-034 — Memory + feedback on tool outcomes
- Each tool call MUST persist a SomaBrain `remember` entry (inputs summary, outputs summary, artifacts refs) and a `/context/feedback` record (success/failure, quality, latency, cost). Adaptation state MUST influence future tool ranking per tenant/persona/capsule.

### RQ-TOOL-035 — Health and degradation awareness
- Active health probes per tool/provider feed capability health; degradation monitor can down-rank/disable failing tools. Selector MUST record `fallback_reason` when switching tools.

### RQ-TOOL-036 — Artifact hygiene for tool outputs
- Tool-generated assets must use the same attachments/provenance/tombstone rules: hash-dedupe, AV scan if binary, derive transcripts/OCR/summaries as applicable, and cascade deletes via compensations.

### RQ-TOOL-037 — Policy-scoped discovery
- Tool discovery endpoints/UI MUST filter by tenant/persona/capsule per registry allowlists; users/agents see only permitted tools. Capsules embed these permissions, and selector must honor capsule constitution constraints.

### RQ-TOOL-038 — CI enforcement
- CI lint/tests MUST fail if tool dispatch bypasses selector/OPA, if capability_id/selection_id/provenance fields are missing, or if hardcoded tool IDs are introduced.

## AgentIQ Governor (Capsule-Scoped Intelligence Governance)

### RQ-AIQ-050 — Governor insertion point
- AgentIQ Governor MUST run after policy gates and before any model/tool invocation, for every turn (chat, tool, A2A). It must remain async and add ≤50 ms p95 decision latency.

### RQ-AIQ-051 — Dual scoring (AIQ_pred, AIQ_obs)
- Compute AIQ_pred pre-call using lane budgets, tool K, degradation level, digest faithfulness risk; compute AIQ_obs post-call from latency, tool success, verifier/schema validity, retries, and policy events. AIQ_obs computation MUST be offloaded so user-facing latency is unaffected.

### RQ-AIQ-052 — Lane/backpressure and buffer
- Prompt assembly MUST use lane plans (system/policy/tools/history/memory/attachments/tool-results/buffer). Buffer lane ≥200 tokens (configurable per provider). Backpressure actions (reduce K, compress, summarize, lower disclosure level, degrade) MUST execute deterministically until within budget.

### RQ-AIQ-053 — Capsule-scoped Top-K tool governance
- Tool discovery MUST be capsule-scoped (allowed/prohibited lists, tenant/persona/capsule allowlists) before Top-K. Progressive tool disclosure ladder (names → desc → minimal schema → full schema) MUST be chosen based on AIQ_pred, pressure, and degradation. Selector MUST return margin; low-margin results increase K or request disambiguation.

### RQ-AIQ-054 — DigestFaithfulness controls
- Any digest/summary injected in place of raw content MUST retain anchors (IDs, codes, numbers, dates, units), include short excerpts for high-risk regions, and carry faithfulness metadata; faithfulness must down-weight RetrievalIQ and surface “lossy view” warnings in UI/Decision Trace.

### RQ-AIQ-055 — Degradation ladder
- Support levels L0–L4 (Normal→Tighten→Conserve→Minimal→Safe). Downshifts and recoveries MUST be deterministic, logged, and included in AIQ scoring and Decision Trace; fallbacks must stay within capsule/policy bounds.

### RQ-AIQ-056 — RunReceipt and retention
- Every turn MUST emit a RunReceipt with: evictions/compressions, tool selection (Top-K, margin), degradation level, lane budgets/usage, digest faithfulness, latency, tool success, policy events. Retention/TTL policies configurable per class (full vs compact), with sampling for low-risk turns.

### RQ-AIQ-057 — Settings and tuning
- All AIQ weights/penalties, thresholds, lane budgets, buffer size, disclosure levels, degradation transitions, and retention policies MUST be live-tunable via UI Settings Store (scopes: global/tenant/persona/session) without redeploy. Secrets remain in Vault.

### RQ-AIQ-058 — QA/chaos coverage
- Provide regression/chaos suites: 100–1000 tools, Top-K/disclosure correctness, degrade transitions under token pressure, retry on provider length errors. Fail builds if AgentIQ invariants (buffer, disclosure, degradation) break.

### RQ-AIQ-059 — Simplicity guardrails (Elegance Pass)
- AgentIQ v1 MUST run in-process (no new services) with exactly two modes: Fast Path (cheap: capsule filter, small K, fixed lane ratios, trim/dedupe only) and Rescue Path (invoked on backpressure/degradation ≥L1: progressive disclosure, summarization/compaction, optional compressor). Governor decision remains ≤50 ms p95.
- Implementation MUST be limited to four primitives: ConfigResolver, Governor (budgets + mode), ToolSelector (capsule-scoped hybrid Top-K), Recorder (stats/receipts). Data objects are only ContextPlan, BuiltContext, AgentIQRecord.
- Receipts default to compact; full receipts only when AIQ_obs below threshold, policy deny, tool failure, or provider rejection. Receipts store hashes/pointers, not blobs.
## Confidence Score Extension (SRS-CONF-2025-12-16)

### RQ-CONF-060 — Provider logprobs capture
- LLM wrappers MUST request token-level logprobs when supported; expose standardized `tokens` + `token_logprobs` arrays guarded by `confidence.enabled`.

### RQ-CONF-061 — Normalized confidence scalar
- Implement `calculate_confidence(logprobs, aggregation)` with modes {average|min|percentile_90}; normalize via exp(mean or chosen agg); clamp to [0,1]; return null when no valid logprobs; default precision 3 decimals (transport only).

### RQ-CONF-062 — API surface
- All public responses that include model output MUST add `confidence: float|null` when enabled; streaming sends final frame with confidence; legacy clients remain compatible (additive field).

### RQ-CONF-063 — Persistence & events
- Events/audit/feedback stores MUST persist only the scalar confidence (no token logprobs); additive schema change; include tenant_id/request_id/model/endpoint for auditability.

### RQ-CONF-064 — Thresholds & gating
- Runtime-configurable: `min_acceptance`, `on_low` {allow|flag|reject}, `treat_null_as_low`; low-confidence decisions MUST integrate with OPA input (`input.confidence`, `confidence_enabled`).

### RQ-CONF-065 — Observability
- Prometheus metrics: confidence avg/EWMA, histogram, missing count, rejected count (labels limited to tenant/model/endpoint); structured logs include confidence, mode, duration; no raw logprobs in logs.

### RQ-CONF-066 — Performance & reliability
- Added overhead ≤5 ms warm / ≤10 ms cold; confidence computation failure MUST NOT abort responses (fallback to null).

### RQ-CONF-067 — Rollout & compatibility
- Feature-flagged; enablement steps: off → staging allow → prod flag/reject per tenant; OpenAPI minor version bump only.
## Resilience, Backups, Secrets, and Memory Queues

### RQ-BCK-039 — Backups and restore paths
- Postgres (agent + attachments + registry) MUST support PITR with WAL archiving and quarterly restore drills; Kafka topics retain ≥7 days in dev, ≥14 days in prod with documented replay; SomaBrain memory store must expose backup/restore compatible with these RPO/RTO targets.

### RQ-BCK-040 — Durable memory/event queues
- Conversation/tool/A2A events and memory writes MUST be durably logged (outbox + Kafka) with deterministic keys (session_id/workflow_id) to preserve order; DLQ and replay MUST be available per topic; idempotent consumers are required for all workers.

### RQ-RES-041 — Failsafe and reconciliation
- Periodic reconciliation workflows MUST compare saga/audit/outbox vs datastore state to repair orphans (attachments, provenance, SomaBrain memories) and re-trigger compensations; circuit breakers must wrap all external dependencies (SomaBrain, model providers, storage).

### RQ-SEC-042 — Secrets and vault policy
- All provider keys, OPA tokens, SomaBrain creds, and Temporal auth MUST be sourced from Vault/secret manager at call time; no secrets in source code or baked into workflow inputs/history/logs; per-tenant/persona scoping and short TTLs are mandatory.

### RQ-SEC-043 — PII/PHI minimization and redaction
- PII detection/redaction MUST run on ingest (context builder, uploads) before storage or outbound calls; failures must fail closed for regulated tenants and emit audit; retention/classification flags must travel with memories and attachments.

## Multimodal Model Selection & Permissions

### RQ-MM-001 — Capability Registry
- Maintain a registry of models/providers per modality (text, vision, audio STT, TTS, video, diagram) with attributes: max_size/ctx, latency_class, cost_tier, health, and availability windows.
- Registry entries include allowlists/denylists for tenants, roles, personas, and environments (dev/stage/prod).

### RQ-MM-002 — Intent-Driven Selection
- Model selection MUST be based on intent + modalities present (text, attachments mime, audio flags), tenant/persona, latency/budget hints, and provider health; NO hardcoded model names.
- Selector MUST provide a ranked set with reason codes and the chosen model; fallbacks are deterministic.

### RQ-MM-003 — Policy Enforcement
- `model.use` decisions MUST be checked against OPA/policy before invocation; unauthorized models MUST be rejected with an auditable denial.
- Secrets/keys for providers are fetched per-call via SecretManager; never baked into workflow inputs.

### RQ-MM-004 — Audit & Explainability
- Every selection MUST emit audit fields: workflow_id, session_id, tenant, persona, intent, modalities, chosen_model, provider, fallback_used, reason, and policy_decision.

### RQ-MM-005 — Health- & Degradation-Aware
- Selector MUST skip providers marked unhealthy/degraded by the degradation monitor unless explicitly forced via dev override.
- Degradation monitor MUST track selection failures and surface metrics per modality/provider.

### RQ-MM-006 — Storage & Assets
- Asset type/format MUST be derived from mime/content-type or explicit task params; defaults are configurable in the registry, not hardcoded.
- Vision/audio/video steps MUST validate size/format against registry limits; reject or downsample per policy.

### RQ-MM-010 — Mandatory Memory Capture
- Every interaction (user input, LLM response, tool result, generated asset) MUST be persisted to SomaBrain with workflow_id, tenant/persona/capsule, modality, asset refs, provenance (provider/model/tool, cost, latency), and policy metadata (classification, retention).
- Multimodal memories must include derived transcripts/summaries and link all assets (original + derived) as references, not blobs.

### RQ-MM-011 — Feedback & Adaptation Loop
- Each stored memory MUST trigger `/context/feedback` with success/failure, quality, provider/model, latency, cost, workflow_id, tenant/persona/capsule; Selector MUST ingest `/context/adaptation/state` to bias future choices.

### RQ-MM-012 — Consistency & Compensations
- All SomaBrain writes must include workflow_id/correlation_id; compensations/tombstones must remove or redact associated SomaBrain entries and assets together.

### RQ-MM-013 — SomaBrain Settings in Agent UI
- Agent UI settings MUST expose SomaBrain configuration (base URL, timeouts, retries, circuit settings, namespace/tenant selection, feature flags, adaptation controls, retention/classification defaults).
- Per-tenant/persona/capsule toggles for memory capture, feedback reporting, adaptation enable/disable, and retention must be configurable in UI and persisted.
- Health/status of SomaBrain integration (latency, error rate, breaker state) must be visible in UI settings.

### RQ-MM-014 — Single Client Surface
- Use the async SomaBrain client with current endpoints (`/context/evaluate`, `/context/feedback`, `/context/adaptation/state`, `/memory/*`, `/plan/*`, `/persona/*`, `/constitution/*`); legacy sync helpers must be removed or updated.
