![Agent Zero Logo](res/header.png)

# Agent Zero Documentation Hub

Welcome! This page curates the actively maintained documentation set. Everything listed here is backed by real services, real data, and production-ready procedures.

## Quick Start

- **[Installation](installation.md):** Fresh installs, upgrades, and platform-specific tips.
- **[Quickstart](quickstart.md):** Launch Agent Zero in minutes.
- **[Usage Guide](usage.md):** Day-to-day workflows in the Web UI.
- **[Troubleshooting](troubleshooting.md):** FAQ and incident triage.

## Architecture & Design

- **[System Overview](architecture/overview.md):** Context diagrams, component map, request flow.
- **[Runtime Lifecycle](architecture/runtime.md):** Startup sequencing, deployment profiles.
- **Component Deep Dives:**
  - [Gateway](architecture/components/gateway.md)
  - [Tool Executor](architecture/components/tool_executor.md)
  - [Memory (SomaBrain)](architecture/components/memory.md)
  - [Agent UI](architecture/components/ui.md)
  - [Realtime Speech](architecture/components/realtime_speech.md)

## APIs & Data Contracts

- **[Gateway API](apis/gateway.md)**
- **[Realtime Session API](apis/realtime_session.md)**
- **[Settings API](apis/settings.md)**
- **[Tool Executor Callbacks](apis/tool_executor_callbacks.md)**
- **[Kafka Topics & Schemas](data/streams.md)**

## Operations

- **[Runbooks](operations/runbooks.md):** Start/stop, smoke tests, recovery drills.
- **[Deployments](operations/deployments.md):** Environment matrix, rollout/rollback.
- **[Observability](operations/observability.md):** Metrics, logs, alerts.

## Development

- **[Environment Setup](development/setup.md)**
- **[Coding Standards](development/coding-standards.md)**
- **[Testing Strategy](development/testing.md)**
- **[Debugging Guide](development/debugging.md)**
- Legacy deep-dive: [Development manual](development.md)

## Features

- **[Realtime Speech](features/realtime_speech.md)**
- **[Memory Management](features/memory_management.md)**
- **[Tooling Integration](features/tooling.md)**

## Extensibility & Connectivity

- **[Extensibility](extensibility.md)**
- **[Connectivity](connectivity.md)**
- **[MCP Setup](mcp_setup.md)**

## Contributing

- **[Contribution Guide](contribution.md)**

---

Need something else? Check the [Reference Index](reference/index.md) or open an issue if a guide is missing.
