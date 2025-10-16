---
title: Troubleshooting & FAQ
slug: user-troubleshooting
version: 1.0.0
last-reviewed: 2025-10-15
audience: operators, support
owner: support-engineering
reviewers:
  - platform-engineering
  - developer-experience
prerequisites:
  - Access to container logs
  - Credentials for managed services
verification:
  - Each issue includes observable recovery criteria
---

# Troubleshooting & FAQ

Use this matrix to diagnose and resolve common SomaAgent01 issues. Each entry gives symptoms, root causes, remediation steps, and verification.

## FAQ

| Question | Resolution |
| -------- | ---------- |
| How do I let the agent edit my files? | Mount or place files in `/work_dir`. The File Browser can navigate to the root, but tool execution occurs under `/work_dir`. |
| Why is nothing happening after I send a prompt? | Check **Settings → API Keys** and ensure chat/utility providers have valid keys. Without them the backend cannot reach the LLMs. |
| Can I use open-source models? | Yes. Follow the [Ollama flow](./installation.md#8-optional-local-models-with-ollama). Set providers to `Ollama` in the settings. |
| How do I persist memory between upgrades? | Use the in-app **Backup & Restore** or mount `/a0/memory`. Review the upgrade steps in [Installation Paths](./installation.md#10-upgrade-strategy). |
| Where can I get more help? | Join the SomaAgent01 [Skool](https://www.skool.com/agent-zero) or [Discord](https://discord.gg/B8KZKNsPpj) communities, or open an issue in the repository. |

## Incident Playbooks

### 1. Chat Input Hangs or Times Out

**Symptoms:** UI shows a spinner indefinitely; no tool execution logs.

**Root Causes:** Missing API keys, rate limits reached, or backend worker offline.

**Remediation:**
1. Verify API keys in **Settings → API Keys**.
2. Check `conversation_worker` logs (`docker logs <worker-container>`).
3. Restart the worker service via the UI or `docker compose restart conversation_worker`.

**Verification:** New chat request completes within 30 seconds and the worker logs show successful tool execution.

### 2. `code_execution_tool` Fails

**Symptoms:** Tool fails with Docker errors or permission denied.

**Root Causes:** Docker not running, outdated base image, or insufficient file access.

**Remediation:**
1. Confirm Docker Desktop is active.
2. On macOS, grant file access under **Docker Desktop → Settings → Resources → File Sharing**.
3. Remove and repull the execution image:

```bash
docker rmi agent0ai/agent-zero-exec || true
docker pull agent0ai/agent-zero-exec
```

**Verification:** Re-run the task; tool completes and outputs artifact paths.

### 3. Slow or Unresponsive UI

**Symptoms:** UI stutters, requests lag, or messages time out.

**Root Causes:** Local resource constraints, large prompt context, network latency.

**Remediation:**
1. Reduce concurrent chats and clear history.
2. Allocate more CPU/RAM to Docker Desktop.
3. If using Ollama, choose smaller models (`phi3:3.8b`).

**Verification:** Subsequent prompts respond within expected SLA (<5s for cached operations, <30s for tool runs).

### 4. Authentication or Authorization Errors

**Symptoms:** `401` or `403` when accessing UI or API.

**Root Causes:** Missing UI credentials, misconfigured OPA policies.

**Remediation:**
1. Set UI username/password under **Settings → Authentication**.
2. Inspect OPA decision logs (`http://localhost:8181/v1/data/http/authz/allow`).
3. Reapply policy bundles from the Technical Manual.

**Verification:** Authenticated users regain access; unauthorized requests remain blocked.

### 5. Backups Fail to Restore

**Symptoms:** Restore wizard errors, mismatched data after restore.

**Root Causes:** Corrupt archive, incompatible patterns, insufficient disk space.

**Remediation:**
1. Validate archive locally (`unzip -t backup.zip`).
2. Review restore patterns to avoid path collisions.
3. Ensure the container has enough disk space (`docker system df`).

**Verification:** Post-restore, knowledge files, chats, and settings match the source environment.

## Escalation

- Collect UI screenshots, container logs, and timestamps.
- File an incident in the project tracker with reproduction steps.
- Notify on-call via the `#soma-oncall` channel.

> [!IMPORTANT]
> Update the [Change Log](../changelog.md) after significant incidents, including resolution steps and preventive actions.
