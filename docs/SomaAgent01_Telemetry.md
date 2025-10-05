⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Telemetry & Cost Accounting

## Purpose
SomaAgent 01 must expose precise, real-time telemetry—especially token spend, latency, reliability, and audio quality—so operators can manage budgets, enforce policy, and continuously improve personas. This document defines what we track, how data flows through the system, and how it powers dashboards, budgets, and model decisions.

## Metrics Captured
- **Model Usage**
  - Input tokens, output tokens, total tokens.
  - Latency (p50, p95, p99), queue delay, GPU utilization.
  - Model ID, persona ID, tenant, role, deployment mode, cost estimation (derived from token/GPU rates).
- **Escalation LLM Tier**
  - Decision reason, source SLM analysis snapshot, router metadata.
  - OSS model ID, base URL, latency, token mix, per-call cost estimate.
  - Success vs. fallback/error counts for high-risk escalations.
- **Tool Execution**
  - Duration, success/failure, exits, stdout/stderr size, attachments.
  - Policy verdicts (allow, warn, block, override).
- **Conversation**
  - Turn count, streaming duration, requeue counts, interrupts.
- **Audio**
  - Word error rate (WER), character error rate (CER), MOS-LQO, RMS energy, latency from microphone to response.
- **Policy & Security**
  - Number of blocks, overrides, policy latency, constitution hash references.

## Data Flow (OSS Components)
1. **Producers**
  - Conversation Worker emits `slm.metrics`, `llm.escalation.metrics`, `conversation.metrics`, `policy.events` to Kafka.
   - Tool Executor emits `tool.metrics`.
   - Audio Service emits `audio.metrics`.
2. **Streaming & Storage**
  - Kafka topics ingested into ClickHouse (`slm_metrics`, `escalation_metrics`, `tool_metrics`, `conversation_metrics`, `audio_metrics`).
   - Redis maintains rolling totals for budget checks.
   - Postgres stores per-session summaries for quick UI access.
3. **Dashboards & Alerts**
   - Prometheus-backed dashboards show live spend, latency, refusal rate, audio quality.
   - Alertmanager warns on threshold breaches (token budget, refusal spike, audio failures).
4. **Exports & Billing**
  - Scheduled jobs export CSV/Parquet for finance (per tenant/persona/model).
  - APIs (`GET /v1/telemetry/tokens`, `/budget/summary`) allow external systems to consume data.

## UI Integration
- Session workspace displays cost per response and cumulative session totals.
- Model control panel shows average cost/latency per profile with trend indicators.
- Operator dashboard highlights top personas by spend, anomalies, and upcoming budget thresholds.
- Notifications trigger when a model escalation occurs (e.g., “Upgraded to Llama 70B for this response—estimated +$0.12”).

## Budget Enforcement
- Configure per-tenant and per-persona budgets (daily/monthly token limits, GPU hours).
- Policy client checks budgets before executing expensive actions; can downgrade models, pause sessions, or escalate for approval.
- Redis stores rolling counters; budgets reset via cron or manual override.

## Model Selection Feedback Loop
- Scoring job consumes telemetry to compute (quality, cost, latency, reliability) and updates model rankings.
- Conversation Worker consults scoring + budget to choose models on the fly (e.g., stay on Mixtral unless task complexity > threshold).
- Telemetry also feeds anomaly detection (unexpected latency spikes, accuracy drift) that can trigger automatic fallback or human review.

## Implementation Tasks
1. Instrument the managed Soma SLM API client, Whisper, and tool executor to emit metrics to Kafka with JSON Schema validation.
2. Set up ClickHouse tables + materialized views for cost aggregation.
3. Build UI components displaying metrics in session view, admin dashboards, and alerts.
4. Implement budget enforcement hooks in policy client and model selector.
5. Define export pipelines and integration tests ensuring telemetry is captured end-to-end with no mocks.

## Alerts
- `TelemetryWorkerDown`: fires when Prometheus fails to scrape the telemetry worker for more than one minute (see `infra/observability/alerts.yml`).
