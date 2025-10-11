# Agent Zero — Canonical Roadmap (Shared Infra + K8s parity)

Last updated: 2025-10-10
Branch: soma_integration

This is the canonical roadmap for delivering strict runtime parity between Docker and Kubernetes (Kind/Helm) for the Soma Agent 01 (SA01) scope, consolidating a Shared Infra layer and enforcing a single Dockerfile and a single Compose file for the app.

## Objectives

- Parity: “Run the whole cluster exactly as the one in Docker that works perfectly, but on Kubernetes.”
- Canonical build: One Dockerfile for all services using build args; one app Compose file.
- Port policy: App gateway on host 7001 (Docker) and on host 7002 (K8s via Kind NodePort/Ingress).
- Shared Infra first: Treat Shared Infra as its own project, production-ready for developers, consumed by app-only stacks.
- No mocks: Real services (Postgres, Kafka, Redis, OPA, Vault, Etcd, Prometheus, Grafana, optional OpenFGA/Jaeger/Loki).

## Constraints

- Single Dockerfile (DockerfileLocal) with SERVICE and K8S build args.
- Single app Compose file for SA01; a separate Docker Compose file exists only for Shared Infra.
- Stable endpoints contract via .env for Docker and cluster DNS for K8s.
- Keep SA01 scope; do not widen beyond documented services.

## Deliverables

1) Shared Infra (Docker) — docker/compose with durable volumes, health checks, and ports
2) Shared Infra (K8s via Kind) — Helm umbrella `infra/helm/soma-infra` with values overlays (dev/staging/prod)
3) SA01 App (Docker) — app-only compose pointing to Shared Infra
4) SA01 App (K8s) — Helm umbrella `soma-stack`, gateway on 7002
5) Observability & Policy — Prometheus/Grafana, OPA policies, optional OpenFGA/Jaeger/Loki
6) CI & GitOps — CI builds single Dockerfile images, spins Kind, installs charts, runs smoke tests; GitOps path outlined

## Milestones and acceptance criteria

M1 — Shared Infra up on Docker (COMPLETE)
- Services: Postgres (host 5436), Kafka (9094), Redis (6380), OPA (8182->8181), Vault (8201), Etcd (2380), Prometheus (9091), Grafana (3001)
- Acceptance: All containers Up/healthy; env contract `.env.shared` published; runbook in `docs/infra/runbook_shared_infra.md`.

M2 — Shared Infra up on Kind (IN PROGRESS)
- Helm chart `infra/helm/soma-infra` with `values-dev.yaml`; namespace `soma`.
- Acceptance: All pods Ready; services and endpoints present; Prometheus targets healthy.

M3 — Auth service + OPA policy bootstrap (PLANNED)
- Real JWT auth service (local mode), OPA policy decision path wired, minimal policies shipped; optional OpenFGA migration job.
- Acceptance: Policy decisions reachable; sample allow/deny evaluated via HTTP; audit logs visible.

M4 — SA01 app-only on Docker (PLANNED)
- App services built from single Dockerfile; gateway on 7001; memory-service gRPC 50052; use Shared Infra endpoints; no bind mounts that mask deps.
- Acceptance: App HTTP /health OK, gRPC memory happy path OK, Kafka in/out OK.

M5 — SA01 app on Kind (PLANNED)
- Helm umbrella `soma-stack`; gateway exposed on host 7002 (Kind NodePort); wired to Shared Infra DNS.
- Acceptance: Same smoke tests as Docker; gateway reachable on 7002.

M6 — Observability extras (OPTIONAL)
- Jaeger and/or Loki opt-in; baseline Grafana dashboards and scrape annotations present.
- Acceptance: Traces/logs visible; key dashboards render without errors.

M7 — CI pipeline + GitOps outline (PLANNED)
- CI builds single Dockerfile images, launches Kind, installs `soma-infra` then `soma-stack`, runs smoke tests; document ArgoCD path for clusters.
- Acceptance: CI green with infra+app smoke tests; docs include GitOps flow.

## Environment contract

- Docker (developer): Apps consume Shared Infra via `.env.shared` (ports listed in M1). App gateway must bind host 7001.
- K8s (Kind): Apps use cluster DNS names configured in Helm values. App gateway exposed on host 7002.

## References

- Helm: `infra/helm/soma-infra` (overlays: dev, staging, prod)
- Docker Compose (Shared Infra): `infra/docker/shared-infra.compose.yaml`
- Runbook: `docs/infra/runbook_shared_infra.md`
- Environment example: `infra/env/.env.shared.example`

## How to maintain

- Update this roadmap by PR when milestones change. Keep acceptance criteria concrete and verifiable. Avoid widening the SA01 scope.

---
Generated/maintained to reflect the integrated shared-infra-first plan and Kubernetes parity as of 2025-10-10.
