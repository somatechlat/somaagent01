<div align="center">

# 🤖 SomaAgent01

### *Enterprise AI Agent Orchestration Gateway*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge)]()

<br/>

**The intelligent gateway for autonomous AI agent orchestration**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API](#-api-reference) · [Documentation](#-documentation)

</div>

---

## 🎯 Overview

**SomaAgent01** is the intelligent gateway that orchestrates AI agents, managing LLM routing, tool execution, and agent lifecycle. Designed for **enterprise-grade reliability** with automatic failover, rate limiting, cryptographic identity (Capsules), and comprehensive audit logging.

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔄 LLM Orchestration

- **Automatic model fallback** when providers degrade
- **Health monitoring** with latency/error tracking
- **Cost-optimized routing** across providers
- **Streaming support** for real-time responses

</td>
<td width="50%">

### 🛠️ Tool Execution Engine

- **Sandboxed execution** with timeout controls
- **Human-in-the-loop** approval workflows
- **17+ built-in tools** (code, HTTP, files, docs)
- **MCP protocol support** for extensibility

</td>
</tr>
<tr>
<td>

### 🔐 Capsule Identity System

- **Cryptographic agent identity** (Ed25519 signatures)
- **Provenance chain** for auditability
- **Constitution binding** for governance
- **ISO 29148 compliant** lifecycle

</td>
<td>

### 📊 Enterprise Features

- **Multi-tenant isolation**
- **Rate limiting** per user/tenant/agent
- **Audit logging** for compliance
- **Circuit breakers** for resilience

</td>
</tr>
</table>

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SOMAAGENT01 GATEWAY                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│    ┌─────────────────────────────────────────────────────────────────────┐     │
│    │                    CONVERSATION ROUTER                               │     │
│    │              (WebSocket + HTTP Streaming + REST)                     │     │
│    └───────────────────────────────┬─────────────────────────────────────┘     │
│                                    │                                            │
│    ┌───────────────┬───────────────┼───────────────┬───────────────┐           │
│    │               │               │               │               │           │
│    ▼               ▼               ▼               ▼               ▼           │
│  ┌─────┐       ┌─────┐       ┌─────────┐     ┌─────────┐     ┌─────────┐      │
│  │Auth │       │Rate │       │   LLM   │     │  Tool   │     │ Capsule │      │
│  │     │       │Limit│       │Degrade  │     │Executor │     │Enforcer │      │
│  └─────┘       └─────┘       └────┬────┘     └────┬────┘     └─────────┘      │
│                                   │               │                            │
│                                   ▼               ▼                            │
│    ┌──────────────────────────────────────────────────────────────────────┐   │
│    │                     LLM PROVIDER POOL                                 │   │
│    │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │   │
│    │  │ OpenAI  │  │Anthropic│  │ Groq    │  │OpenRouter│  │ Custom  │    │   │
│    │  │ GPT-4o  │  │Claude3.5│  │ Llama3  │  │ Mixtral │  │  LLM    │    │   │
│    │  │  ✓ OK   │  │  ✓ OK   │  │ ⚠ Slow  │  │  ✓ OK   │  │  ✗ Down │    │   │
│    │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │   │
│    └──────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│    ┌──────────────────────────────────────────────────────────────────────┐   │
│    │                       TOOL REGISTRY                                   │   │
│    │  🔧 code_execute  │  🌐 http_fetch  │  📁 file_ops  │  📄 doc_ingest │   │
│    │  ⏰ timestamp     │  🔊 echo        │  🖼️ canvas    │  🔍 search     │   │
│    └──────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────────┐
              │                       │                           │
        ┌─────▼─────┐          ┌──────▼──────┐          ┌─────────▼─────────┐
        │ SomaBrain │          │   Redis     │          │       Kafka       │
        │  Memory   │          │   Cache     │          │      Events       │
        └───────────┘          └─────────────┘          └───────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime |
| Redis | 7+ | Caching & sessions |
| PostgreSQL | 15+ | State storage (optional) |

### Installation

```bash
# Clone the repository
git clone https://github.com/somatechlat/somaAgent01.git
cd somaAgent01

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)

# Start the gateway
python -m services.gateway.main
```

### 🐳 Docker Deployment

```bash
docker-compose up -d
```

---

## 📡 API Reference

### Create Conversation

```bash
curl -X POST http://localhost:8001/api/v2/conversations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "agent_id": "agent-123",
    "initial_message": "Hello!"
  }'
```

### Send Message (Streaming)

```bash
curl -X POST http://localhost:8001/api/v2/conversations/{id}/messages \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "content": "What is the weather in NYC?",
    "stream": true
  }'
```

### Execute Tool

```bash
curl -X POST http://localhost:8001/api/v2/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "http_fetch",
    "args": {"url": "https://api.weather.com/nyc"}
  }'
```

---

## 🛠️ Built-in Tools

| Tool | Category | Description |
|------|----------|-------------|
| `echo` | Utility | Echo text back |
| `timestamp` | Utility | Get current time |
| `code_execute` | Code | Execute Python in sandbox |
| `http_fetch` | Network | Fetch URL content |
| `file_read` | Files | Read from work directory |
| `file_write` | Files | Write to work directory |
| `document_ingest` | Documents | Ingest PDF/images |
| `canvas_append` | UI | Append to UI canvas |

---

## ⚙️ Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `LLM_DEFAULT_MODEL` | gpt-4o-mini | Default LLM model |
| `LLM_TIMEOUT_SECONDS` | 30 | Request timeout |
| `LLM_MAX_RETRIES` | 3 | Retry count |
| `TOOL_EXECUTION_TIMEOUT` | 30 | Tool timeout |
| `RATE_LIMIT_REQUESTS_PER_MIN` | 100 | Rate limit |

📖 **Full reference:** [`docs/srs/SRS-SOMAAGENT01-SETTINGS.md`](docs/srs/SRS-SOMAAGENT01-SETTINGS.md)

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/srs/SRS-ARCHITECTURE.md) | System architecture |
| [Capsule Lifecycle](docs/srs/SRS-CAPSULE-LIFECYCLE-COMPLETE-ISO.md) | Agent identity system |
| [Settings](docs/srs/SRS-SOMAAGENT01-SETTINGS.md) | All 89 configuration options |
| [User Journeys](docs/srs/SRS-SOMASTACK-USER-JOURNEYS.md) | Complete user flows |
| [Permission Matrix](docs/srs/SRS-SOMASTACK-PERMISSION-MATRIX.md) | 78 permissions, 9 roles |

---

## 🤝 SomaStack Ecosystem

| Project | Description | Link |
|---------|-------------|------|
| 🧠 **SomaBrain** | Hyperdimensional cognitive memory | [GitHub](https://github.com/somatechlat/somabrain) |
| 💾 **SomaFractalMemory** | Distributed long-term storage | [GitHub](https://github.com/somatechlat/somafractalmemory) |

---

<div align="center">

## 📜 License

Licensed under the [Apache License, Version 2.0](LICENSE)

---

<br/>

**Built with 🤖 by the SomaTech team**

*"Orchestrating intelligence, one agent at a time."*

<br/>

[![Star](https://img.shields.io/github/stars/somatechlat/somaAgent01?style=social)](https://github.com/somatechlat/somaAgent01)

</div>
