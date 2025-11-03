# User Manual

**Standards**: ISO 21500§4.2

## Overview

SomaAgent01 provides a conversational AI interface accessible via Web UI or API.

## Quick Start

### Docker (Recommended)

```bash
docker pull agent0ai/agent-zero
docker run -p 50001:80 agent0ai/agent-zero
```

Visit `http://localhost:50001`

### Local Development

```bash
# 1. Start infrastructure
make deps-up

# 2. Start services
make stack-up

# 3. Start UI
make ui
```

Visit `http://127.0.0.1:3000`

## Features

- **Conversational Interface**: Chat with AI assistant
- **Memory**: Persistent conversation history
- **Multi-agent**: Delegate subtasks to subordinate agents
- **Tools**: Code execution, web search, file operations
- **Streaming**: Real-time response streaming
- **Attachments**: Upload files for context

## System Requirements

- **Docker**: 20.10+ (for containerized deployment)
- **Python**: 3.11+ (for local development)
- **Memory**: 8GB RAM minimum
- **Storage**: 10GB available space

## Ports

| Service | Port | Purpose |
|---------|------|---------|
| UI | 20015 | Web interface |
| Gateway | 21016 | API endpoint (configurable via GATEWAY_PORT) |
| Kafka | 20000 | Event streaming |
| Redis | 20001 | Cache |
| PostgreSQL | 20002 | Database |
| OPA | 20009 | Policy engine |

## Related Documents

- [Installation Guide](./installation.md)
- [Usage Guide](./using-the-agent.md)
- [Troubleshooting](./troubleshooting.md)
