<div align="center">

# 🤖 SomaAgent01

### *Enterprise AI Agent Orchestration Platform*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django 5.0+](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Django Ninja](https://img.shields.io/badge/Django_Ninja-API-00C7B7?style=for-the-badge)](https://django-ninja.rest-framework.com)
[![Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)
[![Build](https://img.shields.io/badge/Build-Passing-brightgreen?style=for-the-badge)]()

<br/>

**The intelligent gateway for autonomous AI agent orchestration**

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API](#-api-reference) · [Documentation](#-documentation)

</div>

---

## 🎯 Overview

**SomaAgent01** is the central platform for AI agent orchestration, built on **Django + Django Ninja** with **Lit Web Components** for the UI. It manages LLM routing, tool execution, agent lifecycle, and the complete SaaS administration layer.

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
- **26+ built-in tools** (code, HTTP, files, docs, memory, browser, vision)
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

### 📊 Enterprise SaaS Features

- **Multi-tenant isolation**
- **53 Django Ninja routers** (682 endpoints)
- **Keycloak JWT authentication**
- **GDPR/HIPAA compliant** audit logging

</td>
</tr>
</table>

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          USER'S BROWSER                                         │
├──────────────────────────────┬──────────────────────────────────────────────────┤
│   Custom UI (Lit/Vite)       │           Django Admin (Built-in)                │
│   Our branded interface      │           Auto-generated forms                   │
│   Port 5173 (dev)            │           /django-admin/                         │
├──────────────────────────────┴──────────────────────────────────────────────────┤
│                                                                                 │
│                     HTTP Requests (JSON or HTML)                                │
│                                                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                           DJANGO SERVER (ASGI/Uvicorn)                          │
│                                                                                 │
│             ┌─────────────────────┬─────────────────────┐                       │
│             │  Django Ninja API   │  Django Admin Views │                       │
│             │  /api/v2/*          │  /django-admin/*    │                       │
│             │  JWT Auth (Keycloak)│  Session Auth       │                       │
│             │  62 Routers         │  Auto-generated     │                       │
│             │  80+ Endpoints      │  CRUD Forms         │                       │
│             └──────────┬──────────┴──────────┬──────────┘                       │
│                        │                     │                                  │
│                        └──────────┬──────────┘                                  │
│                                   │                                             │
│    ┌──────────────────────────────┼──────────────────────────────────────┐     │
│    │                              │                                      │     │
│    │                   ┌──────────▼──────────┐                          │     │
│    │                   │     Django ORM      │                          │     │
│    │                   │     (Shared)        │                          │     │
│    │                   └──────────┬──────────┘                          │     │
│    │                              │                                      │     │
│    │   ┌──────────────────────────┼──────────────────────────┐          │     │
│    │   │                          │                          │          │     │
│    │   ▼                          ▼                          ▼          │     │
│    │ ┌─────────────┐  ┌───────────────────┐  ┌─────────────────────┐   │     │
│    │ │   SAAS      │  │   CAPSULE         │  │   LLM DEGRADATION   │   │     │
│    │ │   ADMIN     │  │   ENFORCER        │  │   SERVICE           │   │     │
│    │ │             │  │                   │  │                     │   │     │
│    │ │ • Tenants   │  │ • Ed25519 Signs   │  │ • Health Monitor    │   │     │
│    │ │ • Users     │  │ • Provenance      │  │ • Fallback Chains   │   │     │
│    │ │ • Plans     │  │ • Constitution    │  │ • Cost Routing      │   │     │
│    │ │ • Features  │  │ • Lifecycle       │  │ • Multi-provider    │   │     │
│    │ └─────────────┘  └───────────────────┘  └─────────────────────┘   │     │
│    │                                                                    │     │
│    │   ┌──────────────────────────────────────────────────────────┐    │     │
│    │   │                    TOOL EXECUTOR                          │    │     │
│    │   │                                                          │    │     │
│    │   │  🔧 code_execute  │  🌐 http_fetch  │  📁 file_ops       │    │     │
│    │   │  ⏰ timestamp     │  🔊 echo        │  📄 doc_ingest     │    │     │
│    │   │  🖼️ canvas       │  🔍 search      │  🔗 mcp_tools      │    │     │
│    │   └──────────────────────────────────────────────────────────┘    │     │
│    │                         SERVICES LAYER                             │     │
│    └────────────────────────────────────────────────────────────────────┘     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
  ┌─────▼─────┐              ┌────────▼────────┐           ┌────────▼────────┐
  │ PostgreSQL │              │    SomaBrain    │           │      Redis      │
  │  Database  │              │ Cognitive Memory│           │      Cache      │
  │  (Django)  │              │   (Port 9696)   │           │    Sessions     │
  └───────────┘              └─────────────────┘           └─────────────────┘
        │                             │                             │
        │                    ┌────────▼────────┐                    │
        │                    │   Milvus        │                    │
        │                    │   Vectors       │                    │
        │                    └─────────────────┘                    │
        │                                                           │
  ┌─────▼─────────────────────────────────────────────────────────────▼─────┐
  │                              LLM PROVIDERS                              │
  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
  │  │ OpenAI  │  │Anthropic│  │  Groq   │  │OpenRouter│  │ Custom  │      │
  │  │ GPT-4o  │  │Claude3.5│  │ Llama3  │  │ Mixtral │  │  LLM    │      │
  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
  └───────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Runtime |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Cache & sessions |
| Node.js | 18+ | UI development |

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
# Edit .env with your credentials

# Run migrations
python manage.py migrate

# Start the Django server
python manage.py runserver 8000

# In another terminal, start the UI
cd webui && npm install && npm run dev
```

### 🐳 Docker Deployment

```bash
docker-compose up -d
```

---

## 📡 API Reference

### Django Ninja API Structure

```
/api/v2/
├── saas/           # SaaS Admin APIs
│   ├── tenants/    # Tenant management
│   ├── plans/      # Subscription plans
│   └── features/   # Feature catalog
├── agents/         # Agent lifecycle
│   ├── capsules/   # Cryptographic identity
│   └── sessions/   # Conversation sessions
├── memory/         # Memory operations
│   ├── store/      # Store memories
│   └── recall/     # Recall memories
└── tools/          # Tool execution
    └── execute/    # Run tools
```

### Example: Create Tenant

```bash
curl -X POST http://localhost:8000/api/v2/saas/tenants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{
    "name": "Acme Corp",
    "slug": "acme",
    "tier": "professional"
  }'
```

### Example: Execute Tool

```bash
curl -X POST http://localhost:8000/api/v2/tools/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "http_fetch",
    "args": {"url": "https://api.example.com/data"}
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
| `document_ingest` | Documents | Ingest PDF/images (OCR) |
| `canvas_append` | UI | Append to UI canvas |
| `memory_save` / `memory_load` | Memory | Save/recall agent memories |
| `browser_agent` | Browser | Autonomous web browsing |
| `vision_load` | Vision | Load and process images |
| `a2a_chat` | A2A | Agent-to-Agent communication |
| `call_subordinate` | Delegation | Delegate to subordinate agents |
| `scheduler` | Scheduling | Schedule delayed tasks |
| `search_engine` | Search | Web search integration |

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
| [Architecture](docs/srs/SRS-ARCHITECTURE.md) | Django + Django Ninja architecture |
| [Capsule Lifecycle](docs/srs/SRS-CAPSULE-LIFECYCLE-COMPLETE-ISO.md) | Agent identity system (ISO 29148) |
| [Settings](docs/srs/SRS-SOMAAGENT01-SETTINGS.md) | All 89 configuration options |
| [User Journeys](docs/srs/SRS-SOMASTACK-USER-JOURNEYS.md) | Complete user flows |
| [Permission Matrix](docs/srs/SRS-SOMASTACK-PERMISSION-MATRIX.md) | 78 permissions, 9 roles |
| [SaaS Index](docs/srs/SRS-SOMASTACK-SAAS-INDEX.md) | Master documentation index |

---

## 🏗️ Project Structure

```
somaAgent01/
├── admin/                  # Django Admin & SaaS models (61 modules)
│   ├── saas/              # Tenants, Plans, Features
│   ├── tools/             # 19 tool implementations
│   ├── permissions/       # RBAC models (78 permissions)
│   └── api.py             # 53 Django Ninja routers (682 endpoints)
├── services/              # Service layer
│   ├── gateway/           # ASGI gateway (Django)
│   ├── common/            # Shared utilities (68 modules)
│   └── tool_executor/     # Tool execution engine (18 modules)
├── webui/                 # Lit 3 Web Components UI (112 files)
│   ├── src/components/   # 34 Lit components
│   └── src/views/        # 61 view components
├── docs/                  # Documentation
│   └── srs/              # 39 SRS documents
└── manage.py             # Django management
```

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
