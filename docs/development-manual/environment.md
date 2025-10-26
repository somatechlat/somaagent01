---
title: Environment Setup
slug: dev-environment
version: 1.0.0
last-reviewed: 2025-10-15
audience: contributors
owner: developer-experience
reviewers:
  - platform-engineering
prerequisites:
  - macOS/Linux (Windows via WSL2)
  - Docker Desktop 4.36+
  - Python 3.12+
verification:
  - `make deps-up` succeeds
  - `make stack-up` streams healthy logs
  - `pytest` passes locally
---

# Environment Setup

Follow these steps to prepare a fully functional SomaAgent01 development environment.

## 1. Clone the Repository

```bash
git clone https://github.com/agent0ai/agent-zero.git
cd agent-zero
```

## 2. Python Runtime

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Verify:

```bash
python -V  # Should return 3.12.x
pip check  # No broken dependencies
```

## 3. Frontend Dependencies

```bash
cd webui
npm install
cd ..
```

Verify: `npm run lint` passes.

## 4. Environment Variables

1. Copy `.env.example` to `.env`.
2. Provide required keys:
   - `SLM_API_KEY` (or alternate model provider).
   - `POSTGRES_DSN`, `REDIS_URL` if using external services.

## 5. Bring Up Shared Dependencies

The Python services now run directly inside your virtualenv. Only the shared
infrastructure (Kafka, Redis, Postgres, OPA) stays in Docker:

```bash
make deps-up
```

- Kafka → `localhost:${KAFKA_PORT:-21000}`
- Redis → `localhost:${REDIS_PORT:-21001}`
- Postgres → `localhost:${POSTGRES_PORT:-21002}`
- OPA → `http://localhost:${OPA_PORT:-21009}`

Tail dependency logs with `make deps-logs`. Stop them via `make deps-down`.

**Verification:**

```bash
docker compose -p somaagent01_deps -f docker-compose.dependencies.yaml ps
curl http://localhost:${OPA_PORT:-21009}/health | jq
pg_isready -h localhost -p ${POSTGRES_PORT:-21002} -d somaagent01 -U soma
```

## 6. Start Gateway & Workers Locally

```bash
make stack-up
```

This runs:

- `uvicorn services.gateway.main:app --host 0.0.0.0 --port ${GATEWAY_PORT:-21016}`
- `python -m services.conversation_worker.main`
- `python -m services.tool_executor.main`
- `python -m services.memory_replicator.main`
- `python -m services.memory_sync.main`
- `python -m services.outbox_sync.main`

Use `Ctrl+C` to stop the stack. For auto-reload on Gateway code changes, run
`make stack-up-reload`.

**Verification:**

```bash
curl http://localhost:${GATEWAY_PORT:-21016}/health
```

## 7. Run Agent UI Locally

```bash
make ui   # http://127.0.0.1:3000
```

Ensure `.env` has `UI_USE_GATEWAY=true` and `UI_GATEWAY_BASE` pointed at the
local Gateway (`http://127.0.0.1:${GATEWAY_PORT:-21016}`).

## 8. Testing

```bash
pytest
pytest tests/playwright/test_realtime_speech.py --headed
```

## 9. Common Tasks

| Task | Command |
| ---- | ------- |
| Stop Python services | `Ctrl+C` in the terminal running `make stack-up` |
| Stop dependencies | `make deps-down` |
| Tail dependencies | `make deps-logs` |
| Full Docker stack (legacy) | `make dev-up` |
| Full Docker teardown | `make dev-down` |
| Rebuild Docker images | `make dev-rebuild` |
| Clean volumes | `make clean` |
| Lint Python | `ruff check .` |
| Format Python | `black .` |

## 10. Local Docker Compose Reference

- `docker-compose.dependencies.yaml` now contains only Kafka/Redis/Postgres/OPA.
- Default `docker-compose.yaml` still builds the full deployment (Gateway,
  workers, Agent UI). Use this for production parity or CI:
  - `docker compose -p somaagent01 --profile core --profile dev up -d`
  - UI exposed at `http://localhost:${AGENT_UI_PORT:-21015}` when using Docker.
- Recommended Docker Desktop allocation: ≥8 CPUs, ≥12 GB RAM.
- Troubleshooting:
  - Port clash on Kafka (`9092`): adjust `KAFKA_PORT` or stop the conflicting
    process.
  - Gateway 5xx on Docker boot: wait for OPA migrations.
  - High CPU idle: stop unused services or run via `make stack-up` instead of
    full Docker.

## 11. IDE Configuration

- VS Code recommended with Python and Docker extensions.
- Select `.venv` interpreter.
- Use `.vscode/launch.json` launchers for `run_ui.py` and `run_tunnel.py`.

## 12. Troubleshooting

- **Docker missing:** Install from [docker.com](https://www.docker.com/products/docker-desktop/).
- **Port conflicts:** Adjust `WEB_UI_PORT` before invoking `make dev-up`.
- **Realtime speech issues:** Verify API keys and inspect `python/api/realtime_session.py` logs.

Once the environment is verified, continue with the [Contribution Workflow](./contribution-workflow.md).

## 13. Optional: Enable SSO/JWT in Dev

The gateway supports JWT auth for local development. Choose one of the following and export as environment variables before `make dev-up` (or set in your shell):

HS256 (shared secret)

```bash
export GATEWAY_REQUIRE_AUTH=true
export GATEWAY_JWT_SECRET=dev-secret
export GATEWAY_JWT_ALGORITHMS=HS256
```

JWKS (OIDC provider like Auth0/Okta/Entra)

```bash
export GATEWAY_REQUIRE_AUTH=true
export GATEWAY_JWKS_URL="https://YOUR_DOMAIN/.well-known/jwks.json"
export GATEWAY_JWT_ALGORITHMS=RS256
export GATEWAY_JWT_AUDIENCE="api://somaagent01"
export GATEWAY_JWT_ISSUER="https://YOUR_DOMAIN/"
```

Notes

- Admin-only endpoints require a scope claim containing `admin` or `keys:manage`.
- Tenant is derived from the first matching claim in `GATEWAY_JWT_TENANT_CLAIMS` (default: `tenant,org,customer`).
- Health endpoints remain open for readiness checks.

## 14. Local ingress and TLS on this machine (optional)

You can expose the app via ingress locally and optionally enable TLS.

- Quickest: HTTP only (default). Uses sslip.io hostnames without certificates.
- Self-signed TLS: cert-manager issues self-signed certs (untrusted by browsers).
- Trusted local TLS: Use mkcert to create a local CA and configure cert-manager with a CA issuer.

### Option A — HTTP only (default)

1) Create a KinD cluster that maps host 80/443 to ingress NodePorts:
   - Optional script: `scripts/kind-create-ingress.sh`
2) Install infra for dev with ingress-nginx:
   - `helm upgrade --install soma-infra infra/helm/soma-infra -f infra/helm/soma-infra/values-dev.yaml`
3) Install app with dev overlay (hosts on sslip.io):
   - `helm upgrade --install soma infra/helm/soma-stack -f infra/helm/overlays/dev-values.yaml`
4) Visit:
   - http://gateway.127.0.0.1.sslip.io/
   - http://ui.127.0.0.1.sslip.io/
   - http://uip.127.0.0.1.sslip.io/

### Option B — Self-signed TLS (cert-manager)

Pros: automated certs via cert-manager. Cons: browser warning (untrusted).

1) Enable cert-manager self-signed issuer in infra:
   - `helm upgrade --install soma-infra infra/helm/soma-infra -f infra/helm/soma-infra/values-dev.yaml -f infra/helm/soma-infra/values-dev-tls.yaml`
2) Enable TLS on app ingresses and point to the dev issuer:
   - `helm upgrade --install soma infra/helm/soma-stack -f infra/helm/overlays/dev-values.yaml -f infra/helm/overlays/dev-tls-values.yaml`
3) Access the HTTPS endpoints (expect a certificate warning):
   - https://gateway.127.0.0.1.sslip.io/
   - https://ui.127.0.0.1.sslip.io/
   - https://uip.127.0.0.1.sslip.io/

### Option C — Trusted local TLS (mkcert + cert-manager CA)

Pros: Browser-trusted TLS locally. Cons: slightly more setup.

1) Install mkcert (macOS):
   - `brew install mkcert nss`
   - `mkcert -install`  # installs local CA to Keychain/System trust
2) Find mkcert CA root directory:
   - `mkcert -CAROOT`
3) Create a Kubernetes secret with the mkcert CA key and cert (development only):
   - `kubectl -n soma-infra create secret tls mkcert-ca --cert="$CAROOT/rootCA.pem" --key="$CAROOT/rootCA-key.pem"`
4) Configure cert-manager CA issuer (infra):
   - Create or edit a values file with:
     ```yaml
     certManager:
       enabled: true
       type: ca
       clusterIssuer:
         name: mkcert-ca
       ca:
         secretName: mkcert-ca
     ```
   - Apply: `helm upgrade --install soma-infra infra/helm/soma-infra -f infra/helm/soma-infra/values-dev.yaml -f <your-ca-values>.yaml`
5) Point the app to the mkcert issuer and enable TLS on ingresses:
   - Create or edit an overlay with:
     ```yaml
     global:
       CERT_MANAGER_CLUSTER_ISSUER: mkcert-ca
     services:
       gateway:
         ingress:
           tls:
             - hosts: [gateway.127.0.0.1.sslip.io]
               secretName: gateway-dev-tls
       ui:
         ingress:
           tls:
             - hosts: [ui.127.0.0.1.sslip.io]
               secretName: ui-dev-tls
       uiProxy:
         ingress:
           tls:
             - hosts: [uip.127.0.0.1.sslip.io]
               secretName: uip-dev-tls
     ```
   - Deploy: `helm upgrade --install soma infra/helm/soma-stack -f infra/helm/overlays/dev-values.yaml -f <your-app-dev-tls-values>.yaml`
6) Visit HTTPS endpoints; they should be trusted by your browser.

Notes
- For network policies, label your app namespace to allow access to infra:
  - `kubectl label namespace <app-namespace> soma.sh/allow-shared-infra="true" --overwrite`
- If using KinD convenience, see `scripts/kind-create-ingress.sh` and `infra/kind/soma-kind-ingress.yaml`.

### Option D — Trusted local TLS (custom OpenSSL CA, no mkcert)

Pros: Trusted TLS without installing mkcert. Cons: You still need to trust a local CA in macOS.

1) Generate a local CA (OpenSSL):
  - `./scripts/dev-ca/generate-dev-ca.sh "Soma Dev Local CA"`
  - Output: `scripts/dev-ca/ca/dev-ca.key.pem` and `dev-ca.crt.pem`
2) Trust the CA in macOS (requires sudo):
  - `sudo ./scripts/dev-ca/install-macos-trust.sh scripts/dev-ca/ca/dev-ca.crt.pem`
3) Create Kubernetes secret for cert-manager CA issuer:
  - `./scripts/dev-ca/create-k8s-secret.sh soma-infra dev-ca scripts/dev-ca/ca/dev-ca.key.pem scripts/dev-ca/ca/dev-ca.crt.pem`
4) Install infra with CA issuer:
  - `helm upgrade --install soma-infra infra/helm/soma-infra -f infra/helm/soma-infra/values-dev.yaml -f infra/helm/soma-infra/values-dev-ca.yaml`
5) Install app with dev CA overlay:
  - `helm upgrade --install soma infra/helm/soma-stack -f infra/helm/overlays/dev-values.yaml -f infra/helm/overlays/dev-ca-values.yaml`
6) Open HTTPS endpoints (should be trusted):
  - https://gateway.127.0.0.1.sslip.io/
  - https://ui.127.0.0.1.sslip.io/
  - https://uip.127.0.0.1.sslip.io/
