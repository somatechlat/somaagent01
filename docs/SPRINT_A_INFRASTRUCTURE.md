⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# Sprint A: Infrastructure & Deployment
**Duration**: 2 weeks (parallel with Sprints B, C, D)  
**Goal**: Enable Kubernetes deployment with GitOps and CI/CD automation

---

## 🎯 OBJECTIVES

1. Create production-ready Kubernetes manifests
2. Establish GitOps workflows with Argo CD
3. Build CI/CD pipelines for automated testing and deployment
4. Add smoke tests for local development validation

---

## 📦 DELIVERABLES

### 1. Kubernetes Base Manifests (`infra/k8s/base/`)

#### 1.1 Namespace Definition
**File**: `infra/k8s/base/namespace.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: somaagent01
  labels:
    name: somaagent01
    environment: base
```

#### 1.2 Gateway Deployment
**File**: `infra/k8s/base/gateway-deployment.yaml`
- Deployment with 3 replicas
- Resource requests/limits
- Liveness and readiness probes
- ConfigMap for environment variables
- Secret references for JWT keys

#### 1.3 Conversation Worker Deployment
**File**: `infra/k8s/base/conversation-worker-deployment.yaml`
- StatefulSet with 2 replicas
- Kafka consumer group affinity
- Volume mounts for models cache

#### 1.4 Tool Executor Deployment
**File**: `infra/k8s/base/tool-executor-deployment.yaml`
- Deployment with autoscaling (HPA)
- Sandbox security context
- Resource quotas

#### 1.5 Supporting Services
- `delegation-gateway-deployment.yaml`
- `delegation-worker-deployment.yaml`
- `router-deployment.yaml`
- `canvas-service-deployment.yaml`
- `requeue-service-deployment.yaml`
- `settings-service-deployment.yaml`

#### 1.6 Service Definitions
- `gateway-service.yaml` (LoadBalancer)
- `router-service.yaml` (ClusterIP)
- `canvas-service.yaml` (ClusterIP)
- `delegation-gateway-service.yaml` (ClusterIP)
- `settings-service.yaml` (ClusterIP)

#### 1.7 ConfigMaps
**File**: `infra/k8s/base/configmap.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: somaagent-config
data:
  SOMA_AGENT_MODE: "PRODUCTION"
  KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
  POSTGRES_DSN: "postgresql://soma:soma@postgres:5432/somaagent01"
  REDIS_URL: "redis://redis:6379"
  LOG_LEVEL: "INFO"
```

#### 1.8 Secrets Template
**File**: `infra/k8s/base/secrets-template.yaml`
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: somaagent-secrets
type: Opaque
stringData:
  GATEWAY_JWT_SECRET: "<vault-ref>"
  KAFKA_SASL_PASSWORD: "<vault-ref>"
  POSTGRES_PASSWORD: "<vault-ref>"
```

#### 1.9 Kustomization
**File**: `infra/k8s/base/kustomization.yaml`
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: somaagent01
resources:
  - namespace.yaml
  - gateway-deployment.yaml
  - gateway-service.yaml
  - conversation-worker-deployment.yaml
  - tool-executor-deployment.yaml
  - delegation-gateway-deployment.yaml
  - delegation-gateway-service.yaml
  - router-deployment.yaml
  - router-service.yaml
  - canvas-service-deployment.yaml
  - canvas-service-service.yaml
  - requeue-service-deployment.yaml
  - settings-service-deployment.yaml
  - configmap.yaml
  - secrets-template.yaml
```

### 2. Environment Overlays (`infra/k8s/overlays/`)

#### 2.1 Local/Dev Overlay
**Directory**: `infra/k8s/overlays/dev/`
- Reduced replicas (1 per service)
- Lower resource limits
- NodePort services
- Development secrets

**File**: `infra/k8s/overlays/dev/kustomization.yaml`
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: somaagent01-dev
bases:
  - ../../base
patchesStrategicMerge:
  - patches/replicas.yaml
  - patches/resources.yaml
  - patches/nodeport.yaml
configMapGenerator:
  - name: somaagent-config
    behavior: merge
    literals:
      - SOMA_AGENT_MODE=DEVELOPMENT
      - LOG_LEVEL=DEBUG
```

#### 2.2 Production Overlay
**Directory**: `infra/k8s/overlays/prod/`
- High availability (3+ replicas)
- Production resource limits
- LoadBalancer services
- Vault secret injection
- Network policies
- Pod disruption budgets

### 3. Helm Charts (`infra/helm/somaagent/`)

#### 3.1 Chart.yaml
```yaml
apiVersion: v2
name: somaagent01
description: SomaAgent 01 Helm chart
version: 0.1.0
appVersion: "1.0.0"
dependencies:
  - name: kafka
    version: "26.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: kafka.enabled
  - name: redis
    version: "18.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
  - name: postgresql
    version: "13.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
```

#### 3.2 values.yaml
- Default configuration values
- Service-specific settings
- Resource limits
- Scaling parameters

#### 3.3 Templates
- Deployments, Services, ConfigMaps, Secrets
- HorizontalPodAutoscalers
- NetworkPolicies
- ServiceAccounts with RBAC

### 4. GitOps Configuration

#### 4.1 Argo CD Application
**File**: `infra/gitops/somaagent-app.yaml`
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: somaagent01
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/agent0ai/agent-zero
    targetRevision: main
    path: infra/k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: somaagent01
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### 5. CI/CD Pipelines

#### 5.1 GitHub Actions Workflow
**File**: `.github/workflows/ci.yaml`
```yaml
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/
      
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install ruff mypy
      - run: ruff check services/
      - run: mypy services/
      
  build:
    runs-on: ubuntu-latest
    needs: [test, lint]
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: agent0ai/somaagent:${{ github.sha }}
          
  deploy-dev:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v4
      - run: kubectl apply -k infra/k8s/overlays/dev
```

#### 5.2 Dagger Pipeline
**File**: `ci/main.py`
```python
import dagger
from dagger import dag, function, object_type

@object_type
class SomaAgentCI:
    @function
    async def test(self) -> str:
        """Run pytest test suite"""
        return await (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "-r", "requirements.txt"])
            .with_exec(["pytest", "tests/", "-v"])
            .stdout()
        )
    
    @function
    async def lint(self) -> str:
        """Run linting and type checks"""
        return await (
            dag.container()
            .from_("python:3.11-slim")
            .with_exec(["pip", "install", "ruff", "mypy"])
            .with_exec(["ruff", "check", "services/"])
            .with_exec(["mypy", "services/"])
            .stdout()
        )
```

### 6. Smoke Tests

#### 6.1 Docker Compose Smoke Test
**File**: `tests/smoke/test_local_stack.py`
```python
"""Smoke tests for local docker-compose stack"""
import httpx
import pytest
import time

@pytest.fixture(scope="module")
def wait_for_services():
    """Wait for all services to be ready"""
    time.sleep(10)  # Grace period
    yield

def test_gateway_health(wait_for_services):
    response = httpx.get("http://localhost:8010/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]

def test_kafka_connectivity(wait_for_services):
    response = httpx.get("http://localhost:8010/health")
    data = response.json()
    assert "kafka" in data["components"]
    assert data["components"]["kafka"]["status"] == "ok"

def test_end_to_end_message(wait_for_services):
    # Send message
    payload = {
        "message": "Smoke test message",
        "metadata": {}
    }
    response = httpx.post("http://localhost:8010/v1/session/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    session_id = data["session_id"]
    
    # Verify event in Kafka (via gateway health or session query)
    time.sleep(2)
    # Additional verification...
```

#### 6.2 Smoke Test Runner
**File**: `scripts/run_smoke_tests.sh`
```bash
#!/bin/bash
set -e

echo "Starting docker-compose stack..."
docker-compose -f infra/docker-compose.somaagent01.yaml up -d

echo "Waiting for services to be ready..."
sleep 15

echo "Running smoke tests..."
pytest tests/smoke/ -v

echo "Smoke tests passed! Cleaning up..."
docker-compose -f infra/docker-compose.somaagent01.yaml down
```

---

## 🔧 IMPLEMENTATION TASKS

### Week 1
- [ ] Create base Kubernetes manifests for all services
- [ ] Create Kustomize overlays for dev/prod
- [ ] Build Helm chart structure
- [ ] Write smoke tests for docker-compose
- [ ] Create GitHub Actions workflow (basic)

### Week 2
- [ ] Complete Helm chart templates
- [ ] Add Argo CD application manifests
- [ ] Implement Dagger pipeline
- [ ] Add resource quotas and network policies
- [ ] Test deployment to dev Kubernetes cluster
- [ ] Document deployment procedures

---

## ✅ ACCEPTANCE CRITERIA

1. ✅ All services have Kubernetes manifests with proper resource limits
2. ✅ Kustomize overlays work for dev and prod environments
3. ✅ Helm chart can deploy full stack with single command
4. ✅ Argo CD syncs and deploys automatically
5. ✅ GitHub Actions pipeline runs tests and builds images
6. ✅ Smoke tests pass on local docker-compose
7. ✅ Services deploy and pass health checks in dev cluster
8. ✅ Documentation covers deployment procedures

---

## 📊 SUCCESS METRICS

- **Deployment Time**: < 5 minutes from commit to running in dev
- **Smoke Test Coverage**: 100% of critical paths
- **CI/CD Reliability**: > 95% success rate
- **GitOps Sync**: < 2 minutes from merge to deployment

---

## 🚀 NEXT STEPS

After Sprint A completion:
1. Deploy to staging environment
2. Run load tests against Kubernetes deployment
3. Enable production rollout with canary deployment
4. Integrate with monitoring (Sprint C)
