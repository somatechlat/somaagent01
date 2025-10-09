## SomaAgent01 — Deployment & Operations (canonical guide)

This document describes how to run, verify, and operate the SomaAgent01 stack included in this repository.
It is written to be simple, explicit, and actionable for local and development environments that should behave in a production-like way (persistence, resource limits, healthchecks, no mocks).

Paths referenced here assume your repository root is the project root where this README lives.

### Quick overview
- Compose file: `infra/docker-compose.somaagent01.yaml`
- Project name used in examples: `somaagent01`
- Key services and host ports (defaults in compose):
  - Gateway: http://localhost:8010/ (health at /health)
  - OpenFGA: http://localhost:8080/ (some builds expose /health or other endpoints — see "OpenFGA checks")
  - Agent UI: http://localhost:7002/
  - Postgres (container): `postgres` — named volume `somaagent01_postgres_data`
  - Kafka (container): `kafka` — named volume `somaagent01_kafka_data`
  - Redis (container): `redis` — named volume `somaagent01_redis_data`

### Goals for this guide
- Start the full stack reliably and persistently
- Provide a single canonical takedown to avoid orphaned containers and port conflicts
- Provide clear smoke checks and troubleshooting steps
- Explain where secrets live and how to rotate them safely

---

## Before you start (prerequisites)
- Docker Desktop (or Docker Engine) and Docker Compose v2+ installed
- At least 8GB free RAM available for the stack (Kafka and the JVM need memory)
- A shell (macOS zsh examples shown)
- From the repo root run: `git status` to ensure you don't have uncommitted local edits you will lose.

### Environment (recommended)
Set these environment variables when running compose commands to match examples here:

```bash
export COMPOSE_PROFILES=core,dev
COMPOSE_FILE=infra/docker-compose.somaagent01.yaml
PROJECT_NAME=somaagent01
```

Replace `core,dev` with `core` if you only want the critical services.

---

## Start the stack (canonical)
1. Optional: dry-run takedown to clean leftovers (safe)

```bash
./scripts/takedown.sh --dry --project ${PROJECT_NAME} --file ${COMPOSE_FILE}
```

2. Start the stack

```bash
COMPOSE_PROFILES=${COMPOSE_PROFILES} docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} up -d
```

3. Wait for core services to become healthy. Check compose service health:

```bash
docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} ps
```

You should see `healthy` in the STATE column for Postgres, Kafka, and Redis.

4. Check migrations (OpenFGA) completed. If the `openfga-migrate` service exists it should exit with 0 (successful) after applying migrations. If migrations fail with authentication/role errors, see "Troubleshooting — migrations & Postgres".

---

## Canonical takedown (clean and safe)
Use the project's takedown helper to avoid orphan containers and port conflicts.

Dry-run first to see what will be removed:

```bash
./scripts/takedown.sh --dry --project ${PROJECT_NAME} --file ${COMPOSE_FILE}
```

To actually take down and remove volumes and orphans:

```bash
./scripts/takedown.sh --project ${PROJECT_NAME} --file ${COMPOSE_FILE}
```

This will run `docker compose down --volumes --remove-orphans` for the compose file and then remove any leftover containers and the named volumes managed by the stack.

If you need to preserve data, skip the `--volumes` removal step (or pass a modified command):

```bash
COMPOSE_PROFILES=${COMPOSE_PROFILES} docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} down
```

---

## Persistence & data durability
The stack uses named volumes for Postgres, Kafka, and Redis. Named volumes survive `docker compose down` unless you explicitly remove them.

Key volumes (example names):
- `somaagent01_postgres_data`
- `somaagent01_kafka_data`
- `somaagent01_redis_data`

To verify volumes exist:

```bash
docker volume ls | grep ${PROJECT_NAME}
```

To explicitly remove them when you want a clean start:

```bash
docker volume rm somaagent01_postgres_data somaagent01_kafka_data somaagent01_redis_data
```

Be careful: removing volumes deletes data irreversibly.

---

## Secrets and configuration (rotate now)
Do not run this stack in any environment with default secrets. Replace default values immediately.

Files/places to update:
- `infra/docker-compose.somaagent01.yaml` — service envs (GATEWAY_JWT_SECRET, DB passwords, OpenFGA secrets)
- `conf/tenants.yaml` or `conf/model_providers.yaml` if they contain secrets

Recommended approach (local):
1. Create a `.env.production` or similar file outside version control and store secrets there. Example variables:

```text
GATEWAY_JWT_SECRET=replace-with-a-secure-random-hex
POSTGRES_PASSWORD=strong_db_password_here
OPENFGA_DB_PASSWORD=strong_openfga_password_here
```

2. Load them when you run compose (zsh):

```bash
export $(cat .env.production | xargs)
COMPOSE_PROFILES=${COMPOSE_PROFILES} docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} up -d
```

Or reference the `.env` file in the compose file using env_file. Never check `.env.production` into git.

Secrets best-practices:
- Use a secrets manager for production (Vault, AWS Secrets Manager, etc.) and inject secrets at deploy-time.
- Use SCRAM/SHA-256 auth for Postgres when possible.
- Rotate secrets periodically and update running services via rolling restarts.

---

## Smoke tests (basic validation)
Run these after `up` to ensure basic functionality.

1) Gateway health

```bash
curl -f http://localhost:8010/health -sS || echo "gateway health check failed"
```

2) OpenFGA quick check

OpenFGA distributions differ; if `/health` returns 404, try listing stores or hitting the root. Example:

```bash
curl -sS http://localhost:8080/ || echo "openfga root unreachable"
# If OpenFGA exposes v1 API, try:
curl -sS -X GET http://localhost:8080/v1/stores || true
```

3) Agent UI

```bash
curl -f http://localhost:7002/ -sS || echo "agent-ui not reachable"
```

4) Kafka produce/consume (quick)

If you have Kafka CLI tools installed, run:

```bash
# create topic
docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} exec -T kafka kafka-topics.sh --bootstrap-server kafka:9092 --create --topic smoke-test --if-not-exists --partitions 1 --replication-factor 1
# produce
echo "hello" | docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} exec -T kafka kafka-console-producer.sh --broker-list kafka:9092 --topic smoke-test
# consume (in another shell)
docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} exec -T kafka kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic smoke-test --from-beginning --timeout-ms 10000
```

If the produce/consume roundtrip works, Kafka is healthy.

5) Postgres check

```bash
docker compose -f ${COMPOSE_FILE} --project-name ${PROJECT_NAME} exec -T postgres psql -U soma -d somaagent01 -c "SELECT 1;"
```

--

## Troubleshooting (common problems)

1) openfga-migrate fails with authentication/role errors

- Symptom: openfga-migrate logs: `password authentication failed for user 'openfga'` or Postgres logs: `role "openfga" does not exist`.
- Cause: Postgres role or database not created before migrations run (init ordering), or wrong password.
- Fixes:
  - Ensure the init scripts in `infra/postgres/init/` include a script that creates the `openfga` role and the `openfga` database (ordered numerically, e.g., `10-create-openfga-role.sql`, `11-create-openfga-db.sql`).
  - Confirm passwords in compose envs match the role password.
  - If migrations already failed, you can create role and DB manually inside the Postgres container and re-run `openfga-migrate`:

```bash
docker exec -i ${PROJECT_NAME}_postgres sh -c "psql -U soma -d somaagent01 -c \"CREATE ROLE openfga WITH LOGIN PASSWORD 'openfga';\""
docker exec -i ${PROJECT_NAME}_postgres sh -c "psql -U soma -d somaagent01 -c \"CREATE DATABASE openfga OWNER openfga;\""
```

2) Kafka fails to start or repeatedly restarts

- Symptom: Kafka crashes with JVM errors or restart loops.
- Cause: incorrect numeric envs (Java int overflow) or insufficient heap settings.
- Fixes:
  - Ensure numeric limits (message size, buffer size) are <= 2147483647. The compose file uses those values.
  - Set KAFKA_HEAP_OPTS to allocate sufficient memory, e.g., `-Xms1g -Xmx2g` in compose envs.
  - Increase Docker Desktop memory if Kafka OOMs.

3) Port conflicts when restarting

- Use the canonical `./scripts/takedown.sh` to clean or run `docker compose down --remove-orphans` before `up`.

4) Noisy agent-ui downloads or background work

- The UI may start background tasks that produce lots of logs (datasets downloads). If logs are noisy while debugging infra, temporarily stop or block the dataset pipeline by editing the agent config or disabling the datasets feature (see `conf/` or the agent UI config entrypoints).

---

## Maintenance and next steps
- Add a `make smoke` target that runs the smoke checks above. This helps in CI and local verification.
- Put secrets into a real secret manager and wire them into compose at deploy time.
- Add a backups process for Postgres (cron + pg_dump) and for Kafka (if using local persistent topics consider tiered storage or mirror to cloud storage).

---

## Quick reference commands

Start:

```bash
COMPOSE_PROFILES=core,dev docker compose -f infra/docker-compose.somaagent01.yaml --project-name somaagent01 up -d
```

Take down (clean):

```bash
./scripts/takedown.sh --project somaagent01 --file infra/docker-compose.somaagent01.yaml
```

Tail logs (gateway + openfga):

```bash
docker compose -f infra/docker-compose.somaagent01.yaml --project-name somaagent01 logs -f gateway openfga
```

Run smoke tests (simple):

```bash
curl -f http://localhost:8010/health && curl -f http://localhost:7002/ && docker compose -f infra/docker-compose.somaagent01.yaml --project-name somaagent01 exec -T postgres psql -U soma -d somaagent01 -c "SELECT 1;"
```

---

If anything in this document is unclear, tell me which section you'd like expanded. I can also:
- Add the `make smoke` Makefile target now.
- Replace placeholders in `infra/docker-compose.somaagent01.yaml` with `.env.production` variable references and add a `.env.example` (no secrets) to the repo.

End of document.
