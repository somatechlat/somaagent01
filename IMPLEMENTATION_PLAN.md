# 🚀 SRS Implementation Plan - SomaAgent01

**Based on:** SRS_GAP_ANALYSIS.md  
**Timeline:** 16 weeks (4 months)  
**Approach:** Parallel execution across 3 tracks  

---

## 📊 Implementation Strategy

### Track 1: Core Platform (Weeks 1-8)
**Owner:** Backend Team  
**Focus:** Orchestrator + Role Agents

### Track 2: Observability (Weeks 1-6)
**Owner:** DevOps Team  
**Focus:** Dashboards + Kubernetes

### Track 3: Validation (Weeks 7-16)
**Owner:** QA Team  
**Focus:** Benchmarks + Testing

---

## 🎯 Milestone Breakdown

### M1: Orchestrator Engine (Weeks 1-3)

**Goal:** Implement LangGraph-style state machine

**Tasks:**
1. Create `services/orchestrator/` service
2. Define state nodes: Plan, Recall, ToolSelect, Execute, Observe, Reflect, Verify, Commit
3. Implement checkpoint persistence in Postgres
4. Add Kafka events for state transitions
5. Integrate with existing conversation worker

**Files to Create:**
- `services/orchestrator/main.py`
- `services/orchestrator/state_machine.py`
- `services/orchestrator/checkpoints.py`
- `services/orchestrator/nodes/plan.py`
- `services/orchestrator/nodes/recall.py`
- `services/orchestrator/nodes/tool_select.py`
- `services/orchestrator/nodes/execute.py`
- `services/orchestrator/nodes/observe.py`
- `services/orchestrator/nodes/reflect.py`
- `services/orchestrator/nodes/verify.py`
- `services/orchestrator/nodes/commit.py`

**Files to Modify:**
- `services/conversation_worker/main.py` - delegate to orchestrator
- `docker-compose.yaml` - add orchestrator service

**Acceptance Criteria:**
- [ ] State machine executes full cycle
- [ ] Checkpoints persist to Postgres
- [ ] Kafka events published per state
- [ ] Integration test passes

---

### M2: Role-Based Agents (Weeks 4-5)

**Goal:** Create Researcher, Coder, Operator profiles

**Tasks:**
1. Create prompt profiles in `agents/researcher/`, `agents/coder/`, `agents/operator/`
2. Define tool scoping per role
3. Update agent initialization to load role configs
4. Add role selection API endpoint

**Files to Create:**
- `agents/researcher/prompts/agent.system.main.md`
- `agents/researcher/config.yaml`
- `agents/coder/prompts/agent.system.main.md`
- `agents/coder/config.yaml`
- `agents/operator/prompts/agent.system.main.md`
- `agents/operator/config.yaml`

**Files to Modify:**
- `agent.py` - load role config
- `services/gateway/main.py` - add role selection endpoint

**Acceptance Criteria:**
- [ ] Three roles defined with distinct prompts
- [ ] Tool scoping enforced per role
- [ ] API endpoint returns available roles
- [ ] Integration test with each role

---

### M3: Observability Dashboard (Weeks 1-6)

**Goal:** Build React dashboard with visualizations

**Tasks:**
1. Setup Next.js project in `dashboard/`
2. Create Plan Graph visualization (D3.js)
3. Create Agent Hierarchy tree view
4. Embed Prometheus metrics (iframe or API)
5. Embed Jaeger traces (iframe or API)
6. Create Kafka stream viewer
7. Deploy Grafana with pre-built dashboards

**Files to Create:**
- `dashboard/package.json`
- `dashboard/pages/index.tsx`
- `dashboard/components/PlanGraph.tsx`
- `dashboard/components/AgentHierarchy.tsx`
- `dashboard/components/MetricsPanel.tsx`
- `dashboard/components/TracesPanel.tsx`
- `dashboard/components/KafkaStream.tsx`
- `infra/grafana/dashboards/overview.json`
- `infra/grafana/dashboards/agents.json`

**Files to Modify:**
- `docker-compose.yaml` - add dashboard + grafana services

**Acceptance Criteria:**
- [ ] Dashboard accessible at localhost:3000
- [ ] Plan Graph renders state transitions
- [ ] Metrics display in real-time
- [ ] Traces link to Jaeger
- [ ] Kafka stream shows live events

---

### M4: Benchmark Harness (Weeks 7-9)

**Goal:** Implement WebArena, GAIA, SWE-bench runners

**Tasks:**
1. Create `benchmarks/` directory structure
2. Implement dataset loaders
3. Create evaluation metrics
4. Build runner framework
5. Add Kafka publisher for results
6. Create benchmark results API

**Files to Create:**
- `benchmarks/runner.py`
- `benchmarks/datasets/webarena.py`
- `benchmarks/datasets/gaia.py`
- `benchmarks/datasets/swebench.py`
- `benchmarks/evaluators/webarena_eval.py`
- `benchmarks/evaluators/gaia_eval.py`
- `benchmarks/evaluators/swebench_eval.py`
- `benchmarks/kafka_publisher.py`

**Files to Modify:**
- `services/gateway/main.py` - add benchmark results endpoint
- `docker-compose.yaml` - add benchmark service

**Acceptance Criteria:**
- [ ] All three benchmarks run successfully
- [ ] Results published to Kafka
- [ ] CSV/JSON export works
- [ ] API returns benchmark history

---

### M5: Kubernetes Deployment (Weeks 3-6)

**Goal:** Create Helm charts for production deployment

**Tasks:**
1. Create Helm chart structure
2. Define Deployments for all services
3. Add ConfigMaps and Secrets
4. Configure HPA (Horizontal Pod Autoscaler)
5. Add liveness/readiness probes
6. Create Ingress for gateway
7. Document deployment process

**Files to Create:**
- `helm/somaagent01/Chart.yaml`
- `helm/somaagent01/values.yaml`
- `helm/somaagent01/templates/gateway-deployment.yaml`
- `helm/somaagent01/templates/conversation-worker-deployment.yaml`
- `helm/somaagent01/templates/tool-executor-deployment.yaml`
- `helm/somaagent01/templates/orchestrator-deployment.yaml`
- `helm/somaagent01/templates/kafka-statefulset.yaml`
- `helm/somaagent01/templates/redis-deployment.yaml`
- `helm/somaagent01/templates/postgres-statefulset.yaml`
- `helm/somaagent01/templates/ingress.yaml`
- `helm/somaagent01/templates/hpa.yaml`
- `docs/deployment/kubernetes.md`

**Acceptance Criteria:**
- [ ] Helm install succeeds
- [ ] All pods reach Ready state
- [ ] HPA scales based on load
- [ ] Ingress routes traffic correctly
- [ ] Health probes work

---

### M6: CI/CD Pipeline (Weeks 7-8)

**Goal:** Automate testing and deployment

**Tasks:**
1. Create GitHub Actions workflows
2. Add unit test job
3. Add integration test job
4. Add Docker build and push
5. Add Helm chart linting
6. Add canary deployment workflow
7. Configure ArgoCD (optional)

**Files to Create:**
- `.github/workflows/test.yml`
- `.github/workflows/build.yml`
- `.github/workflows/deploy.yml`
- `.github/workflows/canary.yml`

**Files to Modify:**
- `Makefile` - add CI targets

**Acceptance Criteria:**
- [ ] Tests run on every PR
- [ ] Docker images pushed on merge
- [ ] Helm charts validated
- [ ] Canary deployment works

---

### M7: Compliance & Security (Weeks 9-10)

**Goal:** GDPR compliance and Vault integration

**Tasks:**
1. Implement data retention policies
2. Create GDPR deletion endpoint
3. Integrate HashiCorp Vault
4. Add secret rotation logic
5. Create example OPA policies
6. Document compliance features

**Files to Create:**
- `services/gateway/gdpr.py`
- `services/common/vault_client.py`
- `policies/examples/tool_access.rego`
- `policies/examples/tenant_isolation.rego`
- `docs/compliance/gdpr.md`

**Files to Modify:**
- `services/gateway/main.py` - add GDPR endpoints
- `services/common/settings.py` - add Vault config

**Acceptance Criteria:**
- [ ] GDPR deletion removes all user data
- [ ] Secrets loaded from Vault
- [ ] OPA policies enforce access control
- [ ] Audit logs retained 90 days

---

### M8: Load Testing & Validation (Weeks 11-16)

**Goal:** Validate performance and reliability

**Tasks:**
1. Create Locust load test scenarios
2. Run 100 concurrent agent test
3. Run 500 concurrent agent test
4. Identify bottlenecks
5. Optimize critical paths
6. Create performance runbook
7. Final acceptance testing

**Files to Create:**
- `tests/load/locustfile.py`
- `tests/load/scenarios/conversation.py`
- `tests/load/scenarios/tool_execution.py`
- `docs/operations/performance_runbook.md`

**Acceptance Criteria:**
- [ ] 100 concurrent agents sustained
- [ ] 500 concurrent agents sustained
- [ ] P95 latency < 2s
- [ ] No memory leaks
- [ ] All benchmarks pass

---

## 📅 Gantt Chart (Text)

```
Week  | 1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16
------|------------------------------------------------
M1    |███████████
M2    |         ███████
M3    |███████████████████
M4    |                  ███████████
M5    |      ███████████████
M6    |                  ███████
M7    |                        ███████
M8    |                           ███████████████████████
```

---

## 🔧 Development Workflow

### Week 1-3: Orchestrator Foundation
```bash
# Create orchestrator service
mkdir -p services/orchestrator/nodes
touch services/orchestrator/{main,state_machine,checkpoints}.py

# Implement state nodes
for node in plan recall tool_select execute observe reflect verify commit; do
  touch services/orchestrator/nodes/${node}.py
done

# Add to docker-compose
# Test with existing conversation worker
```

### Week 4-5: Role Profiles
```bash
# Create role directories
for role in researcher coder operator; do
  mkdir -p agents/${role}/prompts
  touch agents/${role}/config.yaml
done

# Write prompts
# Update agent.py
# Test role switching
```

### Week 7-9: Benchmarks
```bash
# Setup benchmark framework
mkdir -p benchmarks/{datasets,evaluators}
touch benchmarks/runner.py

# Download datasets
# Implement evaluators
# Run first benchmark
```

---

## ✅ Success Criteria

### Technical Metrics
- [ ] All 18 SRS requirements implemented
- [ ] Test coverage ≥ 85%
- [ ] P95 latency < 2s
- [ ] 99.9% uptime in staging
- [ ] Zero critical security vulnerabilities

### Business Metrics
- [ ] Benchmark scores published
- [ ] Documentation complete
- [ ] Production deployment successful
- [ ] Customer pilot launched

---

## 🚨 Risk Mitigation

### Risk 1: Orchestrator Complexity
**Mitigation:** Start with simple state machine, iterate

### Risk 2: Dashboard Performance
**Mitigation:** Use server-side rendering, lazy loading

### Risk 3: Benchmark Dataset Availability
**Mitigation:** Start with GAIA (public), defer SWE-bench

### Risk 4: Kubernetes Learning Curve
**Mitigation:** Use managed services (EKS/GKE), hire consultant

---

## 📞 Team Structure

### Backend Team (3 engineers)
- Orchestrator implementation
- Role-based agents
- Benchmark harness

### DevOps Team (2 engineers)
- Kubernetes deployment
- CI/CD pipeline
- Observability stack

### Frontend Team (2 engineers)
- Dashboard UI
- Grafana dashboards
- Documentation site

### QA Team (1 engineer)
- Load testing
- Integration testing
- Compliance validation

---

**END OF IMPLEMENTATION PLAN**
