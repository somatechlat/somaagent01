# SomaAgent01 Kubernetes Deployment (Tilt)

## Overview
Agentic execution tier (L4) for the SOMA Stack. Contains K8s manifests for local development using Tilt + Minikube.

## Prerequisites
- Minikube with `vfkit` driver (macOS)
- Tilt v0.33+
- kubectl configured for `agent` context
- 10GB RAM minimum for VM

## Quick Start
```bash
# Start Minikube profile
minikube start -p agent --driver=vfkit --memory=10240 --cpus=4

# Configure Docker environment
eval $(minikube docker-env -p agent)

# Start Tilt
tilt up --port 10351
```

## Directory Structure
```
infra/k8s/
├── backup/          # Backup configurations
├── shared/          # Shared K8s resources
├── somabrain/       # SomaBrain integration configs
└── somafractalmemory/ # SFM integration configs
```

## Port Sovereignty (L4 - Agent Tier)
| Service | Host Port | Container Port |
|---------|-----------|----------------|
| agent-webui | 20173 | 20173 |
| api | 20181 | 20181 |
| keycloak | 30173 | 8080 |

## Tilt Dashboard
Access at: `http://localhost:10351`

## Commands

```bash
# Start Tilt
tilt up --port 10351

# Check pod status
kubectl get pods -n agent

# View WebUI logs
kubectl logs -f deployment/agent-webui -n agent

# Port-forward WebUI manually
kubectl port-forward svc/agent-webui 20173:20173 -n agent
```

## Integration with SOMA Stack
SomaAgent01 depends on:
- **SomaBrain (L3)**: Cognitive processing (port 20020)
- **SomaFractalMemory (L2)**: Persistent storage (port 10101)

Ensure lower tiers are running before starting Agent tier.

## Troubleshooting

### Keycloak not starting
Check resource limits and increase VM memory to 12GB if needed.

### Cannot connect to SomaBrain
Verify SomaBrain is running and accessible:
```bash
curl http://localhost:20020/health
```
