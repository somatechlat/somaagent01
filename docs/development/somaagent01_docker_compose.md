# SomaAgent01 Local Stack (Docker Compose)

A complete, step-by-step guide to running the full SomaAgent01 platform locally with Docker Compose. This document covers prerequisites, configuration, verification, developer workflows, and troubleshooting tips.

---

## 1. Prerequisites

Ensure the following are installed on your workstation:

| Tool | Minimum Version | Notes |
|------|-----------------|-------|
| Docker Desktop | 4.29+ | Enable the built-in **Docker Compose v2** integration. Allocate ≥8 CPU cores and ≥12 GB RAM in settings to prevent Kafka/Postgres throttling. |
| Git | 2.40+ | Required to clone and update the repository. |
| Make *(optional)* | 3.81+ | Helpful for scripted workflows, but not required. |
| cURL *(optional)* | 7.80+ | Used in verification commands. |

> **macOS:** Docker Desktop 4.29+ automatically provides the `host.docker.internal` DNS entry used by the stack. No extra configuration is needed.

---

## 2. Clone and Bootstrap the Repository

```bash
git clone https://github.com/agent0ai/agent-zero.git
cd agent-zero
```

Recommended workspace layout:

```
agent-zero/
├── a0_data/        # Writable volume mounted into all Python services
├── conf/           # Tenant + supervisor configuration
├── docker-compose.somaagent01.yaml
└── infra/          # Infrastructure scripts & alternate compose definition
```

---

## 3. Environment Configuration

1. Copy the sample environment file (if present) or create `.env` at the repo root to override defaults:

   ```bash
   cp .env.example .env  # if the template exists
   ```

2. Populate secrets and overrides as needed. Key variables:

   | Variable | Default | Purpose |
   |----------|---------|---------|
   | `GATEWAY_JWT_SECRET` | `changeme` | JWT signing key used by the gateway for API auth. Change for anything beyond local smoke tests. |
   | `SLM_BASE_URL` | `https://slm.somaagent01.dev/v1` | Managed Soma SLM API endpoint. Override when pointing to a custom SLM deployment. |
   | `VOICE_API_URL` | `https://example.com/voice` | External voice service endpoint consumed by the delegation layer. |
   | `WHISPER_MODEL` | `base.en` | Whisper ASR model size. Larger values (e.g. `medium.en`) consume more CPU/GPU. |
   | `KAFKA_PORT`, `POSTGRES_PORT`, ... | dynamic random port | Host bindings for services. Override when fixed ports are required. |

3. (Optional) Update `conf/tenants.yaml` to register additional tenants or tweak budget settings.

---

## 4. First-Time Build and Launch

> All commands assume you are in the repository root (`agent-zero/`).

1. **Build images** (Python services + OpenFGA):

   ```bash
   docker compose -f docker-compose.somaagent01.yaml build
   ```

2. **Start the full stack** in the foreground:

   ```bash
   docker compose -f docker-compose.somaagent01.yaml up
   ```

   For background mode, append `-d`.

3. **Watch for health checks**. The first run may take ~2–4 minutes while Postgres initialises schemas, Kafka provisions topics, and OpenFGA migrations complete.

---

## 5. Service Map and Ports

| Service | Container Name | Host Port | Notes |
|---------|----------------|-----------|-------|
| Agent UI | `somaAgent01_agent-ui` | `7001` | Visit `http://localhost:7001` after the stack is ready. |
| Gateway API | `somaAgent01_gateway` | `${GATEWAY_PORT:-8010}` | Handles REST/WebSocket traffic from clients and UI. |
| Settings API | `somaAgent01_settings-service` | `${SETTINGS_PORT:-8011}` | Persona, policy, and operator settings. |
| Requeue API | `somaAgent01_requeue-service` | `${REQUEUE_PORT:-8012}` | Manages conversation retries. |
| Router API | `somaAgent01_router` | `${ROUTER_PORT:-8013}` | Dispatches work to conversation workers and tool executors. |
| Canvas API | `somaAgent01_canvas-service` | `${CANVAS_PORT:-8014}` | Whiteboard + context visualisation. |
| Delegation Gateway | `somaAgent01_delegation` | `${DELEGATION_GATEWAY_PORT_PRIMARY:-8015}` | Supervisor process for delegation jobs. |
| Audio API | `somaAgent01_audio-service` | `${AUDIO_PORT:-8016}` | Whisper transcription (CPU). |
| Conversation Worker | `somaAgent01_conversation-worker` | — | Kafka consumer processing conversations. |
| Tool Executor | `somaAgent01_tool-executor` | — | Executes tool requests. |
| Scoring Job | `somaAgent01_scoring-job` | — | Periodic metrics aggregation. |
| Kafka (KRaft) | `somaAgent01_kafka` | dynamic or `${KAFKA_PORT}` | Backing message bus. |
| Redis | `somaAgent01_redis` | dynamic or `${REDIS_PORT}` | Caching + state queue. |
| Postgres | `somaAgent01_postgres` | dynamic or `${POSTGRES_PORT}` | Primary relational store. |
| OpenFGA | `somaAgent01_openfga` | `${OPENFGA_HTTP_PORT:-8080}` | Relationship-based authorization. |
| OPA | `somaAgent01_opa` | `${OPA_PORT:-8181}` | Policy evaluation service. |
| Vault | `somaAgent01_vault` | `${VAULT_PORT:-8200}` | Dev-mode secrets store. |
| Prometheus | `somaAgent01_prometheus` | `${PROMETHEUS_PORT:-9090}` | Metrics collection. |
| Grafana | `somaAgent01_grafana` | `${GRAFANA_PORT:-3000}` | Dashboards (default admin password disabled). |
| Qdrant | `somaAgent01_qdrant` | `${QDRANT_HTTP_PORT:-6333}` | Vector storage (optional profile). |
| ClickHouse | `somaAgent01_clickhouse` | `${CLICKHOUSE_HTTP_PORT:-8123}` | Analytics (optional profile). |

> Optional services (Qdrant, ClickHouse) are tagged with Compose profiles and only start when the profile is enabled, e.g. `docker compose --profile vectorstore up`.

---

## 6. Verifying the Stack

Run these commands after `docker compose up` reports healthy services:

```bash
# Agent UI responds (expect HTML)
curl -I http://localhost:7001

# Gateway health endpoint
curl -s http://localhost:8010/health | jq

# Kafka topic list (inside container)
docker exec -it somaAgent01_kafka /opt/bitnami/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --list

# Postgres connectivity check
PGPASSWORD=soma docker exec -i somaAgent01_postgres \
  psql -U soma -d somaagent01 -c "SELECT NOW();"
```

Successful results confirm that the UI, gateway, Kafka, and Postgres are operational.

---

## 7. Developer Workflow Tips

1. **Hot-reload code:** All Python services mount `./a0_data` into the container at `/a0`. Edit files locally and restart only the affected service:

   ```bash
   docker compose -f docker-compose.somaagent01.yaml restart gateway
   ```

2. **Run a single service:**

   ```bash
   docker compose -f docker-compose.somaagent01.yaml up gateway -d
   ```

   Dependencies defined in `x-agent-depends` ensure Kafka, Postgres, Redis, OPA, and OpenFGA come up automatically.

3. **Attach to logs:**

   ```bash
   docker compose -f docker-compose.somaagent01.yaml logs -f conversation-worker
   ```

4. **Exec into a container:**

   ```bash
   docker exec -it somaAgent01_gateway /bin/bash
   ```

5. **Clean up volumes:**

   ```bash
   docker compose -f docker-compose.somaagent01.yaml down -v
   ```

6. **Enable optional profiles:**

   ```bash
   docker compose --profile analytics --profile vectorstore \
     -f docker-compose.somaagent01.yaml up -d
   ```

---

## 8. Customising Configuration

### 8.1 Override Environment Variables

- Add overrides to `.env` or export them before running Compose:

  ```bash
  export GATEWAY_JWT_SECRET=$(openssl rand -hex 32)
  export WHISPER_MODEL=medium.en
  docker compose -f docker-compose.somaagent01.yaml up -d
  ```

- Service-specific variables are centralised in the `x-agent-env` anchor. To change a value for just one service, set it in the service’s `environment` block.

### 8.2 Adjust Resource Limits

- Edit `Docker Desktop → Settings → Resources` to raise CPU/RAM caps as needed.
- For Linux, configure `/etc/docker/daemon.json` to assign additional memory or CPU shares, then restart Docker.

### 8.3 Persist Data to Custom Locations

- Update volume bindings at the bottom of the compose file. Example: persist Postgres under `~/soma-data/postgres`:

  ```yaml
  volumes:
    postgres_data:
      driver_opts:
        type: none
        o: bind
        device: /Users/<you>/soma-data/postgres
  ```

- Alternatively, point the bind mount in `services.postgres.volumes` to a different host path.

---

## 9. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| `somaAgent01_kafka` exits repeatedly with `Address already in use` | Port clash on `9092` | Set `KAFKA_PORT` in `.env`, or stop the conflicting process. Re-run `docker compose up`. |
| Gateway reports `OPA connection refused` | OPA container not healthy yet | Wait for OPA health check (`docker compose ps`). The gateway retries automatically. |
| Agent UI shows blank screen | Frontend build assets not initialised | Restart `agent-ui` container; check logs in `./logs/ui`. |
| Postgres init scripts fail with permission denied | Host volume restricted | Ensure the `postgres_data` directory is writable by Docker or remove it and let Docker recreate. |
| `openfga-migrate` fails | Postgres not ready | Compose restarts the job automatically. If it keeps failing, examine `postgres` logs for errors. |
| High CPU usage on macOS idle | Docker Desktop resource allocation | Reduce Whisper model size (`WHISPER_MODEL=small.en`) or pause optional services (Qdrant, ClickHouse). |
| `host.docker.internal` unresolved on Linux | DNS entry not provided | Add `127.0.0.1 host.docker.internal` to `/etc/hosts`, or use the gateway’s container IP. |
| `docker compose config` fails with anchor error | YAML indentation issue in manual edits | Validate with `yamllint` before running Compose; ensure anchors (e.g. `<<: *agent-service`) are nested correctly. |

### Log Inspection Cheat-Sheet

```bash
# Tail all logs
docker compose -f docker-compose.somaagent01.yaml logs -f

# Filter gateway errors
docker compose -f docker-compose.somaagent01.yaml logs gateway | grep ERROR

# Inspect Prometheus targets
curl -s http://localhost:${PROMETHEUS_PORT:-9090}/api/v1/targets | jq
```

### Reset the Stack

```bash
# Stop containers but keep volumes
docker compose -f docker-compose.somaagent01.yaml down

# Stop and remove all data (irreversible)
docker compose -f docker-compose.somaagent01.yaml down -v
rm -rf a0_data/__pycache__
```

---

## 10. Advanced Topics

### 10.1 Using the Infra Compose File

`infra/docker-compose.somaagent01.yaml` mirrors the root compose with relative paths adjusted for infra tooling. Run commands from the `infra/` directory when orchestrating via scripts:

```bash
cd infra
docker compose -f docker-compose.somaagent01.yaml up -d
```

### 10.2 Observability Dashboards

- Prometheus listens on `${PROMETHEUS_PORT:-9090}`.
- Grafana dashboards auto-provision from `infra/observability/grafana`. Sign in with the default admin user (`admin`, blank password). If Grafana prompts for a password, set `GF_SECURITY_ADMIN_PASSWORD` in `.env` before starting the stack.

### 10.3 Extending with Custom Tools

- Add Python code under `a0_data/python/tools/` and restart the tool executor:

  ```bash
  docker compose -f docker-compose.somaagent01.yaml restart tool-executor
  ```

- Register the tool in `prompts/` or `conf/tenants.yaml` depending on scope.

### 10.4 Running Tests Inside Containers

- Use `docker exec` to run pytest within the gateway container:

  ```bash
  docker exec -it somaAgent01_gateway pytest tests/services/gateway -q
  ```

- Alternatively, mount your local virtual environment into `a0_data/` and execute via VS Code Remote Containers.

---

## 11. Shutdown Checklist

1. Confirm no critical jobs are running (check the scoring job logs).
2. Gracefully stop containers:

   ```bash
   docker compose -f docker-compose.somaagent01.yaml down
   ```

3. Optionally prune images and volumes to reclaim space:

   ```bash
   docker system prune -af
   docker volume prune -f
   ```

---

## 12. Reference Commands

```bash
# Validate compose syntax
docker compose -f docker-compose.somaagent01.yaml config

# List running containers with health status
docker compose -f docker-compose.somaagent01.yaml ps

# Restart a single service
docker compose -f docker-compose.somaagent01.yaml restart agent-ui

# View resource usage (Docker Desktop)
docker stats
```

---

## 13. Getting Help

- Review the root `README.md` quick-start section.
- Check `docs/SomaAgent01_Runbook.md` for operational context.
- Ask in the Agent Zero Discord (`#support`) with logs attached.
- File GitHub issues with the output of `docker compose ps` and relevant logs.
