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
- staging-values.yaml
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
- ui (static FastAPI server)
- outbox-sync (as a dependency chart)

## Metrics

- Scraped directly via Services (metrics ports) or, if Prometheus Operator is present, enable `global.PROM_OPERATOR_ENABLED=true` to render ServiceMonitors.

## Rollback

- The workflow attempts `helm rollback` automatically on failure.
- You can also roll back manually via the Helm history and rollback commands.


## Additional options

Istio reliability policies (optional):
- Configure `services.gateway.istio.trafficPolicy` for connection pooling and outlier detection.
- Configure `services.gateway.istio.http` for `timeout` and `retries`.
These render into DestinationRule/VirtualService and apply to both stable and canary subsets.

Dev overlay with ingress and local hosts:
- `infra/helm/overlays/dev-values.yaml` enables nginx ingress and sets hosts to `*.127.0.0.1.sslip.io` so they resolve to localhost without edits.
	- Gateway: `gateway.127.0.0.1.sslip.io`
	- UI: `ui.127.0.0.1.sslip.io`
	- UI Proxy: `uip.127.0.0.1.sslip.io`

Autoscaling and network policies (optional):
- Toggle `global.HPA_ENABLED` and per-service `services.*.hpa.enabled` to render HPAs (CPU-based by default).
- Toggle `global.NETWORK_POLICY_ENABLED` to apply a conservative, namespace-only allow policy plus DNS egress.

### Private container registries

If your images are hosted in a private registry, configure image pull secrets in the charts:

- Umbrella chart (`soma-stack`): set `global.imagePullSecrets` to a list of Kubernetes secret names.
- Infra chart (`soma-infra`): set `imagePullSecrets` to a list of Kubernetes secret names.

Example (values overlay):

```yaml
global:
	imagePullSecrets:
		- my-regcred
```

Infra chart:

```yaml
imagePullSecrets:
	- my-regcred
```

Notes

- The referenced secrets must exist in the target namespace before deployment.
- Create them with your registry credentials using a `docker-registry` type secret.
- Both the stable and canary Deployments inherit these settings.

### TLS and cert-manager

- Apps (umbrella chart) now accept a global issuer name: `global.CERT_MANAGER_CLUSTER_ISSUER`.
	- In prod overlays we set `letsencrypt-prod` and remove per-service annotations.
	- You can still set per-service `services.*.ingress.annotations` to override.
- Infra chart (soma-infra) can install a `ClusterIssuer`:
	- In prod overlay we enable cert-manager and set the ACME production server.
	- For staging, use `letsencrypt-staging` and the staging ACME URL.

Mode-to-domain-and-cert mapping:

- dev_full: dev overlay (`dev-values.yaml`)
	- Hosts: `*.127.0.0.1.sslip.io`
	- Certs: none by default (global issuer empty)
- dev_prod: staging overlay (`staging-values.yaml`)
	- Hosts: `*.staging.soma.internal`
	- Certs: Let's Encrypt staging (global issuer `letsencrypt-staging`), infra staging ClusterIssuer enabled
- prod: prod overlay (`prod-values.yaml`)
	- Hosts: `*.prod.soma.internal`
	- Certs: Let's Encrypt production (global issuer `letsencrypt-prod`), infra prod ClusterIssuer enabled
- prod_ha: prod-ha overlay (`prod-ha-values.yaml`)
	- Hosts: `*.prod-ha.soma.internal`
	- Certs: Let's Encrypt production (global issuer `letsencrypt-prod`), infra prod ClusterIssuer enabled

### Network policies

- Enable app-side policies via `global.NETWORK_POLICY_ENABLED`.
- Cross-namespace egress can be allowed by label:
	- `global.NETWORK_POLICY_ALLOWED_NAMESPACE_LABEL.key`
	- `global.NETWORK_POLICY_ALLOWED_NAMESPACE_LABEL.value`
- Infra chart allows ingress from namespaces labeled with the same key/value (default: `soma.sh/allow-shared-infra: "true"`). Ensure your app namespace has this label to permit traffic to infra services.

### KinD convenience for ingress ports

- A KinD config at `infra/kind/soma-kind-ingress.yaml` maps host ports 80/443 to the ingress-nginx NodePorts (30080/30443).
- Use `scripts/kind-create-ingress.sh` to create this cluster.

