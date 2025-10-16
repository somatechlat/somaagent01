# 🛠️ SomaAgent 01 Tool Executor – Implementation Notes

## 🎯 Vision
Deliver a Kafka-driven tool executor that keeps the agent in an orchestration role while SomaKamachiq services handle heavy execution (containers, OS access, browser automation). The current codebase provides the minimal executor and leaves clear seams for the external service to attach.

## ✅ Current Implementation (Sprint 1B)
- `services/tool_executor/main.py` consumes `tool.requests`, enforces policy, dispatches execution, stores results, and publishes `tool.results` for downstream agents.
- A `ToolRegistry` plus `ExecutionEngine` layer coordinates execution with sandbox timeouts and resource caps (`services/tool_executor/tool_registry.py`, `execution_engine.py`, `sandbox_manager.py`, `resource_manager.py`).
- Tool payloads are validated against `schemas/tool_result.json` before leaving the service, preventing contract drift.
- Built-in adapters (echo, timestamp, code_execute, file_read, http_fetch, canvas_append) remain lightweight Python implementations; they are stepping stones until SomaKamachiq exposes richer services.

## 🏗️ Architecture Overview
```
┌──────────────────────────────┐
│        Agent / Worker        │
│  - Plans, requests tools     │
│  - Never runs OS actions     │
└───────────────┬──────────────┘
                │ Kafka
┌───────────────▼──────────────┐
│     Tool Executor Service    │
│  - Policy + registry lookup  │
│  - Execution engine (sandbox)│
│  - Telemetry + persistence   │
└───────────────┬──────────────┘
                │ Future: RPC to SomaKamachiq
┌───────────────▼──────────────┐
│  SomaKamachiq Tool Services  │
│  - Docker/Firecracker pools  │
│  - Browser & network access  │
│  - Audit + monitoring        │
└──────────────────────────────┘
```

## 🧭 Execution Flow
1. Conversation worker emits a tool request event.
2. Executor validates policy; blocked requests land in the requeue store.
3. Registry returns the tool definition; execution engine runs it inside the sandbox with resource guards.
4. Result is validated, persisted to Postgres, published to Kafka, and telemetry is emitted.
5. When SomaKamachiq services go live, step 3 will call out to those services instead of executing locally.

## 🔍 Component Summary
- **Executor Service** (`services/tool_executor/main.py`): orchestrates end-to-end request handling, policy enforcement, telemetry, and persistence.
- **Tool Registry** (`services/tool_executor/tool_registry.py`): loads built-in adapters today; prepared to register remote proxies supplied by SomaKamachiq.
- **Execution Engine** (`services/tool_executor/execution_engine.py`): wraps sandbox calls with resource reservations and provides a single seam for remote execution.
- **Sandbox & Resource Managers** (`services/tool_executor/sandbox_manager.py`, `resource_manager.py`): enforce timeouts and concurrency limits. Both expose `initialize()` hooks for future container pools or external leases.
- **Tool Adapters** (`services/tool_executor/tools.py`): simple Python implementations that keep token usage low and avoid direct OS interaction.

## 🌉 Integration with SomaKamachiq
- Heavy-duty execution (Docker, browser automation, shell access) will be performed by SomaKamachiq tools. The executor will forward requests to those services instead of running them inline.
- The current in-process sandbox exists to keep the pipeline functional while the external services are being built; swapping providers only requires updating the execution engine.

## 🧱 Implementation Tasks
- [x] Registry/engine/sandbox/resource abstractions wired into the executor
- [x] Tool result schema published and enforced
- [ ] Replace in-process sandbox with SomaKamachiq remote execution clients
- [ ] Support remote tool catalogue discovery and registration
- [ ] Extend telemetry with resource usage once external execution is available

## 🗺️ Roadmap Alignment
- **Sprint 1B**: ✅ functional executor with policy integration and telemetry
- **Sprint 2**: remote execution via SomaKamachiq, richer monitoring
- **Sprint 3**: operator-facing tool catalogue, delegation workflows, advanced auditing

## 📎 References
- `services/tool_executor/main.py`
- `services/tool_executor/tool_registry.py`
- `services/tool_executor/execution_engine.py`
- `services/tool_executor/sandbox_manager.py`
- `services/tool_executor/resource_manager.py`
- `services/tool_executor/tools.py`
- `schemas/tool_result.json`
