---
title: Infrastructure & Deployment Blueprint
slug: technical-infrastructure
version: 1.0.0
last-reviewed: 2025-10-15
audience: platform-engineers, SRE
owner: platform-operations
reviewers:
  - infra
  - sre
prerequisites:
  - Access to SomaAgent01 repository
  - Permissions to run Docker and Helm
verification:
  - Docker Compose stack boots locally
  - Helm release succeeds in Kind or target cluster
---

# Infrastructure & Deployment Blueprint

This blueprint documents how SomaAgent01 is provisioned across local, staging, and production environments. It covers Docker Compose profiles, Helm chart structure, configuration management, and verification routines.

## 1. Local Environment (Docker Compose)

Compose file: `infra/docker-compose.somaagent01.yaml`

### Profiles

| Profile | Services | Purpose |
| ------- | -------- | ------- |
| `default` | gateway, ui, conversation_worker, memory_service, tool_executor | Base runtime |
| `vectorstore` | qdrant, pgvector | Advanced memory features |
| `observability` | prometheus, grafana, loki (optional) | Local observability |
| `kafka` | kafka, schema-registry | Streaming use cases |

### Bring-Up Command

```bash
COMPOSE_PROFILES=default,vectorstore docker compose -f infra/docker-compose.somaagent01.yaml up --build
```

**Verification:**
- `docker compose ps` shows containers healthy.
- `curl http://localhost:8010/health` returns `200`.

## 2. Cluster Deployments (Helm)

Charts live under `infra/helm/`.

- `soma-infra/`: shared infrastructure (Auth, OPA, Kafka, Redis, Prometheus, Grafana, Vault, Etcd).
- `soma-stack/`: application bundle (gateway, conversation worker, memory service, UI, tool executor).

### Install Flow

```bash
# Bootstrap Kind cluster for validation
kind create cluster --name soma

# Install shared infra
target=dev
helm upgrade --install soma-infra infra/helm/soma-infra \
  -n soma-$target --create-namespace \
  -f infra/helm/values-$target.yaml

# Install application stack
helm upgrade --install soma-stack infra/helm/soma-stack \
  -n soma-$target \
  -f infra/helm/values-$target.yaml
```

**Verification:**
- `kubectl get pods -n soma-dev` shows all pods `Running`.
- Port-forward gateway (`kubectl port-forward svc/gateway 8010:8010`) and hit `/health`.
- Run smoke tests: `poetry run python scripts/smoke_test.py --env dev`.

## 3. Configuration Management

- **Base settings:** `common/config/settings.py` (Pydantic models).
- **Environment overrides:** `infra/helm/values-<env>.yaml`.
- **Secrets:** Stored in Vault; templated via Helm and injected using Vault Agent sidecars.
- **Feature flags:** Sourced from Etcd (`feature_flag_endpoint`), cached in Redis, with updates broadcast over the `config.updates` Kafka topic.

## 4. CI/CD Integration

GitHub Actions workflow: `.github/workflows/ci.yml` (existing) + `docs-quality.yml` (added in this sprint).

Pipeline stages:
1. Lint Python (`ruff`, `mypy`).
2. Run unit and integration tests (`pytest`).
3. Provision Kind cluster, install `soma-infra` and `soma-stack` charts.
4. Execute smoke tests and publish artifacts.
5. Trigger documentation workflow (link checking, markdown lint, MkDocs build).

## 5. Change Management

- Infrastructure changes require entries in [`docs/changelog.md`](../changelog.md).
- Update Helm chart versions in `Chart.yaml` and `values-*.yaml`.
- Tag releases following `v<major>.<minor>.<patch>` and attach Helm package artifacts.

## 6. Disaster Recovery

- **Backups:**
  - State stores (Redis, Kafka) rely on cloud snapshots (documented in `infra/helm/soma-infra/backup/`).
  - Qdrant backups stored in object storage with lifecycle policies.
- **Failover:** Cloudflare Load Balancer or Route53 handles region traffic shifts.
- **RPO/RTO:** Target RPO 15 minutes, RTO 60 minutes. Validate quarterly via failover drills.

## 7. Operational Runbooks

Runbooks relocate to the Development Manual (`../development-manual/runbooks.md`) but referenced here for completeness:

- Start/stop sequences
- Log collection
- Scaling events

## 8. Verification Checklist

- [ ] Compose stack validated locally.
- [ ] Helm deployment validated in Kind.
- [ ] Vault and OPA sidecars injected successfully.
- [ ] Smoke tests green.
- [ ] Documentation updated and linted.
