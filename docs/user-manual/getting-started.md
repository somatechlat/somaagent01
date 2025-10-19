---
title: Getting Started with SomaAgent01
slug: user-getting-started
version: 1.0.0
last-reviewed: 2025-10-15
audience: new users
owner: soma-docs
reviewers:
  - product
  - support
prerequisites:
  - Docker Desktop installed
  - SomaAgent01 repository cloned or Docker image pulled
  - Valid Soma SLM credentials (optional for local Ollama)
verification:
  - Web UI reachable at configured host and port
  - Sample task completes successfully
---

# Getting Started with SomaAgent01

This guide walks you from zero to a functioning SomaAgent01 UI in minutes. It builds on the installation flow and ends with a verified task so you know the environment works end-to-end.

## 1. Launch the Web UI

1. Open a terminal inside the SomaAgent01 checkout or the shipped Docker container.
2. Activate your runtime environment (virtualenv or Conda) if you are running locally.
3. Start the UI service:

```bash
python run_ui.py
```

4. When the server starts, note the hostname and port printed to the console (for example `http://127.0.0.1:50001`).
5. Open the URL in your browser. You should see the SomaAgent01 UI with the dashboard and left-hand navigation.

> [!TIP]
> If you are running through Docker Compose, use `docker compose -p somaagent01 --profile dev -f docker-compose.yaml up agent-ui`. The default host port is `${AGENT_UI_PORT:-20015}`, but you can override it via environment variables or the compose file.

## 2. Explore the Chat Interface

The UI exposes four primary controls below the conversation panel:

- `New Chat` creates an empty session.
- `Reset Chat` clears memory persistence for the current session.
- `Save Chat` writes the conversation to `/tmp/chats` in JSON format.
- `Load Chat` restores a saved transcript.

Use these controls to manage workspaces and maintain reproducibility.

## 3. Run a Sample Task

1. In the chat input field, enter: `Download a YouTube video for me`.
2. Observe the agent thoughts and tool invocations in real time. SomaAgent01 will propose a solution using `code_execution_tool`.
3. When prompted, provide a YouTube URL. The agent downloads the asset and reports the saved file path.

### Verification

- The task log shows tool execution steps without errors.
- A file is present in the reported directory.
- The UI confirms success with a green notification.

If any step fails, consult the [Troubleshooting & FAQ](./troubleshooting.md) matrix for targeted remediation.

## 4. Next Steps

- Learn the daily workflows in the [feature playbook](./using-the-agent.md).
- Configure SLM credentials and persistence using the [installation guide](./installation.md).
- Bookmark the [troubleshooting matrix](./troubleshooting.md) for fast recovery during operations.

> [!IMPORTANT]
> Keep the UI port private. When exposing the tunnel externally, enable authentication and TLS proxies according to the security guidelines in the Technical Manual.
