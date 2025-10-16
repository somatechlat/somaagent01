# Shared Infra Runbook (Developer Production Ready)

This runbook describes how to start the consolidated shared infrastructure for the Soma stack using either Docker (local only) or Kubernetes (Kind or a real cluster). The app services (SA01, etc.) will consume these endpoints and should not run their own infra copies.

## Components
- Postgres, Kafka (KRaft), Redis, OPA, OpenFGA (optional), Vault (dev for local), Etcd, Prometheus, Grafana

## Docker (local shared infra only)
- Compose file: infra/docker/shared-infra.compose.yaml
- Exposed ports (host): Postgres 5433, Kafka 9094, Redis 6380, OPA 8182, Vault 8201, Etcd 2380, Prometheus 9091, Grafana 3001
- Contract file: copy infra/env/.env.shared.example to .env.shared and export in your shell. App compose should read from this file.

## Kubernetes (Kind or cluster)
- Chart: infra/helm/soma-infra/
- Values overlays: values-dev.yaml, values-staging.yaml, values-prod.yaml
- Namespace: soma-infra
- Kind config: infra/kind/soma-kind.yaml (reserves host:7002 via NodePort mapping 30080)
- All services are cluster-internal by default. Grafana/Prometheus can be temporarily exposed via NodePort for troubleshooting.

## Health and verification
- Ensure all containers/pods are healthy.
- Verify endpoints: Postgres connectivity, Kafka metadata fetch, Redis PING, OPA responds, Vault dev token works, Etcd health, Prometheus targets, Grafana UI.

## Notes
- Keep the app gateway reserved for host port 7001 (Docker) and 7002 (K8s). Do not map infra to those ports.
- The environment contract keeps Docker and K8s consistent; only hostnames/ports differ.