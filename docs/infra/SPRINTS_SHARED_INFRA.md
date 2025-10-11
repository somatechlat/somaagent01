# Shared Infra Sprints (Exec Plan)

This is the sprint-level execution plan to deliver the Shared Infra layer on a local Kind cluster with production semantics, and to make it ready for standalone reuse.

## Sprint 0 — Foundations (done/ongoing)
- Create umbrella chart `infra/helm/soma-infra` with dev/staging/prod values overlays.
- Add Docker compose `infra/docker/shared-infra.compose.yaml` (dev-only).
- Add Kind cluster config `infra/kind/soma-kind.yaml` mapping 7002 for app gateway.
- Publish env contract `infra/env/.env.shared.example`.
- Runbook `docs/infra/runbook_shared_infra.md`.

Acceptance: repo contains these assets; no app coupling; docs explain contracts.

## Sprint 1 — Bring-up on Kind (current)
- Create namespace `soma-infra`.
- Install `soma-infra` with values-dev: Postgres, Kafka, Redis, OPA, Prometheus, Grafana, Vault, Etcd (OpenFGA optional off).
- Health checks: psql SELECT 1, Redis PING, Kafka metadata, OPA allow/deny, Vault dev, Etcd health.
- Prometheus targets show Up; (optional) Grafana accessible.
- NetworkPolicies: default-deny + allows from app namespaces by label.

Acceptance: Readiness report with Pods/Services/Endpoints + checks above.

## Sprint 2 — Identity and Policy Baseline
- Dev JWT issuer (JWKS URL stable) or select IdP (Keycloak/Auth0/Okta) and wire JWKS.
- OPA policy bundle v1: inputs schema, default-deny, tenant, roles/scopes, s2s allowlist, budgets/routing.
- Document decision path and test vectors; add contract tests to CI.

Acceptance: JWT validation OK across sample services; OPA decisions enforced in sample requests.

## Sprint 3 — Security & K8s Baseline
- Enforce PodSecurity (restricted), non-root users, read-only root FS.
- Add NetworkPolicies to all shared services; verify denies and allows.
- Ensure probes/limits everywhere; add HPAs only where suitable (OPA/Prometheus optional).

Acceptance: Policy checks pass; kube-bench-like baseline satisfied (dev profile).

## Sprint 4 — Observability & SLOs
- Prometheus dashboards for Postgres/Kafka/Redis/OPA/Vault; scrape 15s; retention 1–3 days.
- Optional: Jaeger/Loki add-ons; wire OTLP endpoint variable.
- Alert rules: error rate, latency, consumer lag; document initial SLOs.

Acceptance: Dashboards render; alerts fire in synthetic scenarios.

## Sprint 5 — Data & DR Planning
- Define prod HA path: Postgres (Patroni/Crunchy), Kafka (Strimzi), Redis Operator.
- Backups: Postgres PITR, retention plans; Kafka retention; Redis backups as needed.
- DR runbooks; smoke recovery test in CI.

Acceptance: DR docs/runbooks land; basic recovery validated.

## Sprint 6 — Supply Chain & GitOps
- SBOM (Syft), image scanning (Trivy), image signing (Cosign) baked into CI.
- Chart testing; Kind ephemeral env in CI; helm upgrade --install smoke.
- Argo CD app-of-apps outline for infra; values promotion strategy.

Acceptance: CI green; artifacts signed; GitOps path documented.

## Sprint 7 — Ready-to-Split Packaging
- values.schema.json; chart Lint PASS; OCI/Pages publishing instructions.
- MIGRATION.md for splitting infra into its own repo; consumers keep DNS contracts.

Acceptance: One command to publish chart; consumers can depend without code changes.
