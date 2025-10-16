---
title: Conversation Worker
slug: technical-conversation-worker
version: 1.0.0
last-reviewed: 2025-10-15
audience: platform-engineers, runtime developers
owner: platform-architecture
reviewers:
  - infra
  - product
prerequisites:
  - Kafka topics provisioned
  - Postgres and Redis reachable
verification:
  - `pytest tests/rate_limiter_test.py` passes
  - Kafka consumer lag under 100 messages during load test
---

# Conversation Worker

## Mission

Process conversation tasks emitted by the Gateway, orchestrate tool execution, and persist responses back to the timeline while respecting rate limits and extension hooks.

```mermaid
graph TD
    Gateway -->|Kafka: conversation.tasks| Worker
    Worker -->|hydrate| AgentContext
    Worker -->|call| LLM[Chat Model]
    Worker -->|invoke| Tools
    Tools -->|results| Worker
    Worker -->|persist| Postgres
    Worker -->|emit| Kafka[conversation.events]
    Worker -->|update| Memory[SomaBrain]
```

## Module Layout

| Module | Description |
| --- | --- |
| `services/conversation_worker/main.py` | Async consumer loop, task deserialization, health probes |
| `agent.py` | Core monologue loop, extensions, agent context management |
| `python/helpers/rate_limiter.py` | Sliding-window limiter for requests and token budgets |
| `python/helpers/settings.py` | Provider configuration, tenant overrides |
| `python/helpers/extension.py` | Lifecycle hooks invoked around the loop |

## Message Loop Lifecycle

```mermaid
graph TD
    A[Receive UserMessage] --> B[hist_add_user_message]
    B --> C[prepare_prompt]
    C --> D[call_chat_model]
    D --> E{Response contains tool request?}
    E -- Yes --> F[process_tools]
    F --> G[Tool execution & result handling]
    G --> H[Add AI response to history]
    E -- No --> H
    H --> I[Extensions: response_stream_end]
    I --> J[Check for Intervention]
    J -->|Continue| A
    J -->|Pause| K[Wait while paused]
    K --> J
```

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Running : receive user message
    Running --> Waiting : awaiting LLM stream
    Waiting --> ToolCall : tool request detected
    ToolCall --> Running : tool result injected
    Running --> Idle : response sent to user
    Running --> Error : unhandled exception
    Error --> Idle : reset after logging
```

## Rate Limiting

- `RateLimiter` tracks configurable counters (`*_rl_requests`, `*_rl_input`, `*_rl_output`).
- Before each model invocation the worker calls `allow`/`wait` ensuring budgets are respected.
- Breaches trigger progress updates surfaced through `AgentContext.log.set_progress` so UI clients show a waiting bar.
- Limits configurable per model family via `python/helpers/settings.py` and tenant overrides.

## Extension Hooks

| Hook | Purpose |
| --- | --- |
| `monologue_start` | Observe loop start with inbound payload |
| `before_main_llm_call` | Mutate prompts or settings before provider invocation |
| `tool_execute_before` / `tool_execute_after` | Wrap tool execution for auditing |
| `response_stream_chunk` | Stream tokens to downstream observers |
| `monologue_end` | Cleanup and finalize transcripts |

Extensions receive the shared `loop_data` object, allowing feature teams to add observers without touching core logic.

## Configuration

- Environment toggles (sample): `CONVERSATION_MAX_TOKENS`, `CONVERSATION_RETRY_LIMIT`.
- Kafka topics: `conversation.tasks` (consume), `conversation.events` (produce).
- Dependencies resolved via `python/helpers/settings.py` (LLM provider, tool registry, memory adapters).

## Observability

- Metrics: message throughput, tool latency, retry counts (`/metrics` endpoint when `PROMETHEUS_ENABLE=1`).
- Logs: structured JSON with `conversation_id`, `task_id`, `tenant_id`.
- Traces: optional OTEL spans around LLM calls and tool execution if exporter configured.

## Verification Checklist

- [ ] Run `pytest tests/rate_limiter_test.py` to confirm loop throttling.
- [ ] Kafka lag < 100 for `conversation.tasks` under standard load test.
- [ ] Tool invocation breadcrumbs visible in logs and metrics.
