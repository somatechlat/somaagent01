---
title: Operational Runbooks
slug: dev-runbooks
version: 1.0.0
last-reviewed: 2025-10-15
audience: developers, sre
owner: platform-operations
reviewers:
  - platform-engineering
prerequisites:
  - Access to Kubernetes cluster or local environment
verification:
  - Runbooks executed successfully during drills
---

# Operational Runbooks

These runbooks capture repeatable operational tasks for developers and SREs. Update them after every drill or significant change.

## 1. Deploy Soma Infra & Stack Locally (Kind)

**Purpose:** Validate full stack changes against a local Kubernetes cluster.

**Procedure:**

```bash
# Create cluster
kind create cluster --name soma-dev

# Load custom image (optional)
docker build -t agent-zero:dev .
kind load docker-image agent-zero:dev --name soma-dev

# Install shared infra
helm upgrade --install soma-infra infra/helm/soma-infra \
  --namespace soma --create-namespace \
  -f infra/helm/values-dev.yaml

# Install application stack
helm upgrade --install soma-stack infra/helm/soma-stack \
  --namespace soma \
  -f infra/helm/values-dev.yaml

# Verify
kubectl get pods -n soma
kubectl get svc -n soma
```

**Verification:** All pods `Running`; `/health` endpoint returns `200` after port-forwarding `gateway` service.

**Cleanup:** `kind delete cluster --name soma-dev`.

## 2. Restart Conversation Worker in Production

1. Authenticate with `kubectl` (`kubectx` to prod cluster).
2. Identify deployment: `kubectl get deploy -n soma-prod | grep conversation-worker`.
3. Restart: `kubectl rollout restart deploy/conversation-worker -n soma-prod`.
4. Monitor rollout: `kubectl rollout status deploy/conversation-worker -n soma-prod`.
5. Verify metrics dashboard shows healthy request rate.

## 3. Rotate Soma SLM API Key

1. Generate new key via internal portal.
2. Store in Vault path `kv/slm/api-key` with metadata.
3. Update `.env` (dev) or Helm secret values (prod).
4. Trigger rollout of gateway and conversation worker.
5. Run smoke test to confirm authentication.
6. Update [`docs/changelog.md`](../changelog.md) with rotation details.

## 4. Restore Backup

1. Download backup archive from secure storage.
2. Upload via UI (**Settings → Backup → Restore**).
3. Choose overwrite or preserve settings.
4. Confirm knowledge files, memory, and chats restored correctly.
5. Document restoration in `changelog` and incident tracker.

## 5. Emergency Shutdown

1. Notify stakeholders on `#soma-oncall`.
2. Disable public tunnels: turn off Cloudflare tunnel in UI or revoke token.
3. Scale deployments to zero: `kubectl scale deploy --all --replicas=0 -n soma-prod`.
4. Revoke API keys via Vault.
5. Document actions and start incident response procedure (see [Security Manual](../technical-manual/security.md)).

## Maintenance

- Review runbooks quarterly.
- Capture lessons learned from incidents and update procedures.
- Link to supporting diagrams or scripts where applicable.
