---
title: Deployment
---

# Deployment

## Environments

| Environment | Purpose | Notes |
| --- | --- | --- |
| Local Dev | Feature development, manual QA | `make dev-up` |
| Staging | Pre-production validation | Mirrors prod configuration, uses real providers |
| Production | Live users | Hardened networking, autoscaling |

## Configuration Matrix

| Config | Local | Staging | Production |
| --- | --- | --- | --- |
| `GATEWAY_REQUIRE_AUTH` | false | true | true |
| `OPENAI_API_KEY` | .env | Secret manager | Secret manager |
| Kafka | Docker compose | Managed cluster | Managed cluster |
| Postgres | Docker compose | Managed instance | Managed HA cluster |

## Build Pipeline

1. Run tests locally (`pytest`, Playwright).
2. Build images: `docker build -f Dockerfile -t somaagent01:latest .` or `docker compose -f docker-compose.yaml build`.
3. Push to registry (tag with git SHA, semantic version).
4. Deploy via Compose (staging) or Helm (production).

## Docker Compose Deployment (Staging)

```bash
git pull
docker compose -p somaagent01-staging --profile core --profile dev -f docker-compose.yaml up -d
```

- Use `.env.staging` for environment-specific overrides.
- Confirm health: `docker compose ps`.
- Host ports default to the reserved range `20000-20199` (Kafka 20000, Redis 20001, Postgres 20002, Gateway 20016, UI 20015). Override via `PORT_POOL_START` / `PORT_POOL_MAX` if the range is occupied.
- SomaBrain integration expects `http://host.docker.internal:9696`; ensure your local SomaBrain service is listening on that port (set via `SOMA_BASE_URL`).

## Kubernetes Deployment (Planned)

- Helm chart (`deploy/helm/somaagent01`) will manage:
	- StatefulSets for Postgres/Kafka/Redis
	- Deployments for Gateway, UI, Tool Executor
	- ConfigMaps for prompts, settings defaults
	- Secrets for API keys, credentials
- Ingress exposes Gateway + UI via HTTPS.

## Rolling Update Procedure

1. Scale Gateway to zero traffic (if load balancer supports draining).
2. Apply new build (`docker compose up -d gateway` or `helm upgrade`).
3. Monitor health checks, metrics, logs.
4. Re-enable traffic.
5. Run smoke tests.

## Rollback

- Docker: `docker compose up -d gateway=<previous-tag>`.
- Helm: `helm rollback somaagent01 <revision>`.
- Ensure database migrations are backward compatible or have rollback scripts.

## Environment Promotion Checklist

- [ ] Tests green (unit, integration, E2E).
- [ ] Release notes updated.
- [ ] Config parity reviewed (feature flags, API keys).
- [ ] Observability dashboards verified.
- [ ] Incident response contacts updated.

## Secrets Management

- Local: `.env` (never commit). The runtime also supports file- and base64-based secrets automatically.
- Staging/Prod: use a secret manager (Vault, AWS/GCP/Azure Secrets). Inject as files or env vars.

Resolution order for any KEY (first non-empty wins):

1) `KEY`
2) `KEY_FILE` → read file contents, strip trailing newline
3) `KEY_B64` → base64 decode value
4) `KEY_B64_FILE` → read file and base64 decode

Examples:

- `SLM_API_KEY_FILE=/var/run/secrets/slm_api_key`
- `OPENAI_API_KEY_FILE=/run/secrets/openai_api_key`
- `REDIS_PASSWORD_FILE=/run/secrets/redis_password`
- `GATEWAY_JWT_SECRET_FILE=/run/secrets/gateway_jwt_secret`

Kubernetes:

- Mount a Secret as a file and set `*_FILE` to the mount path.
- Prefer files over plain env vars to reduce accidental leaks in process dumps.

Vault:

- JWT HS secrets can be hydrated from Vault with `GATEWAY_JWT_VAULT_PATH`, `GATEWAY_JWT_VAULT_SECRET_KEY` (see gateway README/comments). For other keys, prefer mounting via CSI driver or syncing to K8s Secrets and using `*_FILE`.

## Compliance & Audit

- Record deployment metadata in `docs/changelog.md`.
- Tag git release (`git tag vX.Y.Z`).
- Store build artifacts and configuration in artifact repository.
