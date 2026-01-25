# 🧠 SomaAgent01: Enterprise Multi-Agent Cognitive Platform

![Status](https://img.shields.io/badge/Status-Production%20Ready-green)
![Framework](https://img.shields.io/badge/Framework-Django%205.0-blue)
![Architecture](https://img.shields.io/badge/Architecture-Modular%20Monolith-orange)
![Compliance](https://img.shields.io/badge/VIBE-Compliant-purple)

**SomaAgent01** is the next-generation **Cognitive Operating System** for enterprise AI. Built on a robust **Django 5.0** foundation, it orchestrates autonomous agents, multimodal perception, and long-term memory into a cohesive swarm intelligence.

---

## 🌟 Core Capabilities

### 🤖 Autonomous Swarm Intelligence
-   **Multi-Agent Orchestration**: Coordinate specialized agents (Research, Coding, Analysis) via `admin.orchestrator`.
-   **Hierarchical Delegation**: Agents can delegate sub-tasks to specialized workers or other swarms.
-   **Self-Healing Workflows**: Intelligent error recovery and task retry mechanisms.

### 🧠 Advanced Cognitive Architecture
-   **SomaBrain™ Integration**: Long-term semantic memory and experience retention (`admin.memory`).
-   **RAG & Vector Search**: High-performance knowledge retrieval using ChromaDB/Milvus.
-   **Context Management**: Dynamic context window handling for infinite-turn conversations.

### 👁️👂 Multimodal Perception
-   **Voice Native**: Real-time Speech-to-Text (STT) and Text-to-Speech (TTS) via `admin.voice`.
-   **Vision Capabilities**: Image analysis, diagram interpretation, and visual QA via `admin.multimodal`.
-   **File Intelligence**: Native parsing of PDF, DOCX, CSV, and code repositories (`admin.files`).

### 🛡️ Enterprise Governance (AAAS)
-   **Multi-Tenancy**: Strict data isolation per tenant (`admin.aaas`).
-   **Capsule Security**: Policy-as-Code enforcement for agent boundaries (`admin.capsules`).
-   **RBAC & Audit**: Granular role-based access control and immutable audit logs.

---

## 🏗️ Technical Architecture

SomaAgent01 is engineered as a **Modular Monolith** to combine the simplicity of a single deployment with the scalability of microservices.

### The 17 Core Pillars (`admin/`)
| App | Function | Description |
| :--- | :--- | :--- |
| **Agents** | `admin.agents` | Lifecycle management and prompt engineering. |
| **Brain** | `admin.memory` | Vector embeddings and semantic recall. |
| **Voice** | `admin.voice` | ElevenLabs/Deepgram integration layers. |
| **LLM** | `admin.llm` | Provider-agnostic AI gateway (OpenAI/Anthropic/Gemini). |
| **Orchestrator** | `admin.orchestrator` | Task graph execution engine. |
| **Tools** | `admin.tools` | Secure sandbox for code execution and API calls. |
| **AAAS** | `admin.aaas` | Subscription, billing, and tenant management. |
| **Gateway** | `services.gateway` | High-performance Django Ninja API Gateway. |

---

## 🚀 Deployment

### Quick Start (Docker)
Get the full stack running in minutes.

```bash
# 1. Clone
git clone https://github.com/somatechlat/somaagent01.git

# 2. Configure Environment
cp .env.example .env

# 3. Launch Stack
docker-compose up -d --build

# 4. Access
# API Docs: http://localhost:8010/api/v2/docs
# Dashboard: http://localhost:8010/dashboard
```

### Production Requirements
-   **Database**: PostgreSQL 16+
-   **Cache**: Redis 7+
-   **Vector Store**: Milvus or ChromaDB
-   **Runtime**: Python 3.12+

---

## 🛡️ VIBE Coding Standards

This repository adheres to the **VIBE Coding Rules**, ensuring:
1.  **Zero Legacy**: No deprecated frameworks (FastAPI removed).
2.  **Zero Mocks**: All tests run against real Docker infrastructure.
3.  **100% Type Safety**: Strict MyPy/Pyright compliance.
4.  **Django Native**: Leveraging ORM, Signals, and Apps for all logic.

---
**Maintained by SomaTech LATAM**