⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 – Sprint 1A & 1B Execution Plan

## Sprint Goals
- Extract the conversation engine from the monolithic Agent Zero runtime into a dedicated Kafka-driven worker that leverages Redis/Postgres session repositories.
- Launch the Tool Executor service and integrate OPA/OpenFGA policy checks with requeue support.
- Deliver initial UI/CLI tooling for inspecting sessions, models, and policy statuses.

## Sprint 1A (Weeks 3–4) – Conversation Worker & OSS SLM Pre-Processing

### Deliverables
1. **Conversation Worker Service**
   - New package `services/conversation_worker` consuming `conversation.inbound`.
   - Rehydrate session context (persona ID, history pointers, attachments) from Redis/Postgres repositories.
   - Invoke OSS SLM preprocessing pipeline (intent classification, slot extraction, safety tags) using vLLM-hosted Llama 3 8B or Mistral 7B.
   - Call primary LLM via model profile (initial default: Llama 3 70B or Mixtral) and stream partial tokens back through `conversation.outbound`.
   - Persist results to Postgres event store, including token counts and latency metrics.

2. **Stateful Entities**
   - Domain models (`ConversationTurn`, `ToolCall`, `PolicyVerdict`, `MemoryOperation`) with serialization helpers.
   - History manager that supports replay, truncation, and summarization for long sessions.

3. **Legacy Code Refactor**
   - Remove direct use of `python/helpers/persist_chat.py` / `tmp/chats`.
   - Strip inline tool execution from `agent.py`; convert to functions callable by the worker (pure orchestration logic).

4. **Streaming Enhancements**
   - Implement partial token events (`status: streaming`) with correlation IDs in Kafka.
   - WebSocket client updates to render partial responses and status lines.

5. **Developer Utilities**
   - CLI `scripts/replay_session.py` to replay events from Postgres/Kafka for debugging.
   - Unit/integration tests covering SLM preprocessing, LLM invocation, streaming output.

### Acceptance Criteria
- End-to-end test: send message → conversation worker produces streaming response → session state persisted.
- OSS SLM pipeline returns intent classification within <150ms on dev hardware.
- Legacy chat file writes removed; repository tests green.
- Metrics exported: `conversation_requests_total`, `conversation_latency_seconds`, `slm_intent_duration_seconds`.

### Risks & Mitigations
- **SLM latency**: enable batching in vLLM, profile prompts, provide fallback to smaller models when under load.
- **State consistency**: thorough tests + transactional writes to Postgres ensure history integrity.

## Sprint 1B (Week 5) – Tool Executor, Policy Enforcement, Requeue Flow

### Deliverables
1. **Tool Executor Service**
   - Kafka consumer at `tool.requests`, executing adapters from `python/tools` in isolated workers (Docker sandbox / Firecracker).
   - Emit results to `tool.results`, including stdout/stderr, attachments, execution time, exit status.

2. **Policy Client Integration**
   - Shared `policy_client` module calling SKM Policy Engine (`/v1/evaluate`) with context (tenant, persona, tool, payload).
   - Wrap conversation worker memory writes and tool requests with policy checks.
   - On denial or OPA failure, publish `policy.blocked` event and store entry in Redis/Postgres requeue store.

3. **Requeue Management**
   - API endpoints (`POST /v1/policy/requeue/{id}/resolve`) for admins to re-evaluate or override blocks (with audit trail).
   - Background job (conversation worker) polling requeue store and retrying actions once policy passes.

4. **User Interface Enhancements**
   - Session inspector panel showing tool calls, policy decisions, and memory operations with status icons.
   - Model profile summary (read-only) displayed during conversation for operator awareness.

5. **Testing & Observability**
   - Integration tests covering tool execution success/failure, policy block/unblock path, requeue retries.
   - Metrics: `tool_execution_duration_seconds`, `policy_blocked_total`, `requeue_pending_total`.
   - Logs enriched with trace IDs, constitution hash, tenant ID, persona ID.

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
