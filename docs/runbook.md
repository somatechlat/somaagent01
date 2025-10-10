# Runbook: Deploying Soma Infra and Stack Locally

This document provides a quick‑start guide for developers who want to spin up the
shared infrastructure (`soma‑infra`) and the full Soma stack (`soma‑stack`) in a
local Kubernetes cluster using **Kind**.

## Prerequisites

* **Docker** (>= 24.x) – required by Kind.
* **kubectl** – version that matches the Kind node image.
* **kind** – install via `brew install kind` (macOS) or the official binary.
* **helm** – version 3.12+.
* **Python 3.11+** with the project virtual‑env activated (see `README.md`).

## Step‑by‑Step

1. **Create a Kind cluster**
   ```bash
   kind create cluster --name soma-dev
   ```

2. **Load local Docker images** (if you have built custom images for the
   services, e.g., `agent-zero`):
   ```bash
   docker build -t agent-zero:dev .
   kind load docker-image agent-zero:dev --name soma-dev
   ```

3. **Install the shared infra chart**
   ```bash
   helm repo add soma-infra file://infra/helm/soma-infra
   helm install soma-infra soma-infra/soma-infra \
        --namespace soma --create-namespace \
        -f infra/helm/soma-infra/values.yaml
   ```

   This will deploy Auth, OPA, Kafka, Redis, Prometheus, Grafana, Vault and the
   newly added Etcd chart.

4. **Deploy the application stack** (replace with your own chart if you have a
   `soma-stack` chart):
   ```bash
   helm install soma-stack path/to/your/soma-stack/chart \
        --namespace soma --create-namespace
   ```

5. **Verify the deployment**
   ```bash
   kubectl get pods -n soma
   kubectl get svc -n soma
   ```

   You should see all services in `Running` state and the service IPs/ports.

6. **Access the UI**
   Forward the UI service locally:
   ```bash
   kubectl port-forward svc/soma-ui 8080:80 -n soma
   ```
   Then open <http://localhost:8080> in a browser.

## Cleanup

When you are done, delete the Kind cluster:
```bash
kind delete cluster --name soma-dev
```

---

Feel free to extend this runbook with additional steps such as loading test
data, running integration tests, or configuring TLS certificates.
