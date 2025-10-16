# Agent Monologue Loop

The core of **Agent‑Zero** lives in `agent.py`.  The following flowchart shows the
runtime steps for a single monologue iteration – from receiving a user message
to producing a response, optionally invoking tools, and handling extensions.

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

### State diagram for the monologue

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

**Key extension points** (see `docs/development/extensions.md`):
* `monologue_start`
* `message_loop_start`
* `before_main_llm_call`
* `reasoning_stream_chunk` / `response_stream_chunk`
* `tool_execute_before` / `tool_execute_after`
* `monologue_end`

All of these hooks receive the shared `loop_data` object, allowing developers to
inject custom behaviour without modifying the core loop.
