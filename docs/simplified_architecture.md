# Simplified Architecture Proposal

## Goal
Reduce the Docker‑Compose footprint to the **minimum set of services required for a production‑grade, enterprise‑ready SomaAgentHub**, while **keeping Kafka** as the event backbone.

---

## Essential Services (keep)
| Service | Reason |
|---------|--------|
| **kafka** | Core messaging bus for all internal communication (conversation, tool‑execution, delegation, etc.). |
| **redis** | Fast in‑memory store used for caching, session state, and pub/sub patterns. |
| **postgres** | Relational store for agent metadata, telemetry, and persistence of user data. |
| **gateway** | FastAPI entry point exposing the public API (port 8010). |
| **conversation‑worker** | Consumes `conversation.*` topics, runs the LLM inference loop. |
| **tool‑executor** | Executes external tool calls; depends on Kafka for request/response flow. |
| **settings‑service** | Provides configuration management via REST; lightweight and required for multi‑tenant setups. |
| **router** | Routes requests between services; thin wrapper around FastAPI. |
| **agent‑ui** | Optional UI for local development; can be omitted in headless deployments. |

## Services that can be **removed** for a lean stack
- **clickhouse** – analytics data store (replace with Postgres if needed).
- **prometheus** / **grafana** – monitoring stack (can be added later as side‑cars).
- **vault** – secret management (use environment variables or external KMS).
- **opa** – policy engine (if simple allow‑all policy is sufficient).
- **openfga** – fine‑grained authorization (can be deferred to OPA or custom checks).
- **qdrant** – vector store (replace with Postgres `pgvector` or external service).
- **audio‑service**, **canvas‑service**, **requeue‑service**, **scoring‑job**, **delegation**, **settings‑service** (some can be merged or disabled depending on use‑case).

## Consolidation Strategy
1. **Merge small FastAPI services** – `settings-service`, `router`, `requeue-service` can be combined into the **gateway** process, exposing additional endpoints under `/settings`, `/router`, etc. This reduces the number of containers and simplifies networking.
2. **Optional UI** – run `agent-ui` only in dev mode (`profiles: ["dev"]`). Exclude it in production by removing its entry from `docker‑compose.yml`.
3. **Feature toggles** – keep the original service definitions but wrap them in Docker **profiles** (e.g., `profiles: ["analytics"]` for ClickHouse/Prometheus). Users can start the minimal stack with `docker compose --profile core up`.

## Minimal Docker‑Compose Example
```yaml
services:
  kafka:
    ... # unchanged
  redis:
    ... # unchanged
  postgres:
    ... # unchanged
  gateway:
    <<: *agent-service
    container_name: somaAgent01_gateway
    command:
      - "python3"
      - "-m"
      - "uvicorn"
      - "services.gateway.main:app"
      - "--host"
      - "0.0.0.0"
      - "--port"
      - "8010"
    environment:
      <<: *agent-env
      PORT: "8010"
      # expose merged endpoints via the same process
    ports:
      - "8010:8010"
  conversation-worker:
    <<: *agent-service
    command: ["python3", "-m", "services.conversation_worker.main"]
    environment:
      <<: *agent-env
  tool-executor:
    <<: *agent-service
    command: ["python3", "-m", "services.tool_executor.main"]
    environment:
      <<: *agent-env
  # Optional UI – enable with `--profile dev`
  agent-ui:
    <<: *agent-service
    profiles: ["dev"]
    command: ["/exe/initialize.sh", "development"]
    ports:
      - "7001:80"
    depends_on:
      - kafka
      - postgres
      - redis
```

## Benefits
- **Fewer containers** → lower resource consumption, faster spin‑up, easier CI/CD.
- **Kafka retained** → all existing pub/sub flows remain untouched.
- **Modular** – optional services can be added back via Docker **profiles** without altering the core stack.
- **Enterprise‑ready** – core services (Kafka, Redis, Postgres) are battle‑tested for high‑throughput, durability, and scaling.

---

## Next Steps
1. **Update `docker-compose.somaagent01.yaml`** to add the `profiles` keys shown above and remove optional services from the default startup list.
2. **Validate** the minimal stack by running `docker compose --profile core up` and exercising the public API (`/health`, `/v1/...`).
3. **Add monitoring** later by enabling the `analytics` profile when needed.
4. **Document** the profile usage in the README for operators.

*Feel free to adjust the list of merged services based on your exact feature set.*
