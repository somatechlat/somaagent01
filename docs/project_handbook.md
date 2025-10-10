# Agent Zero Engineering Handbook

Your single stop for understanding how the Agent Zero platform fits together, what to work on next, and how to stand up a reliable development or operations environment.

---

## 1. Program Snapshot

| Item | Detail |
| --- | --- |
| Primary runtime | Python 3.11+, FastAPI microservices, Kafka backbone |
| Core repos | `agent-zero/` (this repo) with packaged copy in `a0_data/` |
| Environments | Local IDE (`run_ui.py`), SomaAgent01 Docker stack, remote deployments |
| Default entrypoints | CLI (`run_ui.py`, `run_tunnel.py`), HTTP gateway (`services/gateway/main.py`), web UI (`webui/`) |
| Observability | Prometheus (+ Alertmanager), OTel traces, `/health` endpoints |
| Secrets & policy | Vault (dev), OPA, OpenFGA, tenant budgets (`conf/tenants.yaml`) |

---

## 2. Current Priorities

Derived from `ROADMAP_SPRINTS.md` — review the roadmap before picking up work.

1. **Foundation & API hygiene (Sprint 1)**
   - Keep `/v1/*` endpoints stable, validated, and covered by integration tests in `tests/integration/test_gateway_public_api.py`.
   - Ensure `docker-compose.somaagent01.yaml` matches the documented service contract.
2. **Security & policy enforcement (Sprint 2)**
   - Maintain JWT + OpenFGA + OPA integration; document any new policy hooks in `docs/SomaAgent01_Router.md`.
3. **Observability & resilience (Sprint 3)**
   - Confirm circuit breaker metrics export (`CIRCUIT_BREAKER_METRICS_PORT`) and Prometheus alerts remain healthy.
4. **Capsule marketplace & extensions (Sprint 4)**
   - Align registry, SDK, and UI flows; update `docs/SomaAgent01_ModelProfiles.md` when signatures or flows change.

> 🔁 Re-run the regression suite (`pytest`) and refresh the Docker stack health checks whenever you change gateway contracts, tenant policies, or tool executor behaviour.

---

## 3. Repository & Data Layout

```
agent-zero/
├── agents/                     # Canonical prompt + persona definitions
├── a0_data/                    # Packaged mirror (mounted into containers)
├── docs/                       # Primary documentation set (this file lives here)
├── services/                   # FastAPI services (gateway, router, audio, etc.)
├── python/                     # Shared helper modules
├── prompts/                    # Runtime prompt templates (live system)
├── scripts/                    # Operational helpers & automation
├── docker-compose.somaagent01.yaml
└── infra/                      # Infra variants + observability assets
```

Key directories to keep in sync:
- **`agents/` vs `a0_data/agents/`** – `agents/` is the source of truth for prompts; the `a0_data` copy is injected into containers at runtime. Update both only when you intend to change the packaged artifact.
- **`docs/`** – canonical docs. Anything in `a0_data/docs/` should be treated as legacy and removed when safe.
- **`conf/`** – environment-specific configuration (tenants, providers). Changes here require restarts inside Docker.

---

## 4. Environment Matrix

| Environment | Purpose | Components | Docs |
| --- | --- | --- | --- |
| **Local IDE** (`run_ui.py`) | Fast iteration, debugger support | Web UI, API clients, minimal services | [`docs/development.md`](development.md) |
| **SomaAgent01 Docker stack** | Full-platform parity on a single host | Kafka, Redis, Postgres, Vault, OpenFGA, OPA, tool executor, workers, UI | [`docs/development/somaagent01_docker_compose.md`](development/somaagent01_docker_compose.md) |
| **Remote deploys** (Kubernetes, cloud VMs) | Production-like, multi-node | Mirrors Docker stack, optionally with Helm/IaC | `docs/SomaAgent01_Deployment.md`, `docs/SomaAgent01_Runbook.md` |

**Decision rule:** start in the IDE, graduate to the Docker stack when touching Kafka interactions, circuit breakers, or multi-service flows, and only promote changes upstream after passing the compose health checks.

---

## 5. Developer Workstation Setup (macOS example)

1. **Install prerequisites**
   - Python 3.11 or 3.12, Docker Desktop ≥ 4.29, Git, a VS Code–compatible IDE.
   - Optional but recommended: `uv` or `pipx` for environment management, `jq` for JSON inspection.
2. **Clone repo & bootstrap**
   ```bash
   git clone https://github.com/agent0ai/agent-zero.git
   cd agent-zero
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   playwright install chromium
   ```
3. **Editor configuration**
   - Allow workspace recommendations (`.vscode/extensions.json`).
   - Use the `Python: Select Interpreter` command to target `.venv`.
4. **Run the web UI locally**
   ```bash
   python run_ui.py --port 5555
   ```
   Set `WEB_UI_PORT` in `.env` if you prefer a static port.
5. **Connect to Docker tool executor (optional)**
   - Spin up the compose stack (section 6) and configure RFC in UI Settings → Development (`RFC Destination URL`, `RFC Password`, SSH port).
6. **Debugging**
   - Use `.vscode/launch.json` → “run_ui.py” config; place breakpoints in `python/api/` modules.

> ✅ Keep virtual environments out of Git (`.gitignore` already covers `.venv/`).

---

## 6. SomaAgent01 Stack Playbook

1. **Create network once**
   ```bash
docker network inspect somaagent01 >/dev/null 2>&1 || docker network create somaagent01
   ```
2. **Start clean**
   ```bash
docker compose -f docker-compose.somaagent01.yaml -p somaagent01 down --remove-orphans
   ```
3. **Launch**
   ```bash
COMPOSE_PROFILES=dev bash scripts/run_dev_cluster.sh
   ```
4. **Verify**
   ```bash
curl -I http://localhost:7002
curl -s http://localhost:8010/health | jq
docker exec somaAgent01_kafka kafka-topics.sh --bootstrap-server kafka:9092 --list
   ```
5. **Troubleshoot quickly**
   - Kafka stuck → `docker rm -f somaAgent01_kafka && docker volume rm agent-zero_kafka_data`.
   - Port clash → `WEB_UI_PORT=7100 COMPOSE_PROFILES=dev bash scripts/run_dev_cluster.sh`.
   - Full reset → remove volumes listed in §7.2 of `docs/development.md`.

> 📎 Optional profiles: `metrics`, `analytics`, `vectorstore`. Enable via `COMPOSE_PROFILES="dev,metrics"`.

---

## 7. Configuration & Secrets

- **Environment variables** – define in `.env` or export before `docker compose up`.
  - `GATEWAY_JWT_SECRET`, `POLICY_FAIL_OPEN`, `OPENFGA_HOST`, `SOMA_BASE_URL`, `CIRCUIT_BREAKER_METRICS_PORT`.
- **Tenant policies** – edit `conf/tenants.yaml`; restart gateway and router afterwards.
- **Model providers** – update `conf/model_providers.yaml`; keep API keys outside Git and inject via env vars.
- **Vault (dev)** – default unsealed credentials live in `docker-compose.somaagent01.yaml`; change for shared environments.

Document all deviations from defaults in `docs/SomaAgent01_Deployment.md` before promoting to staging/prod.

---

## 8. Testing, Quality, and CI Hooks

| Command | Scope |
| --- | --- |
| `pytest` | Full unit/integration suite (requires Kafka mock fixtures) |
| `pytest tests/integration/test_gateway_public_api.py` | API regression guardrail |
| `ruff check .` | Lint (if Ruff installed) |
| `mypy python/ services/` | Static typing (optional; ensure `requirements-dev.txt` if introduced) |
| `npm test` (inside `webui/` if applicable) | Front-end assertions |

CI expectations:
- Tests must pass on default branch using GitHub Actions workflows in `.github/workflows/`.
- Compose stack lint (`docker compose config`) should remain clean.
- Commit messages follow conventional style (e.g., `feat:`, `fix:`, `docs:`); see `CONTRIBUTING.md`.

---

## 9. Observability & Operations

- **Health checks**
  - HTTP: `/health` on gateway and UI.
  - gRPC or async workers: rely on internal heartbeats; see `services/router/health.py`.
- **Metrics**
  - Prometheus: default `http://localhost:29090` (if profile enabled).
  - Circuit breaker exporter on `${CIRCUIT_BREAKER_METRICS_PORT:-9610}`.
- **Tracing**
  - OpenTelemetry spans emitted when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
- **Logging**
  - Structured JSON logs from services via `python/helpers/logging.py`.
  - Session transcripts stored under `logs/`.
- **Dashboards/Alerts**
  - Import rules from `infra/observability/alerts.yml` into Prometheus.
  - Grafana optional: enable profile or use external instance.

When diagnosing incidents, capture:
1. `docker compose ps` for state.
2. `docker compose logs <service>` for traces.
3. Relevant metrics queries (`rate(http_requests_total[5m])`, circuit breaker counters).
4. Kafka lag via `kafka-consumer-groups.sh`.

Record findings in `docs/SomaAgent01_Runbook.md` if new failure modes appear.

---

## 10. Data & Storage Contracts

- **Postgres** – primary relational DB, volume `agent-zero_postgres_data`.
- **Kafka** – topics defined under `scripts/kafka_partition_scaler.py`; keep topic schema docs in `docs/SomaAgent01_Session_State.md`.
- **Redis** – ephemeral caching; safe to flush between runs (volume `agent-zero_redis_data`).
- **File artifacts** – stored in `a0_data/`, `logs/`, or user uploads under `tmp/uploads/`.
- **Memory** – SomaBrain service default endpoint `http://127.0.0.1:9696`; configure via `SOMA_BASE_URL`.

Back up Postgres and Kafka volumes before destructive operations (see §7.7 of `docs/development.md`).

---

## 11. Deployment Checklist

1. Update docs (`docs/`), especially when changing APIs, env vars, or service shape.
2. Run `pytest` and smoke test the Docker stack.
3. Tag release (`git tag vX.Y.Z`), update changelog (`README.md` “What’s New”).
4. Push images (if applicable) using `DockerfileLocal` or CI pipeline.
5. Notify stakeholders via Discord/Skool; include link to `docs/SomaAgent01_Deployment.md` for ops teams.

For Kubernetes rollouts, keep Helm charts or manifests under `infra/` and reference them here once stabilized.

---

## 12. Support & Further Reading

- **Guides**: [`docs/installation.md`](installation.md), [`docs/usage.md`](usage.md), [`docs/extensibility.md`](extensibility.md)
- **Architecture**: [`docs/architecture.md`](architecture.md), [`docs/simplified_architecture.md`](simplified_architecture.md)
- **Operations**: [`docs/SomaAgent01_Runbook.md`](SomaAgent01_Runbook.md), [`docs/SomaAgent01_QuickActions.md`](SomaAgent01_QuickActions.md)
- **Community**: GitHub Discussions, Discord (`discord.gg/B8KZKNsPpj`)

Keep this handbook current: whenever you add a service, tweak gateway behaviour, or change environment expectations, update the relevant section and cross-link the detailed document in `docs/`.
