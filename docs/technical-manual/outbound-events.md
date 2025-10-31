# Outbound SSE Event Contract (sa01-v1)

This document describes the unified, versioned event shapes emitted to the canonical SSE stream at:

- /v1/session/{session_id}/events

All events share a common envelope and MUST be JSON-serializable.

## Common envelope

- event_id: string (UUID)
- session_id: string (UUID)
- persona_id: string | null
- role: string — one of: user, assistant, tool, system (future)
- message: string — primary text payload; may be empty for lifecycle markers
- metadata: object — additional fields; see type-specific sections
- version: string — protocol version, currently "sa01-v1"
- type: string — semantic event type, namespaced as below

## Assistant events

- assistant.thinking
  - Purpose: indicate the assistant has started planning/thinking.
  - role: assistant
  - message: ""
  - metadata:
    - status: "thinking"
    - source: "worker"
    - analysis: { intent: string, sentiment: string, tags: string[] }

- assistant.stream
  - Purpose: streaming partial content.
  - role: assistant
  - message: cumulative content buffer (not a delta)
  - metadata:
    - status: "streaming"
    - source: "slm" | "escalation_llm"
    - analysis: {...}
    - stream_index: number (1-based)

- assistant.final
  - Purpose: final response for a turn.
  - role: assistant
  - message: complete assistant answer
  - metadata:
    - status: "completed"
    - source: "slm" | "escalation_llm"
    - analysis: {...}
    - escalation: { reason: string, metadata: object } | null

## Tool events

- tool.start
  - Purpose: indicate tool execution has begun.
  - role: tool
  - message: ""
  - metadata:
    - status: "start"
    - source: "tool_executor"
    - tool_name: string
    - request_id: string (stable across lifecycle)

- tool.result
  - Purpose: final tool result payload for display and memory.
  - role: tool
  - message: compacted string form of payload (JSON if structured)
  - metadata:
    - status: "success" | "error" | "blocked" | string
    - source: "tool_executor"
    - tool_name: string
    - request_id: string (stable across lifecycle)
    - execution_time: number (seconds)
    - sandbox_logs: string | null (when available)

## Notes

- The UI should treat unknown fields as opaque and forward-compatible.
- For long-term stability, clients should use `type` and `metadata.status` to drive rendering, not rely on implicit roles alone.
- The assistant.stream events carry the full cumulative buffer to simplify UI replacement logic.
