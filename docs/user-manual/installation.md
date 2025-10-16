---
title: SomaAgent01 Installation Guide
slug: user-installation
version: 1.0.0
last-reviewed: 2025-10-15
audience: evaluators, operators
owner: platform-experience
reviewers:
  - platform-engineering
  - developer-experience
prerequisites:
  - Docker Desktop 4.32+ or docker-ce 26+
  - 16 GB RAM, 4 CPU cores
  - Optional: Soma SLM API key or Ollama runtime
verification:
  - Container starts without errors
  - Web UI reachable via configured port
  - Health check passes via `/health`
---

# SomaAgent01 Installation Guide

Follow this document to install, launch, and verify SomaAgent01 across Windows, macOS, and Linux. Each pathway includes screenshots, commands, and post-installation validation.

## 1. Choose Your Runtime

| Option | When to choose | Requirements |
| ------ | -------------- | ------------ |
| **Managed Soma SLM (recommended)** | Default experience with zero GPU footprint | Internet access to Soma SLM endpoint |
| **Local runtime with Docker Desktop** | Offline trials, custom GPU workloads | Docker Desktop 4.32+, 12 GB RAM |
| **Local models via Ollama (optional)** | When the SLM endpoint is unreachable | Ollama 0.3+, local disk for model caches |

> [!TIP]
> The managed Soma SLM profile is already wired through `.env` values (`SLM_BASE_URL`, `SLM_API_KEY`). If those variables are present, you can skip the Ollama setup entirely.

## 2. Install Docker Desktop (Windows, macOS, Linux)

1. Download Docker Desktop from the [official portal](https://www.docker.com/products/docker-desktop/).
2. Run the installer with default settings.
3. On macOS, drag Docker Desktop to `Applications` and enable **Allow the default Docker socket to be used** under *Settings → Advanced*.
4. Launch Docker Desktop and ensure the whale icon is visible in your system tray or menu bar.

> [!NOTE]
> Linux users may substitute Docker Desktop with `docker-ce`. After installation, add your user to the `docker` group:
>
> ```bash
> sudo usermod -aG docker $USER
> newgrp docker
> docker login
> ```

## 3. Pull the SomaAgent01 Image

You can pull via Docker Desktop UI or the CLI:

```bash
docker pull agent0ai/agent-zero:latest
```

For the hacking edition, pull `agent0ai/agent-zero:hacking`.

## 4. (Optional) Prepare Persistent Storage

1. Create a directory for persistent volumes (for example `~/somaagent01/data`).
2. Map sub-folders as needed:
   - `/a0/agents`
   - `/a0/memory`
   - `/a0/knowledge`
   - `/a0/instruments`
   - `/a0/tmp`

> [!CAUTION]
> Mapping the entire `/a0` directory may complicate upgrades. Prefer mapping only the sub-folders you need or rely on the built-in backup feature.

## 5. Run the Container

Using Docker Desktop:

1. Open the **Images** tab.
2. Locate `agent0ai/agent-zero` and click **Run**.
3. Expand **Optional settings** and set the host port for container port `80` (use `0` for auto selection).
4. Configure volume mounts if you created persistence directories.
5. Click **Run**; the container appears under **Containers**.

Using CLI:

```bash
docker run -p 50080:80 \
  -v ~/somaagent01/memory:/a0/memory \
  -v ~/somaagent01/tmp:/a0/tmp \
  agent0ai/agent-zero:latest
```

## 6. Verify the Deployment

- Open the mapped port in your browser: `http://localhost:<PORT>`.
- Sign in if authentication is enabled.
- Run the built-in smoke check:
  1. Open the **Settings → Diagnostics** tab.
  2. Click **Run Smoke Test**.
  3. Confirm all checks are green.

If the UI fails to load, review container logs (`docker logs <container_id>`) for errors. See the [Troubleshooting & FAQ](./troubleshooting.md) page for targeted fixes.

## 7. Configure Soma SLM Access

1. Open **Settings → API Keys**.
2. Provide `SLM_API_KEY` and verify `SLM_BASE_URL` (defaults to `https://slm.somaagent01.dev/v1`).
3. Save changes and restart the `conversation_worker` service.

### Verification

- Execute the `/health` endpoint: `curl http://localhost:<PORT>/health`.
- Run a sample chat request (see [Getting Started](./getting-started.md)).
- Confirm the **Status** badge in the header is green.

## 8. Optional: Local Models with Ollama

Use these steps only if you cannot access the managed endpoint:

```bash
# macOS (Homebrew)
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Pull a lightweight model
ollama pull phi3:3.8b
```

Update the UI settings:

1. Change the provider to **Ollama** for Chat/Utility/Embedding models.
2. Set the base URL to `http://host.docker.internal:11434`.
3. Save configuration.

## 9. Mobile or External Access

1. Confirm the container port mapping (e.g., `32771:80`).
2. Access the UI via `http://<HOST_IP>:<PORT>` on devices within your network.
3. When enabling Cloudflare Tunnel under **Settings → External Services**, configure authentication first to avoid public exposure without credentials.

## 10. Upgrade Strategy

1. Stop the running container:

```bash
docker stop somaagent01
```

2. Remove the container (data persists in mounted volumes):

```bash
docker rm somaagent01
```

3. Pull the latest image and rerun with previous volume mappings.
4. If settings fail to load, delete `/a0/tmp/settings.json` and restart—the UI rebuilds defaults automatically.

## 11. Post-Installation Checklist

- [ ] Container is running without errors.
- [ ] Web UI accessible via browser.
- [ ] Smoke test passes.
- [ ] API credentials stored securely.
- [ ] Backups scheduled via **Settings → Backup**.
- [ ] Change logged in [`docs/changelog.md`](../changelog.md).

> [!IMPORTANT]
> Store sensitive backups in a secure location. Backups include chat history, API keys, and custom knowledge files.
