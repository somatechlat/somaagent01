<div align="center">

# 🤖 SomaAgent01

### *Autonomous AI Agents That Remember, Reason, and Act*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django 5.0+](https://img.shields.io/badge/Django-5.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)](LICENSE)

<br/>

**Deploy AI agents with cryptographic identity, persistent memory, and governed autonomy.**

[Website](https://www.somatech.dev) · [Features](#-what-makes-it-different) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [Ecosystem](#-somastack-ecosystem)

</div>

---

## 🎯 What Is This?

**SomaAgent01** is the orchestration layer for autonomous AI agents. It handles the hard parts: identity, memory, tool execution, and governance—so your agents can focus on solving problems.

This isn't another LLM wrapper. It's infrastructure for agents that need to:

- **Persist** across sessions with real memory (not just context windows)
- **Act** in the world through sandboxed tools with human oversight
- **Scale** across teams with multi-tenant isolation
- **Comply** with audit requirements through cryptographic provenance

---

## ✨ What Makes It Different

### 🔐 Cryptographic Agent Identity

Every agent gets a **Capsule**—a signed identity with Ed25519 cryptography. This isn't just authentication; it's provenance. Every action an agent takes is traceable back to its origin.

```python
# Every agent action is signed and traceable
capsule = CapsuleEnforcer.create(
    agent_id="legal-assistant",
    constitution_id="enterprise-v2",  # Governance rules
)
# capsule.fingerprint = "sha3-512:a7f3..."
```

**Why it matters:** When an agent makes a decision, you know *which* agent, *under what rules*, and *with what authorization*. No more black boxes.

---

### 🧠 Real Memory, Not Token Limits

Agents connect to **SomaBrain** for hyperdimensional cognitive memory. This isn't RAG with extra steps—it's associative recall that works like human memory.

```
Agent: "What did we discuss about the Smith contract last month?"
→ SomaBrain recalls context, emotional tone, related decisions
→ Agent responds with actual continuity
```

**Why it matters:** Your agents remember. Not just facts, but context, relationships, and history.

---

### 🛠️ Tools With Human Oversight

Agents can execute code, browse the web, call APIs, and manipulate files. But dangerous operations require **human-in-the-loop approval**.

| Tool | What It Does |
|------|-------------|
| `code_execute` | Run Python in a sandbox |
| `http_fetch` | Call external APIs |
| `browser_agent` | Autonomous web navigation |
| `document_ingest` | Extract text from PDFs, images (OCR) |
| `memory_save/load` | Persist information across sessions |
| `call_subordinate` | Delegate to other agents |

```python
# High-risk tools require approval
@tool(requires_approval=True)
def delete_records(ids: list[str]):
    ...
```

**Why it matters:** Autonomy with guardrails. Agents can act, but you stay in control.

---

### 📜 Constitution-Bound Governance

Agents operate under a **Constitution**—a cryptographically signed set of rules that constrain behavior. Change the constitution, and the change is auditable.

```yaml
# constitution.yaml
name: enterprise-v2
rules:
  - never_reveal_api_keys
  - require_approval_for_external_calls
  - log_all_financial_decisions
```

**Why it matters:** Compliance isn't an afterthought. It's baked into the agent's identity.

---

### 🎙️ Voice In, Voice Out

Built-in voice pipeline with **Whisper** (speech-to-text) and **Kokoro** (text-to-speech). Agents can listen and speak.

```
User speaks → Whisper transcribes → Agent reasons → Kokoro responds
```

**Why it matters:** Voice-first interfaces without stitching together five different services.

---

### 🔄 LLM Provider Resilience

Automatic failover when providers degrade. Health monitoring with latency tracking. Cost-optimized routing across OpenAI, Anthropic, Groq, and custom models.

```
Primary: GPT-4o (healthy, 180ms avg)
Fallback: Claude 3.5 (standby)
Emergency: Llama 3 via Groq (standby)
```

**Why it matters:** Your agents don't go down because OpenAI has an outage.

---

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        YOUR APP                              │
│                   (Web, Mobile, API)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     SOMAAGENT01                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Capsule   │  │    Tool     │  │   LLM Gateway       │  │
│  │   Identity  │  │   Executor  │  │   (Failover/Cost)   │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Voice     │  │   A2A       │  │   SaaS Admin        │  │
│  │   Pipeline  │  │   (Multi)   │  │   (Multi-tenant)    │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌────────────┐   ┌────────────┐   ┌────────────┐
   │  SomaBrain │   │  Postgres  │   │   Redis    │
   │  (Memory)  │   │  (State)   │   │  (Cache)   │
   └────────────┘   └────────────┘   └────────────┘
```

**Stack:** Django + Django Ninja (API), Lit 3 (UI), PostgreSQL, Redis, Temporal (workflows)

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/somatechlat/somaAgent01.git
cd somaAgent01

# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure your LLM keys

# Run
python manage.py migrate
python manage.py runserver 8000

# UI (separate terminal)
cd webui && npm install && npm run dev
```

**Docker:**
```bash
docker-compose up -d
```

---

## 🔌 API Example

```bash
# Create a session and chat
curl -X POST http://localhost:8000/api/v2/chat/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"agent_id": "assistant-v1"}'

# Execute a tool
curl -X POST http://localhost:8000/api/v2/tools/execute \
  -d '{"tool": "http_fetch", "args": {"url": "https://api.example.com"}}'

# Store a memory
curl -X POST http://localhost:8000/api/v2/memory/store \
  -d '{"content": "User prefers dark mode", "tags": ["preferences"]}'
```

---

## 🤝 SomaStack Ecosystem

SomaAgent01 is one part of a larger system:

| Project | Role |
|---------|------|
| **SomaAgent01** (this) | Agent orchestration, tools, identity |
| [**SomaBrain**](https://github.com/somatechlat/somabrain) | Cognitive memory (hyperdimensional vectors) |
| [**SomaFractalMemory**](https://github.com/somatechlat/somafractalmemory) | Long-term distributed storage |

Together, they form a complete cognitive stack for autonomous agents.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/srs/SRS-ARCHITECTURE.md) | System design |
| [Capsule Lifecycle](docs/srs/SRS-CAPSULE-LIFECYCLE-COMPLETE-ISO.md) | Agent identity (ISO 29148) |
| [User Journeys](docs/srs/SRS-USER-JOURNEYS.md) | End-to-end flows |
| [Permission Matrix](docs/srs/SRS-PERMISSION-MATRIX.md) | RBAC model |

---

<div align="center">

## 📜 License

[Apache License, Version 2.0](LICENSE)

---

**Built by the SomaTech team**

*Orchestrating intelligence, one agent at a time.*

</div>
