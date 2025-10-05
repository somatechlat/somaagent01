⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 – Sprint 1A & 1B Execution Plan

## Sprint Goals
- Extract the conversation engine from the monolithic Agent Zero runtime into a dedicated Kafka-driven worker that leverages Redis/Postgres session repositories.
- Launch the Tool Executor service and integrate OPA/OpenFGA policy checks with requeue support.
- Deliver initial UI/CLI tooling for inspecting sessions, models, and policy statuses.

## Status Snapshot (Codebase as of Sprint 1B)
- Conversation worker exists and processes messages via Kafka, applying model profiles and budget checks, but still lacks streaming tokens, preprocessing, and typed domain entities (`services/conversation_worker/main.py`).
- Tool executor has been refactored with registry/execution engine abstractions, policy checks, schema validation, and telemetry (`services/tool_executor`). Remote SomaKamachiq execution is still pending.
- Requeue service API is available, yet automated retries from the conversation worker and UI dashboards remain to be implemented.
- No dedicated session inspection UI or developer replay tooling has landed in the repository.

## Sprint 1A (Weeks 3–4) – Conversation Worker & OSS SLM Pre-Processing

### Deliverables
1. **Conversation Worker Service** – *Partially delivered*
   - Kafka consumer, session persistence, policy/budget checks implemented.
   - Lightweight preprocessing (intent/sentiment/tags) and streaming token delivery added; deeper OSS pipelines still pending.

2. **Stateful Entities** – *Not started*
   - Domain models/history manager still pending.

3. **Legacy Code Refactor** – *In progress*
   - Core agent no longer executes tools inline, but legacy helpers (e.g., `python/helpers/persist_chat.py`) remain.

4. **Streaming Enhancements** – *Partially delivered*
   - Streaming deltas emitted on `conversation.outbound`; WebSocket/SSE clients receive partial tokens. UI rendering remains to be updated.

5. **Developer Utilities** – *Not started*
   - Replay CLI added (`scripts/replay_session.py`); additional automated tests remain outstanding.

### Acceptance Criteria
- End-to-end test: send message → conversation worker produces streaming response → session state persisted.
- OSS SLM pipeline returns intent classification within <150ms on dev hardware.
- Legacy chat file writes removed; repository tests green.
- Metrics exported: `conversation_requests_total`, `conversation_latency_seconds`, `slm_intent_duration_seconds`.

### Risks & Mitigations
- **SLM latency**: coordinate batching through the managed Soma SLM API, profile prompts, provide fallback to smaller models when under load.
- **State consistency**: thorough tests + transactional writes to Postgres ensure history integrity.

## Sprint 1B (Week 5) – Tool Executor, Policy Enforcement, Requeue Flow

### Deliverables
1. **Tool Executor Service** – *Partially delivered*
   - Registry/execution engine, schema validation, telemetry, and policy checks are live. Remote sandboxing via SomaKamachiq still needs implementation.

2. **Policy Client Integration** – *Partially delivered*
   - Tool executor calls the policy client; conversation worker still needs policy hooks around memory writes and tool requests.

3. **Requeue Management** – *Partially delivered*
   - Requeue API exists; automatic retries and UI tooling remain outstanding.

4. **User Interface Enhancements** – *Not started*
   - No session inspector or model profile dashboard committed.

5. **Testing & Observability** – *In progress*
   - Basic telemetry (SLM/tool metrics) is emitted, but dedicated integration tests and additional metrics are pending.

### Acceptance Criteria
- Tool executor processes sample requests (e.g., code execution, web search) with policy gating.
- Requeue dashboard/API shows blocked actions and allows override with audit event.
- Conversation worker reacts to `tool.results` events (integrated with streaming response).
- Observability dashboards updated with tool/policy metrics.

### Risks & Mitigations
- **Sandbox stability**: start with Docker-based isolation; plan Firecracker integration in later sprints.
- **Policy misconfiguration**: implement canary mode with fail-open option and verbose logging before enforcing fail-closed in production.

---
This document details the second pair of sprints for SomaAgent 01, focusing on conversation extraction and policy-governed tool execution.
