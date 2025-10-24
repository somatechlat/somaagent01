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
  - `make dev-up` succeeds
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

## 5. Start the Stack

```bash
make dev-up
```

- Gateway available at `http://localhost:${GATEWAY_PORT:-20016}`.
- UI (when started) available at `http://localhost:${AGENT_UI_PORT:-20015}`.
- Logs tail via `make dev-logs`.

**Verification:**
- `docker compose -p somaagent01 ps` shows services healthy.
- `curl http://localhost:${GATEWAY_PORT:-20016}/health` returns `200`.

## 6. Testing

```bash
pytest
pytest tests/playwright/test_realtime_speech.py --headed
```

## 7. Common Tasks

| Task | Command |
| ---- | ------- |
| Stop stack | `make dev-down` |
| Rebuild stack | `make dev-rebuild` |
| Tail a specific service | `make dev-logs-svc SERVICES=gateway` |
| Start selected services | `make dev-up-services SERVICES="gateway tool-executor"` |
| Clean volumes | `make clean` |
| Lint Python | `ruff check .` |
| Format Python | `black .` |

## 8. Local Docker Compose Reference

- Single compose file `docker-compose.yaml` drives local development.
- Profiles:
  - `core`: Kafka (`${KAFKA_PORT:-20000}`), Redis (`${REDIS_PORT:-20001}`), Postgres (`${POSTGRES_PORT:-20002}`), OPA (`${OPA_PORT:-20009}`).
  - `dev`: Gateway (`${GATEWAY_PORT:-20016}`), Conversation Worker, Tool Executor, Agent UI (`${AGENT_UI_PORT:-20015}`).
- Bring-up examples:
  - `docker compose -p somaagent01 --profile core --profile dev -f docker-compose.yaml up -d`
  - `docker compose -p somaagent01 --profile core -f docker-compose.yaml up -d kafka redis postgres`
- Recommended Docker Desktop allocation: ≥8 CPUs, ≥12 GB RAM to keep Kafka/Postgres healthy.
- Frequently used containers:
  - `somaAgent01_gateway` → `http://localhost:${GATEWAY_PORT:-20016}`
  - `somaAgent01_agent-ui` → `http://localhost:${AGENT_UI_PORT:-20015}`
  - `somaAgent01_tool-executor`
  - `somaAgent01_conversation-worker`
- Verification checklist after `docker compose up`:
  1. `curl http://localhost:${GATEWAY_PORT:-20016}/health`
  2. `docker compose -p somaagent01 ps` shows services `healthy`
  3. `docker exec somaAgent01_postgres psql -U soma -d somaagent01 -c "SELECT NOW();"`
- Troubleshooting quick hits:
  - Port clash on Kafka (`9092`): set `KAFKA_PORT` in `.env` or stop conflict.
  - Gateway 5xx on boot: wait for OPA/OpenFGA migrations to finish.
  - High CPU idle: disable optional profiles or lower `WHISPER_MODEL`.

## 9. IDE Configuration

- VS Code recommended with Python and Docker extensions.
- Select `.venv` interpreter.
- Use `.vscode/launch.json` launchers for `run_ui.py` and `run_tunnel.py`.

## 10. Troubleshooting

- **Docker missing:** Install from [docker.com](https://www.docker.com/products/docker-desktop/).
- **Port conflicts:** Adjust `WEB_UI_PORT` before invoking `make dev-up`.
- **Realtime speech issues:** Verify API keys and inspect `python/api/realtime_session.py` logs.

Once the environment is verified, continue with the [Contribution Workflow](./contribution-workflow.md).

## 11. Optional: Enable SSO/JWT in Dev

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

## 12. Local ingress and TLS on this machine (optional)

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
