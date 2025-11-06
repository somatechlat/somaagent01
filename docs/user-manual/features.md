# Features Overview

**Standards**: ISO/IEC 29148§5.3

## Core Features

### Conversational Interface

Chat with the AI assistant using natural language. The agent understands context and maintains conversation history.

**Example**:
```
User: What's the weather like?
Agent: I'll search for current weather information...
```

### Code Execution

The agent can write and execute code in multiple languages:
- Python
- JavaScript
- Bash/Shell
- SQL

**Example**:
```
User: Calculate the factorial of 10
Agent: [Writes Python code, executes it, returns result]
```

### Memory System

Persistent memory across sessions:
- **Short-term**: Current conversation context
- **Long-term**: Facts, preferences, solutions stored in SomaBrain

**Example**:
```
User: Remember my email is user@example.com
Agent: ✅ Saved to memory
```

Persona-aware metadata:
- Runtime memory writes include persona summaries (name, tags) to improve downstream filtering and analysis.
	- Config: `SOMABRAIN_PERSONA_TTL_SECONDS` controls persona cache TTL.

### Multi-Agent Cooperation

Delegate complex tasks to subordinate agents:
- Main agent breaks down tasks
- Subordinates work in parallel
- Results aggregated and reported back

**Example**:
```
User: Analyze these 5 datasets simultaneously
Agent: Creating 5 subordinate agents...
```

### Tool Ecosystem

Built-in tools:
- **Web Search**: DuckDuckGo, SearXNG integration
- **File Operations**: Read, write, manage files
- **Browser Agent**: Automated web browsing
- **Document Query**: RAG-based document Q&A
- **Scheduler**: Task scheduling and automation

### Streaming Responses

Real-time response streaming:
- See agent thinking process
- Intervene at any point
- Stop/pause execution

### Attachments

Upload files for context:
- Documents (PDF, TXT, MD)
- Images (PNG, JPG)
- Code files
- Data files (CSV, JSON)


## Advanced Features

### Agent Profiles

Different agent personalities:
- **Default**: General-purpose assistant
- **Developer**: Code-focused agent
- **Researcher**: Research and analysis
- **Hacker**: Security testing (Kali Linux)

### MCP Integration

Model Context Protocol support:
- Connect to external MCP servers
- Use third-party tools
- Extend agent capabilities

### A2A Protocol

Agent-to-Agent communication:
- Connect multiple agent instances
- Distributed task processing
- Cross-agent memory sharing

### Secrets Management

Secure credential storage:
- Agents use credentials without seeing them
- Fernet encryption
- Vault integration (optional)

### Admin Ops (SomaBrain)

Operator-focused endpoints (admin scope required):
- `GET /v1/admin/memory/metrics` → SomaBrain memory metrics for a tenant/namespace
- `POST /v1/admin/migrate/export` → export memory state
- `POST /v1/admin/migrate/import` → import memory state

Policy decision receipts are captured for every protected call when OPA/OpenFGA are configured, aiding audits and troubleshooting.

## Next Steps

- [Installation Guide](./installation.md)
- [FAQ](./faq.md)
- [Technical Manual](../technical-manual/index.md)
