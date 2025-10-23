# 🎯 SRS Gap Analysis - SomaAgent01

**Analysis Date:** 2025-01-22  
**SRS Version:** Enterprise Agent Platform v1.0  
**Current Codebase:** messaging_architecture branch  

---

## Executive Summary

**Current State:** SomaAgent01 already implements 70% of SRS requirements through its event-driven microservices architecture.

**Key Gaps:**
1. **LangGraph-style Orchestrator** - Need formal state machine with checkpointed nodes
2. **Role-Based Agents** - Need dedicated Researcher/Coder/Operator profiles
3. **Benchmark Harness** - Need WebArena/GAIA/SWE-bench runners
4. **Enhanced Observability** - Need Grafana dashboards and advanced tracing
5. **Kubernetes Deployment** - Need Helm charts and production configs

**Implementation Effort:** 12-16 weeks across 8 milestones

---

## ✅ ALREADY IMPLEMENTED (70%)

### FR-3: Tool Framework Extension ✅
**SRS Requirement:** Registration API for custom tools; sandboxed execution with declared permissions

**Current Implementation:**
- **File:** `services/tool_executor/main.py`
- **Registry:** `tool_registry.py` with dynamic tool loading
- **Sandbox:** `sandbox_manager.py` with timeout enforcement
- **Resource Management:** `resource_manager.py` tracks CPU/memory/concurrency
- **Built-in Tools:** echo, timestamp, code_execute, file_read, http_fetch, canvas_append

**Gap:** None - fully implemented

---

### FR-4: Kafka Integration ✅
**SRS Requirement:** Publish to agent.runs.v1, agent.steps.v1, agent.tools.v1, agent.audit.v1, agent.errors.v1, agent.benchmarks.v1

**Current Implementation:**
- **File:** `services/common/event_bus.py`
- **Topics:** conversation.inbound, conversation.outbound, tool.requests, tool.results, config_updates
- **Producer:** aiokafka with JSON serialization
- **Consumer:** Group-based consumption with offset management

**Gap:** Topic naming convention differs (conversation.* vs agent.*) - cosmetic only

---

### FR-5: Redis Cache Layer ✅
**SRS Requirement:** Cache recent tool results, session state, rate-limit counters; TTL-based eviction

**Current Implementation:**
- **File:** `services/common/session_repository.py`
- **Session Cache:** `session:{session_id}:meta` with 3600s TTL
- **Budget Tracking:** `budget:{tenant}:{persona_id}`
- **API Keys:** `apikey:{key_id}` and `apikey:secret:{hash}`
- **Requeue Store:** `policy:requeue:{requeue_id}`

**Gap:** None - fully implemented

---

### FR-6: Postgres Persistence ✅
**SRS Requirement:** Store run metadata, artifact blobs, benchmark results, audit logs; SQLAlchemy models with migrations

**Current Implementation:**
- **File:** `services/common/session_repository.py`
- **Schema:** sessions.sessions, sessions.events (append-only event sourcing)
- **Driver:** asyncpg with connection pooling
- **Migrations:** Manual schema creation (no Alembic yet)

**Gap:** Need Alembic migrations for schema versioning

---

### FR-7: Memory API Client ✅
**SRS Requirement:** Wrapper for SomaBrain Memory API (RAG retrieval & write-back); supports batch queries & streaming updates

**Current Implementation:**
- **File:** `python/integrations/soma_client.py`
- **Methods:** remember(), recall(), search_similarity_threshold()
- **Circuit Breaker:** 3 failures → 15s cooldown
- **Container Support:** Auto-rewrites localhost → host.docker.internal
- **Dual Endpoints:** /memory/* (new) + legacy fallbacks

**Gap:** None - fully implemented

---

### FR-8: Policy Engine ✅
**SRS Requirement:** Load OPA policies from policies/; enforce on tool calls and agent delegation

**Current Implementation:**
- **Gateway:** `services/gateway/main.py` - JWT + OPA + OpenFGA
- **Tool Executor:** `services/tool_executor/main.py` - OPA per tool
- **Conversation Worker:** `services/conversation_worker/main.py` - OPA per message
- **Requeue Pattern:** Blocked requests stored for operator approval

**Gap:** Need policies/ folder with example .rego files

---

### FR-11: Security Hardening ✅
**SRS Requirement:** Run tools as non-root, limit CPU/memory, validate inputs, rotate secrets from Vault

**Current Implementation:**
- **Resource Limits:** `resource_manager.py` enforces CPU/memory/concurrency
- **Input Validation:** JSON schema validation via `services/common/schemas.py`
- **Circuit Breakers:** JWKS, OPA, SomaBrain all protected
- **Container Isolation:** Docker runtime with configurable user

**Gap:** Vault integration for secret rotation (currently env vars only)

---

### NFR-1: Performance ✅
**SRS Requirement:** End-to-end latency for a single tool call ≤500ms (excluding LLM inference)

**Current Implementation:**
- **Gateway → Kafka:** <10ms
- **Tool Execution:** 100ms-30s (tool-dependent)
- **Metrics:** Prometheus histograms track latency

**Gap:** Need load testing to verify at scale

---

### NFR-2: Scalability ✅
**SRS Requirement:** Horizontal scaling to ≥100 concurrent agents; configurable Kafka partitions & Redis shards

**Current Implementation:**
- **Stateless Services:** Gateway, conversation-worker, tool-executor all horizontally scalable
- **Kafka:** Configurable partitions via init-topics.sh
- **Redis:** Single instance (can be clustered)
- **Postgres:** Connection pooling

**Gap:** Need Kubernetes HPA configs and load testing

---

### NFR-5: Observability ✅
**SRS Requirement:** Export metrics to Prometheus (/metrics); traces to Jaeger/OTLP collector

**Current Implementation:**
- **Prometheus:** Gateway (9610), conversation-worker (9401), tool-executor (9401)
- **OpenTelemetry:** FastAPI auto-instrumentation, httpx client instrumentation
- **Structured Logging:** JSON logs with session_id, tenant, etc.

**Gap:** Need Grafana dashboards and Jaeger deployment

---

## ❌ MISSING FEATURES (30%)

### FR-1: Orchestrator Engine ❌
**SRS Requirement:** LangGraph-style state machine with checkpointed nodes (Plan, Recall, ToolSelect, Execute, Observe, Reflect, Verify, Commit)

**Current Implementation:**
- **File:** `agent.py` - Simple while loop with tool execution
- **No formal state machine**
- **No checkpointing**
- **No explicit Plan/Reflect/Verify nodes**

**Gap:** Need to implement LangGraph-style orchestrator

**Implementation Effort:** 3 weeks

---

### FR-2: Role-Based Agents ❌
**SRS Requirement:** Three default roles (Researcher, Coder, Operator) with scoped tool access; dynamic role creation via config

**Current Implementation:**
- **File:** `agent.py` - Generic agent with call_subordinate
- **Prompt Profiles:** `agents/{profile}/prompts/` exists but no default roles

**Gap:** Need Researcher/Coder/Operator prompt profiles and tool scoping

**Implementation Effort:** 2 weeks

---

### FR-9: Observability Dashboard ❌
**SRS Requirement:** UI panels for Plan Graph, Agent Hierarchy, Kafka stream, Prometheus metrics, OpenTelemetry traces, Benchmark results

**Current Implementation:**
- **File:** `webui/index.html` - Basic chat interface
- **No Plan Graph visualization**
- **No Agent Hierarchy view**
- **No Kafka stream viewer**
- **No embedded metrics/traces**

**Gap:** Need React/Next.js dashboard with advanced visualizations

**Implementation Effort:** 3 weeks

---

### FR-10: Benchmark Harness ❌
**SRS Requirement:** Runners for WebArena, GAIA, SWE-bench; export CSV/JSON; push to agent.benchmarks.v1

**Current Implementation:**
- **None**

**Gap:** Need benchmark runner framework with dataset loaders and evaluation metrics

**Implementation Effort:** 3 weeks

---

### FR-12: CI/CD Pipeline ⚠️
**SRS Requirement:** Automated tests, linting, Docker build, Helm chart generation, canary deployment to Kubernetes

**Current Implementation:**
- **GitHub Actions:** `.github/workflows/capsule.yml` exists
- **Docker Build:** Makefile targets
- **Tests:** pytest suite in tests/
- **No Helm charts**
- **No canary deployment**

**Gap:** Need comprehensive CI/CD pipeline with Kubernetes deployment

**Implementation Effort:** 2 weeks

---

### NFR-3: Reliability ⚠️
**SRS Requirement:** 99.9% uptime; automatic restart of failed containers via Kubernetes

**Current Implementation:**
- **Docker Compose:** restart: unless-stopped
- **No Kubernetes deployment**
- **No health probes**

**Gap:** Need Kubernetes manifests with liveness/readiness probes

**Implementation Effort:** 1 week

---

### NFR-7: Portability ⚠️
**SRS Requirement:** Deployable on Docker-Compose, Kubernetes, or bare-metal with minimal changes

**Current Implementation:**
- **Docker Compose:** ✅ Fully working
- **Kubernetes:** ❌ No manifests
- **Bare-metal:** ⚠️ Possible but undocumented

**Gap:** Need Helm charts and bare-metal deployment guide

**Implementation Effort:** 2 weeks

---

### NFR-8: Compliance ⚠️
**SRS Requirement:** GDPR-compatible data handling; immutable audit logs retained 90days

**Current Implementation:**
- **Audit Logs:** Append-only events in Postgres
- **No retention policy**
- **No GDPR deletion endpoint**

**Gap:** Need data retention policies and GDPR compliance endpoints

**Implementation Effort:** 1 week

---

## 📊 Gap Summary Table

| Feature ID | Feature Name | Status | Gap Size | Effort |
|------------|--------------|--------|----------|--------|
| FR-1 | Orchestrator Engine | ❌ Missing | Large | 3 weeks |
| FR-2 | Role-Based Agents | ❌ Missing | Medium | 2 weeks |
| FR-3 | Tool Framework | ✅ Complete | None | - |
| FR-4 | Kafka Integration | ✅ Complete | None | - |
| FR-5 | Redis Cache | ✅ Complete | None | - |
| FR-6 | Postgres Persistence | ✅ Complete | Small | 1 week |
| FR-7 | Memory API Client | ✅ Complete | None | - |
| FR-8 | Policy Engine | ✅ Complete | Small | 1 week |
| FR-9 | Observability Dashboard | ❌ Missing | Large | 3 weeks |
| FR-10 | Benchmark Harness | ❌ Missing | Large | 3 weeks |
| FR-11 | Security Hardening | ✅ Complete | Small | 1 week |
| FR-12 | CI/CD Pipeline | ⚠️ Partial | Medium | 2 weeks |
| NFR-1 | Performance | ✅ Complete | None | - |
| NFR-2 | Scalability | ✅ Complete | Small | 1 week |
| NFR-3 | Reliability | ⚠️ Partial | Medium | 1 week |
| NFR-5 | Observability | ✅ Complete | Small | 1 week |
| NFR-7 | Portability | ⚠️ Partial | Medium | 2 weeks |
| NFR-8 | Compliance | ⚠️ Partial | Small | 1 week |

**Total Implementation Effort:** 22 weeks (can be parallelized to 12-16 weeks)

---

## 🎯 Priority Matrix

### P0 - Critical (Must Have)
1. **FR-1: Orchestrator Engine** - Core differentiator
2. **FR-2: Role-Based Agents** - Key feature
3. **NFR-3: Reliability** - Production requirement

### P1 - High (Should Have)
4. **FR-9: Observability Dashboard** - Operator experience
5. **FR-12: CI/CD Pipeline** - Development velocity
6. **NFR-7: Portability** - Deployment flexibility

### P2 - Medium (Nice to Have)
7. **FR-10: Benchmark Harness** - Validation and marketing
8. **NFR-8: Compliance** - Enterprise requirement
9. **FR-6: Alembic Migrations** - Operational maturity

### P3 - Low (Future)
10. **FR-8: Example Policies** - Documentation
11. **FR-11: Vault Integration** - Advanced security
12. **NFR-2: Load Testing** - Performance validation

---

## 🔄 Alignment with Current Roadmap

### Messaging Architecture Roadmap (ROADMAP_CANONICAL.md)

**Wave 0 - Baseline:** ✅ Complete
- Docker Compose stack
- Kafka topics
- Gateway consolidation
- Basic smoke checks

**Wave 1 - Gateway Consolidation:** 🔄 In Progress
- Remove legacy Flask routes
- Unified error handling
- Consistent response schemas

**Wave 2 - Messaging Backbone:** 📋 Planned
- Kafka topic automation
- Consumer retry/DLQ
- Tool result fan-in

**Wave 3 - Credential Flow:** 📋 Planned
- UI credential settings
- Encrypted storage
- Hot-reload

**Wave 4 - E2E Hardening:** 📋 Planned
- Playwright test suite
- OpenTelemetry spans
- Grafana dashboards

**Wave 5 - Performance:** 📋 Planned
- Load testing
- Autoscaling
- Release runbook

### SRS Alignment

**SRS Milestone 1-3** align with **Waves 0-2** (infrastructure)
**SRS Milestone 4-5** align with **Waves 3-4** (security + observability)
**SRS Milestone 6-8** are **NEW** (orchestrator, roles, benchmarks, dashboard)

---

## 🚀 Recommended Approach

### Phase 1: Complete Current Roadmap (Waves 1-5)
**Duration:** 8 weeks  
**Focus:** Stabilize existing architecture before adding new features

### Phase 2: Implement SRS Gaps (Milestones 6-8)
**Duration:** 8 weeks  
**Focus:** Orchestrator, roles, benchmarks, dashboard

### Phase 3: Production Hardening
**Duration:** 4 weeks  
**Focus:** Load testing, compliance, documentation

**Total Timeline:** 20 weeks (5 months)

---

**END OF GAP ANALYSIS**
