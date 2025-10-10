# SomaAgent01 Architecture Overview

> **Audience:** architects, senior developers, SREs, LLM orchestration engineers.  
> **Purpose:** explain how SomaAgent01 stitches together realtime UI, orchestration services, memory, and external providers so humans **and** automated agents can reason about the system.

## System Context

```mermaid
graph TD
    User[Human Operator]
    ScriptedAgent[Automation / CI Agent]
    UI[Web UI (7002)]
    Gateway[Gateway API (8010)]
    ToolExec[Tool Executor]
    Memory[(SomaBrain KV)]
    Kafka[(Kafka Topics)]
    Redis[(Redis Cache)]
    Postgres[(Postgres DB)]
    OpenFGA[(OpenFGA)]
    OPA[(OPA Policy)]
    ExternalLLM[(Model Providers)]
    ExternalTools[(Third-party APIs)]

    User -->|Browser| UI
    ScriptedAgent -->|HTTP| Gateway
    UI --> Gateway
    Gateway --> ToolExec
    Gateway --> Kafka
    Gateway --> Memory
    Gateway --> Redis
    ToolExec --> Kafka
    ToolExec --> ExternalTools
    ToolExec --> Redis
    ToolExec --> Postgres
    Gateway --> OPA
    Gateway --> OpenFGA
    Gateway --> Postgres
    Gateway --> ExternalLLM
    ToolExec --> ExternalLLM
    Gateway --> Memory
    Memory --> Gateway
```

- **Ingress:** humans use the web UI, while machine clients call Gateway directly. Both funnel into the same orchestration pipeline.
- **Decisioning:** Gateway enforces policy (OPA), access control (OpenFGA), and delegates actions to tool executors or downstream services via Kafka.
- **State:** The `SomaBrain` key-value store persists long-lived facts; Redis handles hot caches; Postgres stores structured domain state; Kafka coordinates async workloads.
- **Extensibility:** Every major component exposes APIs or plugin hooks so external agents can extend capabilities without forking the core.

## Service Inventory

| Tier | Service | Purpose | Key Ports | Primary Dependencies |
| --- | --- | --- | --- | --- |
| Presentation | Web UI (`agent-ui`) | Realtime chat, settings, asset delivery | 7002 | Gateway, Settings API |
| Orchestration | Gateway | REST + WebSocket ingress, policy enforcement, job dispatch | 8010 | Redis, Kafka, Postgres, OpenFGA, OPA |
| Execution | Tool Executor | Runs delegated tool invocations / automations | n/a (internal) | Kafka, Redis, Postgres |
| Intelligence | SomaBrain | KV memory persistence, semantic recall | Redis + Postgres | Gateway |
| Data Plane | Kafka | Event fan-out / work queues | 29092 | Zookeeper-less (KRaft) |
| Data Plane | Postgres | Durable relational storage | 25432 | Persistent volume |
| Data Plane | Redis | Low-latency caches / rate limits | 26379 | Persistent volume |
| Policy | OpenFGA | Relationship-based auth | 28280/28281 | Postgres |
| Policy | OPA | Declarative policy evaluation | 29181 | Config maps |

## Deployment Profiles

SomaAgent01 ships with Docker Compose profiles to scale up or down depending on the scenario.

| Profile | What it Enables | Usage |
| --- | --- | --- |
| `core` | Kafka, Redis, Postgres, OpenFGA, OPA | Mandatory for backend services |
| `dev` | Gateway, Agent UI, support workers | Used for local development |
| `speech` (planned) | Whisper / Realtime audio backends | Runs when voice interactions are required |

`make dev-up` activates `core` + `dev` automatically. Staging/production deployments use the same composition with environment overlays.

## Data Flow Narrative

1. **Ingress:** user or agent submits a message via UI/Gateway.
2. **Auth & Policy:** Gateway validates JWT/OpenFGA tuples, applies OPA policies, and verifies rate limits stored in Redis.
3. **Context Assembly:** Gateway queries SomaBrain and Postgres to build the full prompt context, then calls the selected LLM provider.
4. **Decision Output:** Response may include tool invocations; Gateway publishes tasks to Kafka or calls Tool Executor directly for synchronous actions.
5. **Side Effects:** Tool Executor persists results to Postgres, files to S3-compatible storage (optional), and emits follow-up events.
6. **Feedback Loop:** Gateway streams partial results to UI over WebSocket, updates Redis caches, and optionally saves new memories.

## Non-Functional Characteristics

- **Availability:** Core services restart automatically; Postgres and Kafka use persistent volumes. Health checks gate dependent container startup.
- **Observability:** Prometheus/Grafana stack (see `docs/operations/observability.md`) monitors latency, queue depth, realtime session health.
- **Security:** OpenFGA enforces relationship-based access; OPA policy ensures per-tenant budget and capability controls.
- **Scalability:** Stateless Gateway + Tool Executors can be horizontally scaled; Kafka partitions distribute workload; Redis supports clustering for higher tiers.

## Extensibility Touchpoints

| Extension Type | Location | Mechanism |
| --- | --- | --- |
| Tool plugins | `python/tools/` | Register new tool classes discovered at startup |
| Prompt personas | `prompts/*` | Swap system prompts per tenant/persona |
| Memory schemas | `python/memory/schemas/` | Define Pydantic models for structured memories |
| UI Modules | `webui/components/` | Add Alpine.js components with feature flags |
| Automation scripts | `scripts/*.py` | Use CLI wrappers to interact with Gateway/Kafka |

## Next Steps

- Review specific component documents in `docs/architecture/components/` for deeper dive.
- Consult `docs/operations/runbooks.md` for operational procedures.
- Use `docs/development/setup.md` to bootstrap a developer workstation.
