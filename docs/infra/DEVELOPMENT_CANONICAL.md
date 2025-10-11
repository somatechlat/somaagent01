# Shared Infra — Development Canonical (Setup, Operate, Deploy)

This is the single canonical manual for developing, setting up, and deploying the Soma Shared Infrastructure locally with production semantics. It complements SHARED_INFRA_ARCHITECTURE.md and SPRINTS_SHARED_INFRA.md.

---

## 1) What this is
- A cluster-wide Shared Infra layer used by all Soma stacks.
- Runs on a local Kind cluster with resource-conscious settings; mirrors production contracts (DNS, ports, policy, observability).
- Self-contained under `infra/` and `docs/infra/` so it can move to its own repo without changes.

Core services: Postgres (required), Kafka (KRaft), Redis, OPA (PDP), Vault, Prometheus, Grafana, Etcd; OpenFGA optional.

---

## 2) Prerequisites (local Mac)
- Docker Desktop with ~6–10 CPU, 12–20 GB RAM, 50–100 GB disk for volumes.
- Kind cluster (context `kind-soma` recommended). A Kind config is provided at `infra/kind/soma-kind.yaml`.
- kubectl and helm installed.

---

## 3) Install paths

### A. Docker (shared infra only)
- Compose file: `infra/docker/shared-infra.compose.yaml`
- Env: `infra/env/.env.shared.example` (copy to your env if needed)
- Bring up:
  - Postgres, Kafka, Redis, OPA, Vault, Etcd, Prometheus, Grafana (dev-sized, persistent volumes where needed)

### B. Kubernetes (Kind) — recommended
- Namespace: `soma-infra`
- Chart: `infra/helm/soma-infra`
- Overlays: `values-dev.yaml` (Kind), `values-staging.yaml`, `values-prod.yaml`

---

## 4) Contracts (consumers rely on these)
- DNS and ports:
  - `postgres.soma-infra.svc.cluster.local:5432`
  - `kafka.soma-infra.svc.cluster.local:9092`
  - `redis.soma-infra.svc.cluster.local:6379`
  - `opa.soma-infra.svc.cluster.local:8181`
  - `vault.soma-infra.svc.cluster.local:8200`
  - `prometheus.soma-infra.svc.cluster.local:9090`
  - `grafana.soma-infra.svc.cluster.local:3000`
  - `etcd.soma-infra.svc.cluster.local:2379`
- Identity: JWKS URL (dev issuer now; pluggable IdP later)
- Policy: OPA decision path `/v1/data/soma/allow` with inputs `{identity, request, service, tenant, context}`

---

## 5) Security & policy
- Kubernetes: NetworkPolicies (default-deny); PodSecurity (restricted); runAsNonRoot; read-only root FS; probes & limits.
- Secrets: Vault in dev mode OK; no secrets in images; JWKS-only for apps.
- OPA: default-deny, service-to-service allowlist, tenant enforcement, budgets/routing.

---

## 6) Observability
- Prometheus scrapes all shared components; scrape interval 15s (5s on demand).
- Grafana baseline dashboards for Postgres, Kafka, Redis, OPA, Vault.
- OTEL endpoints configurable; Jaeger/Loki optional.

---

## 7) Sizing (Kind)
- Postgres: 500m CPU / 1–2 GiB RAM; PVC 5–10 GiB
- Kafka: 1 CPU / 2–4 GiB RAM; PVC 10–20 GiB; short retention
- Redis: 200–300m CPU / 512 MiB RAM; AOF everysec; allkeys-lru
- OPA: 100–200m CPU / 256–512 MiB RAM
- Prometheus: 500m–1 CPU / 2–4 GiB RAM; Grafana small

---

## 8) Readiness checklist (Kind)
- Pods Ready; Services routable.
- Postgres SELECT 1; Redis PING; Kafka metadata; OPA allow/deny; Vault health; Etcd health.
- Prom targets up; (optional) Grafana reachable.
- NetworkPolicies enforced (deny by default; labeled allows present).
- JWKS and OPA decision path published to app teams.

---

## 9) Day-2 operations (dev)
- Backups (optional): small pg_dump; keep Kafka retention short; monitor Prom metrics.
- Policy iteration: update OPA bundle ConfigMap; verify with contract tests.
- Secrets: rotate dev signing keys in Vault; JWKS URL remains stable for apps.

---

## 10) Ready-to-split guidance
- No app dependencies; infra stands alone under `infra/` and `docs/infra/`.
- To split: subtree-export `infra/` and `docs/infra/` to a new repo; publish Helm via OCI/Pages.
- Consumers keep DNS, ports, JWKS, and OPA contracts; no code changes required.

---

## 11) References
- `docs/infra/SHARED_INFRA_ARCHITECTURE.md`
- `docs/infra/SPRINTS_SHARED_INFRA.md`
- `docs/infra/runbook_shared_infra.md`
