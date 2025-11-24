# Metrics Roadmap (Centralized, No Stubs)

## Objectives
- Full observability of chat pipeline (ingress → enrich → LLM → emit) in normal and degraded modes.
- Centralized, low-cardinality Prometheus metrics; no hardcoded values; reuse existing `/metrics` endpoints per service.
- Coverage for LLM usage, messages, sessions, backlogs, budgets/quotas, uploads, SSE, ops health.

## Scope & Services
- Gateway (HTTP ingress, SSE, uploads, sessions)
- Conversation Worker (Somabrain/LLM path, degraded bypass)
- Memory Replicator / Outbox / Publisher (Kafka/WAL)
- Tool Executor (LLM/tool calls)
- Optional Somabrain status probes (metrics only; no behavior change)

## Metric Set (Prometheus)
- **Traffic**
  - `chat_messages_in_total{role,source}` (gateway)
  - `sessions_created_total`, `sessions_deleted_total` (gateway)
  - `attachments_uploaded_total`, `attachment_upload_seconds` (gateway)
  - `sse_clients_gauge`, `sse_stream_errors_total{reason}` (gateway)
- **Latency**
  - `chat_enqueue_seconds` (gateway enqueue → WAL/Redis)
  - `context_build_seconds` (worker prompt build)
  - `llm_latency_seconds{model,provider,mode}` (worker/tool-executor)
  - `event_to_response_seconds` (user event → assistant emit)
  - `wal_publish_seconds`, `wal_consume_seconds` (publisher/consumers)
- **LLM Usage**
  - `llm_requests_total{model,provider,mode}` (mode=normal|degraded_bypass_somabrain)
  - `llm_tokens_total{model,provider,direction=in|out}`
  - `llm_errors_total{provider,code}`
- **Somabrain / Degradation**
  - `somabrain_calls_total{result}` (success|timeout|circuit_open|skipped)
  - `somabrain_bypass_total` (answered without Somabrain)
  - `circuit_state{component}` (gauge or enum as labeled gauge)
- **Backlog / Reliability**
  - `degraded_buffer_size` (Redis degraded:* keys)
  - `outbox_pending` (outbox rows)
  - `wal_publish_errors_total`, `redis_errors_total`, `kafka_errors_total`, `postgres_errors_total`
- **Budgets / Quotas**
  - `tenant_budget_tokens_allowed{tenant}`, `tenant_budget_tokens_used{tenant}`
  - `tenant_budget_tokens_overruns_total{tenant}`
  - (Optional) message-count budgets mirroring tokens
- **Ops / Health**
  - CPU/mem/disk gauges (gateway ops_status already partial)
  - `health_checks_total{component,result}`

## Implementation Plan (no new endpoints)
1) **Gateway**
   - Add counters/histograms in `services/gateway/main.py` (enqueue), `routers/attachments.py`, `routers/ui_static/sse` for SSE gauges.
   - Expose gauges for degraded buffer size via existing `/metrics` (no UI change).
2) **Conversation Worker**
   - Wrap Somabrain call and LLM call with latency + success/failure counters.
   - Add degraded bypass counters and token/latency metrics for direct LLM responses.
3) **Event Bus / Publisher**
   - Instrument `services/common/event_bus.py` and `services/common/publisher.py` for publish/consume latency and error counters.
4) **Outbox / Replicator**
   - Gauges for pending outbox rows and replication success/error counters.
5) **Tool Executor**
   - LLM/tool call counters, latency, errors, tokens.
6) **Budgets**
   - Instrument budget manager to emit allowed/used/overrun metrics per tenant (low-cardinality).
7) **Validation**
   - Curl scrape: `curl http://localhost:8010/metrics` (gateway) and worker/tool-executor ports.
   - Smoke: send message in degraded mode → expect `somabrain_bypass_total`, `assistant_emitted_total{mode="degraded"}`, LLM tokens/latency increment.
   - Playwright UI smoke (browsers in `/tmp/playwright`): `PLAYWRIGHT_BROWSERS_PATH=/tmp/playwright RUN_PLAYWRIGHT=1 pytest tests/ui/playwright/test_basic_chat.py -q`.

## Guardrails
- Keep label sets tight: provider, model, mode, tenant (bounded), result/code.
- Histogram buckets: latency (0.05,0.1,0.25,0.5,1,2,5,10,20), tokens (64,128,256,512,1k,2k,4k,8k).
- No hardcoded URLs/paths; use `cfg.env`/settings.
- No new files beyond this roadmap; instrumentation goes into existing modules.
