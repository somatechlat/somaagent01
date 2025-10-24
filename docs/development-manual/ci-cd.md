# CI/CD Pipeline

This project ships a mode-aware GitHub Actions workflow that builds, scans, and deploys the runtime services via Helm overlays.

## Modes

- dev_full: Local-like defaults, single replicas, lightweight resources.
- dev_prod: Production-like configuration but reduced scale.
- prod: Production configuration and scaling assumptions.
- prod_ha: High-availability overlays for production.

The helper script generates a unified environment file consumed across tools:
- `scripts/generate-global-env.sh <mode> /root/soma-global.env`

## Workflows

Key CI workflows in `.github/workflows/`:

- `ci.yml`: Lints Python and Helm, runs unit tests.
- `ci-kind.yml`: Spins up a KinD cluster and validates infra chart basics.
- `docs.yml` and `docs-quality.yml`: Builds documentation (MkDocs) and performs docs checks.
- `security.yml`: Security scans (e.g., dependency checks or image scanning, if configured).

Typical deployment flow (generic, environment-agnostic):
- Build docs with git plugins disabled by default.
- Build and push container images to your registry.
- Helm lint charts (outbox-sync and the umbrella soma-stack).
- Select overlay by mode and deploy with `helm upgrade --install`.
- Wait for rollout, then run Helm tests (`helm test <release>`).
- On failure, rollback to previous Helm revision.

### Canary deployments (gateway)

The workflow supports an optional canary for the gateway using nginx ingress canary annotations.

Inputs (workflow_dispatch):
- `canaryEnabled`: true/false (default: false)
- `canaryWeight`: percentage 0-100 (default: 10)
- `canaryImageTag`: image tag for the canary (defaults to the built tag)
- `stableImageTag`: optional; if provided, the stable deployment keeps this tag while canary uses `canaryImageTag`.

Chart values (umbrella `soma-stack`):
- `services.gateway.canary.enabled`
- `services.gateway.canary.weight`
- `services.gateway.canary.imageTag`

Requirements:
- nginx ingress controller for canary annotations to take effect.
- `services.gateway.ingress.enabled: true` with appropriate host/class.

## Overlays

The umbrella chart supports overlays in `infra/helm/overlays/`:
- dev-values.yaml
- prod-values.yaml
- prod-ha-values.yaml

These are merged with `infra/helm/soma-stack/values.yaml` during deployment.

## Progressive canary rollout

File: `.github/workflows/canary-progressive.yml`

Purpose: Safely shift traffic to the gateway canary either via nginx ingress canary annotations or Istio VirtualService weights, validating at each step with Helm tests.

Inputs (workflow_dispatch):
- `environment`: dev | prod | prod-ha (selects overlay values file)
- `target`: nginx | istio (canary mechanism)
- `releaseName`: Helm release (default: soma)
- `namespace`: Kubernetes namespace (default: default)
- `chartPath`: Path to umbrella chart (default: infra/helm/soma-stack)
- `canaryImageTag`: Optional canary image tag override

Requirements:
- Cluster access with `KUBE_CONFIG_B64` secret configured in repository secrets (base64-encoded kubeconfig).
- For nginx: `services.gateway.ingress.enabled: true` and nginx ingress controller installed.
- For Istio: `global.ISTIO_ENABLED: true`, `services.gateway.istio.enabled: true`, and a reachable `services.gateway.istio.host` via configured `gateways`.

Flow:
1) Ensures canary is enabled and starts at 5% traffic.
2) Progresses through 10% → 25% → 50% → 75% → 100%.
3) After each shift, runs Helm tests; on failure, rolls back to 0% canary (or 100% stable for Istio) and exits.

## Services

Umbrella chart `infra/helm/soma-stack` deploys:
- gateway (FastAPI, HTTP)
- conversation-worker (metrics exposed)
- tool-executor (metrics exposed)
- delegation-gateway (FastAPI, HTTP)
- delegation-worker
- memory-service (gRPC)
- ui (static FastAPI server)
- outbox-sync (as a dependency chart)

## Metrics

- Scraped directly via Services (metrics ports) or, if Prometheus Operator is present, enable `global.PROM_OPERATOR_ENABLED=true` to render ServiceMonitors.

## Rollback

- The workflow attempts `helm rollback` automatically on failure.
- You can also roll back manually via the Helm history and rollback commands.

