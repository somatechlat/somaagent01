# Shared Infra Architecture (Prod-like Development)

This document defines the canonical Shared Infrastructure layer for the entire Soma Stack. It is designed to run on a local Kind cluster with production semantics and be lifted into a standalone repository without changes.

## Scope
- Namespace: `soma-infra`
- Shared services: Postgres (required), Kafka (KRaft), Redis, OPA (central PDP), Vault, Prometheus, Grafana, Etcd; OpenFGA optional (off by default)
- Contracts only; no app code. Stable DNS and port contracts across environments.

## DNS and Ports (ClusterIP)
- `postgres.soma-infra.svc.cluster.local:5432`
- `kafka.soma-infra.svc.cluster.local:9092`
- `redis.soma-infra.svc.cluster.local:6379`
- `opa.soma-infra.svc.cluster.local:8181`
- `vault.soma-infra.svc.cluster.local:8200`
- `prometheus.soma-infra.svc.cluster.local:9090`
- `grafana.soma-infra.svc.cluster.local:3000`
- `etcd.soma-infra.svc.cluster.local:2379`
- `openfga.soma-infra.svc.cluster.local:8080` (optional)

Gateway external ports reserved for apps only: Docker 7001; Kind 7002.

## Security and Policy
- Authentication: JWT + JWKS contract. Dev issuer now; pluggable IdP (Keycloak/Auth0/Okta) later without app changes.
- Authorization: OPA central PDP, decision path `/v1/data/soma/allow`, default-deny, s2s allowlist, tenancy, budgets/routing.
- Kubernetes: NetworkPolicies (default-deny), PodSecurity (restricted), runAsNonRoot, read-only root FS, probes and limits required.
- Secrets: Vault (dev mode locally; CSI/Agent in prod). No private keys in images.

## Persistence and Backups
- Postgres: single StatefulSet in dev; HA (Patroni/Crunchy) in prod. PITR and backup verification in prod.
- Kafka: single broker and short retention in dev; Strimzi multi-broker in prod.
- Redis: single instance with AOF and allkeys-lru in dev; Redis Operator with TLS/ACLs in prod.
- Etcd: single in dev; 3-node in prod.

## Observability
- Prometheus + Grafana baseline. Metrics labels: `service, instance, env, version`.
- OpenTelemetry endpoints configurable; Jaeger optional. Loki optional for logs.

## Isolation and Portability
- All assets under `infra/` and `docs/infra/`. No references to app code or paths.
- Values-driven configuration (dev/staging/prod overlays). StorageClass, namespace, and resources configurable.
- Ready to split into a separate repo; publish as Helm repo or OCI.

## Acceptance (Dev Kind)
- Pods Ready; Services routable.
- Health checks pass: Postgres SELECT 1; Redis PING; Kafka metadata; OPA allow/deny; Vault dev health; Etcd health.
- Prom targets up; (optional) Grafana reachable.
- NetworkPolicies enforce default-deny; app namespace allowed to shared infra by label.
- JWKS URL and OPA decision path published for all apps.
