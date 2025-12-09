# SomaAgent01 - Product Overview

SomaAgent01 is an enterprise-grade AI agent framework built on Agent Zero foundations. It uses the computer as a tool to accomplish tasks through a deterministic FSM-based orchestration model with cognitive processing, distributed microservices architecture, and production-ready observability.

## Core Philosophy

- **Real implementations only**: No mocks, no stubs, no placeholders. Real data, real servers, real everything.
- **Computer as a tool**: Agents write and execute code, use terminals, browse the web, and manage files.
- **Organic learning**: Persistent memory with cognitive adaptation that grows with usage.
- **Full transparency**: All behavior defined by prompts; nothing hidden or hard-coded.

## Architecture

### FSM-Based Orchestration
Deterministic state machine governing agent lifecycle:
- **Idle** → **Planning** → **Executing** → **Verifying** → **Error**
- State transitions logged and exposed via Prometheus counter `fsm_transition_total`
- Gauge `somaagent_fsm_state` tracks current state

### Event-Driven Microservices
- **Gateway**: FastAPI HTTP gateway serving UI, routing to Kafka
- **ConversationWorker**: Processes conversation messages from Kafka
- **ToolExecutor**: Executes agent tools in sandboxed environment
- **MemoryReplicator**: Replicates memory events across services

### Clean Architecture
Domain-driven design with use cases, ports/adapters, and repository patterns in `src/core/`.

## Cognitive Processing (SomaBrain Integration)

### Neuromodulation System
Simulated neurotransmitter levels affect agent behavior:
- **Dopamine** (0.0-1.0): Controls exploration factor and creativity boost
- **Serotonin** (0.0-1.0): Controls patience factor and empathy
- **Noradrenaline** (0.0-1.0): Controls focus factor and alertness
- Natural decay applied each iteration
- Note: SomaBrain integration methods (`get_neuromodulators`, `update_neuromodulators`) are called but may require SomaBrain service endpoints not yet documented in soma_client.py

### Adaptation State
- Learning weights (exploration, creativity, patience) loaded from SomaBrain
- Recent interaction patterns tracked for behavior optimization
- Cognitive parameters adjusted based on adaptation state
- Note: `get_adaptation_state` is called but requires SomaBrain service endpoint

### Sleep Cycles
- Memory consolidation triggered at high cognitive load (>0.8)
- Pruning and optimization of cognitive parameters post-sleep
- Cognitive load reset after sleep cycle
- Note: `sleep_cycle` is called in cognitive.py but the SomaBrain endpoint may not be implemented yet

## Tools

### Code Execution (`code_execution_tool.py`)
- **Runtimes**: Python (IPython), Node.js, Terminal (bash)
- **Sessions**: Multiple concurrent terminal sessions with session IDs
- **Modes**: Local shell or SSH remote execution
- **Features**: Dialog detection, shell prompt detection, output truncation, timeout handling

### Browser Agent (`browser_agent.py`)
- Playwright-based headless browser automation via `browser-use` library
- Vision support for visual page understanding
- Secrets masking for credential handling
- Screenshot capture and attachment support
- 5-minute timeout with progress updates

### Task Scheduler (`scheduler.py`)
Three task types:
- **ScheduledTask**: Cron-based recurring tasks (minute/hour/day/month/weekday)
- **AdHocTask**: Token-triggered one-time tasks
- **PlannedTask**: Datetime-scheduled task sequences

Methods: `list_tasks`, `find_task_by_name`, `show_task`, `run_task`, `delete_task`, `create_*_task`, `wait_for_task`

### Memory Operations
- **memory_save**: Store information with semantic indexing
- **memory_load**: Recall by similarity search with threshold
- **memory_delete**: Remove specific memories
- **memory_forget**: Bulk removal by query

### Communication
- **response**: Final response to user/superior
- **call_subordinate**: Create child agent for subtask delegation
- **a2a_chat**: Agent-to-Agent communication via FastA2A protocol
- **input**: Request input from user
- **notify_user**: Send notifications

### Other Tools
- **search_engine**: Web search via SearXNG/DuckDuckGo
- **document_query**: RAG-based document Q&A
- **vision_load**: Image analysis and understanding
- **behaviour_adjustment**: Modify agent behavior parameters
- **catalog**: Browse available tools and instruments

## Memory System

### Dual Storage Architecture
- **Local**: FAISS vector store with LangChain embeddings
- **Remote**: SomaBrain distributed memory service

### Memory Areas
- **Main**: General conversation and fact storage
- **Fragments**: Code snippets and partial solutions
- **Solutions**: Complete working solutions
- **Instruments**: Custom agent instruments/procedures

### Operations
- Semantic similarity search with configurable threshold
- Knowledge preloading from markdown documents
- AI-powered memory consolidation and pruning
- Automatic indexing with timestamps and metadata

## Multi-Agent Cooperation

### Agent Hierarchy
- Every agent has a superior (human user for Agent 0)
- Agents create subordinates for subtask delegation
- Results propagate up the chain
- Context isolation per agent

### Agent Profiles
- Dedicated prompts per agent role (`agents/{profile}/prompts/`)
- Custom tools per profile (`agents/{profile}/tools/`)
- Profile-specific extensions and instruments

## MCP Integration

### Server Support
- Agent Zero acts as MCP server for external tool access
- Streamable HTTP and stdio transport types
- Token-based authentication

### Client Support
- Connect to external MCP servers as tools
- Local (stdio) and remote (SSE/HTTP) server types
- Dynamic tool discovery and schema validation

## FastA2A Protocol

Agent-to-Agent communication standard:
- **Server**: `DynamicA2AProxy` ASGI application with token auth
- **Client**: `a2a_chat` tool for outbound A2A calls
- **Skills**: Advertised capabilities (code execution, file management, web browsing)
- Temporary context creation per A2A conversation

## Voice Subsystem

Located in `src/voice/`:
- **AudioCapture**: Microphone input handling
- **Speaker**: Audio output/TTS playback
- **VoiceAdapter**: Pipeline orchestration
- **Provider abstraction**: Pluggable STT/TTS providers (Whisper, Kokoro)
- Prometheus metrics: `VOICE_SESSIONS_TOTAL`, `VOICE_SESSION_DURATION_SECONDS`

## Extension System

21 lifecycle hooks in `python/extensions/`:

| Hook | Trigger Point |
|------|---------------|
| `agent_init` | Agent initialization |
| `monologue_start` | Conversation loop begins |
| `monologue_end` | Conversation loop ends |
| `message_loop_start` | Each iteration starts |
| `message_loop_end` | Each iteration ends |
| `message_loop_prompts_before` | Before prompt building |
| `message_loop_prompts_after` | After prompt building |
| `before_main_llm_call` | Before LLM invocation |
| `system_prompt` | System prompt assembly |
| `reasoning_stream` | During reasoning output |
| `reasoning_stream_chunk` | Each reasoning chunk |
| `reasoning_stream_end` | Reasoning complete |
| `response_stream` | During response output |
| `response_stream_chunk` | Each response chunk |
| `response_stream_end` | Response complete |
| `tool_execute_before` | Before tool execution |
| `tool_execute_after` | After tool execution |
| `hist_add_before` | Before history addition |
| `hist_add_tool_result` | Tool result to history |
| `error_format` | Error message formatting |
| `util_model_call_before` | Before utility model call |

## Streaming Architecture

### Real-Time Output
- Reasoning and response streams with chunk callbacks
- SSE heartbeats every 20s (`system.keepalive`)
- Active connections tracked via `gateway_sse_connections` gauge

### Canonical Event Sequence
```
assistant.started → assistant.thinking.started → assistant.delta (repeated) 
→ assistant.thinking.final → assistant.final (metadata.done=true)
```

Optional tool markers: `assistant.tool.started` / `assistant.tool.delta` / `assistant.tool.final`

## Observability

### Prometheus Metrics
- `fsm_transition_total`: FSM state transitions
- `somaagent_fsm_state`: Current FSM state
- `gateway_sse_connections`: Active SSE connections
- `gateway_rate_limit_results_total`: Rate limiter outcomes
- `assistant_first_token_seconds`: Time to first token

### OpenTelemetry Tracing
- Full trace chain across services
- Tenant ID and request UUID in all traces
- Voice session spans

### Circuit Breakers
- `pybreaker` integration for fault tolerance
- Metrics on port `${CIRCUIT_BREAKER_METRICS_PORT:-9610}`

## Security

### Authentication
- OPA (Open Policy Agent) policy enforcement (fail-closed, cached decisions)
- Internal token authentication between services (`SA01_AUTH_INTERNAL_TOKEN`)
- Bearer token and API key support for external access
- Note: Policy rules are minimal by default (`default allow = true`)

### Secrets Management
- Vault integration for secret injection (`services/common/vault_secrets.py`)
- Redis-encrypted credential storage (`SA01_CRYPTO_FERNET_KEY`)
- SecretsManager for runtime credential masking in browser agent
- mTLS support configurable via `MTLS_ENABLED` (disabled in dev, enabled in prod)

### Code Execution Isolation
- Local or SSH-based remote execution (configurable via `code_exec_ssh_enabled`)
- Multiple concurrent terminal sessions
- Output truncation and timeout handling
- Note: Docker-based sandboxing with `sandbox_policy.yaml` is planned (see SRS.md) but not yet implemented

## API Surface

### Gateway Endpoints (`/v1/*`)
- `/v1/health`: Health check
- `/v1/sessions/*`: Session management
- `/v1/llm/invoke(/stream)`: LLM invocation
- `/v1/runtime-config`: Configuration management
- `/v1/capsules/*`: Capsule registry

### Rate Limiting
- Configurable via `GATEWAY_RATE_LIMIT_ENABLED`
- Window: `GATEWAY_RATE_LIMIT_WINDOW_SECONDS` (default 60)
- Max requests: `GATEWAY_RATE_LIMIT_MAX_REQUESTS` (default 120)

## Customization

### Prompt-Based Behavior
- System prompt: `prompts/default/agent.system.md`
- 80+ prompt templates in `prompts/` folder
- Profile-specific prompts in `agents/{profile}/prompts/`

### Instruments
Custom procedures in `instruments/` folder:
- Markdown-defined callable functions
- Automatically indexed into memory
- Invocable by agent during execution

## User Interfaces

- **Web UI**: Served at `/ui` via Gateway
- **Terminal**: Real-time streaming with intervention support
- **Settings**: Model configuration, API keys, behavior tuning
- **Memory Dashboard**: Browse and manage stored memories
- **File Browser**: Navigate and manage files

## Key Principles

1. **No mocks, no bypasses**: Real implementations only
2. **Transparent codebase**: All behavior visible and modifiable
3. **Production-grade**: Enterprise observability and security
4. **Extensible**: Hooks, profiles, instruments, MCP integration
5. **Cognitive**: Neuromodulation and adaptation for organic behavior
