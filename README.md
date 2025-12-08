# SomaAgent01

**WE DO NOT MOCK. WE DO NOT BYPASS. WE DO NOT INVENT TESTS. WE USE REAL DATA, REAL SERVERS, REAL EVERYTHING.**

[![SomaAgent01 Website](https://img.shields.io/badge/Website-somaagent01.dev-0A192F?style=for-the-badge&logo=vercel&logoColor=white)](https://somaagent01.dev)

SomaAgent01 is a personal, organic agentic framework that grows and learns with you. It is designed to be fully transparent, readable, comprehensible, customizable, and interactive.

## Core Features

*   **General-Purpose Assistant:** Not pre-programmed for specific tasks. Gathers info, executes code, cooperates with other agents.
*   **Computer as a Tool:** Uses the OS to accomplish tasks (terminal, file system).
*   **Persistent Memory:** Memorizes solutions, code, facts, and instructions.
*   **Multi-Agent Cooperation:** Agents report to superiors and can create subordinates.
*   **Customizable:** Behavior defined by `prompts/`, extensible tools in `python/tools/`.
*   **Enterprise-Grade:** Versioned gateway, Prometheus metrics, circuit breakers, capsule registry.

## Acknowledgement

This project is based on [Agent Zero](https://github.com/agent0ai/agent-zero), originally created by Jan Tomasek and distributed under the MIT License. SomaAgent01 extends the original framework with significant architectural enhancements, enterprise-grade features, and a "Code is Truth" philosophy that ensures 100% alignment between documentation and implementation. While we honor the roots of this project, SomaAgent01 represents a distinct evolution designed for rigorous production environments.

## Quick Start (Development)

### Prerequisites

*   Docker & Docker Compose
*   Python 3.11+
*   Make

### Running the Stack

Provider credentials and model profiles are managed exclusively through the Web UI Settings (`/ui` -> Settings). Secrets are stored encrypted in Redis via the Gateway.

1.  **Start the stack (Developer Profile):**
    ```bash
    make dev-up
    ```
    This starts the Gateway, Workers, and UI in Docker containers.

2.  **Access the UI:**
    *   Open [http://localhost:21016/ui](http://localhost:21016/ui)
    *   Settings -> Model -> Configure your LLM provider (e.g., Groq, OpenAI).
    *   Start chatting!

3.  **Stop the stack:**
    ```bash
    make dev-down
    ```

### Common Commands

See `Makefile` for the full list.

| Command | Description |
| :--- | :--- |
| `make dev-up` | Start minimal dev stack (Gateway, Workers, UI). |
| `make dev-down` | Stop minimal dev stack. |
| `make dev-logs` | Tail logs for the stack. |
| `make dev-rebuild` | Rebuild and restart the stack. |
| `make dev-down-clean` | Stop stack, remove volumes, and clean network. |
| `make quality` | Run all quality checks (Format, Lint, Typecheck, Test). |
| `make test-e2e` | Run End-to-End tests. |

## Documentation

*   [Installation](./docs/installation.md)
*   [Usage](./docs/usage.md)
*   [Development](./docs/development.md)
*   [Connectivity](./docs/connectivity.md)
*   [Architecture](./docs/architecture.md)

For complete documentation, see `docs/README.md` or build the site with `mkdocs`.

## Architecture

The system consists of several key services:

*   **Gateway (`services/gateway`):** Central entry point, handles API requests, streaming, and auth.
*   **Orchestrator (`orchestrator/`):** Manages agent lifecycle and task coordination.
*   **Conversation Worker (`services/conversation_worker`):** Handles chat logic and LLM interaction.
*   **Tool Executor (`services/tool_executor`):** Executes tools (code, search, etc.) safely.
*   **Web UI (`webui/`):** User interface for interaction and configuration.
*   **Infrastructure:** Redis (State/Cache), Postgres (Persistence), Kafka (Event Bus).

## Coding Standards (Vibe Coding Rules)

We strictly follow the Vibe Coding Rules:
1.  **No Bullshit:** Truthful reporting, no mocks.
2.  **Check First, Code Second:** Verify before implementing.
3.  **No Unnecessary Files:** Keep it simple.
4.  **Real Implementations Only:** Production-grade code.
5.  **Documentation = Truth:** Docs must match code.
6.  **Complete Context Required:** Understand before changing.
7.  **Real Data & Servers Only:** No assumptions.

See `docs/development-manual/coding-standards.md` for detailed Python guidelines.

## License

MIT License. See [LICENSE](./LICENSE) for details.
