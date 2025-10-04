# SomaAgent 01 – Delivery Roadmap

This roadmap tracks the rapid-development sprints required to launch SomaAgent 01 into production. Each sprint is two weeks unless noted. Columns: **Scope**, **Key Tasks**, **Deliverables**, **Success Metrics**.

## Sprint 0 – Foundation Sync *(Week 0)*
- Review existing Agent Zero + SomaBrain codebase
- Stand up shared dev cluster (Kubernetes + Kafka + Redis + Postgres)
- Baseline benchmarks & smoke tests
- ✅ Deliverables: environment ready, dashboards baseline, risks logged

## Sprint 1 – Event Backbone & Persistence *(Weeks 1-2)*
- Implement Kafka producers/consumers for chat, memory, routing, audit
- Add Postgres transactions + outbox pattern
- Create reconciliation worker skeleton (logs discrepancies)
- Introduce global `SOMAGENT_MODE` flag (developer/training/test/production) with config propagation and event broadcasting
- Enforce JSON schema validation for every event type so downstream consumers stay in sync
- Deliverables: reliable event stream, admin report of queue stats
- Metrics: zero lost messages in chaos test, offset lag < 1s under load

## Sprint 2 – Dynamic Router & SLM Tier *(Weeks 3-4)*
- Integrate Groq + HuggingFace + premium providers via Litellm
- Deploy SLM stack (Phi-3 Mini, Llama 3.1 8B, Mistral 7B)
- Build routing policy engine (bandit scaffold) + Redis cache
- Initial admin API for routing policies + budgets
- Metrics: routing audit log, <200ms decision latency, SLM fallback tests pass

## Sprint 3 – Canvas & Session Intelligence *(Weeks 5-6)*
- Canvas microservice (CRUD + WebSocket updates)
- Agent tools for canvas manipulation & streaming code outputs
- Persist canvas layout in Postgres; restore on reconnect
- Metrics: simultaneous canvas sessions >1k with p95 <150ms update

## Sprint 4 – Multi-Tenancy & Governance *(Weeks 7-8)*
- Tenant-aware routing policies, spend controls, memory namespaces
- OPA policies for tool usage & delegation
- JWT scopes + SPIFFE cert wiring
- Privileged-mode framework: scoped elevation for host-level commands with full audit trail
- Enterprise switch scaffolding: ensure `ENTERPRISE_MODE` toggles OSS-only providers, expanded auditing, training disabled by default
- Metrics: policy enforcement coverage, negative tests blocked, audit logs enriched

## Sprint 5 – Delegation Gateway *(Weeks 9-10)*
- Kafka topic `somastack.delegation` + gateway service
- Task definitions, callback tracking, retries
- Integration tests with SomaAgent Server stub
- Metrics: <1% failed delegation, trace linking across agents

## Sprint 6 – Observability & SLO Enforcement *(Weeks 11-12)*
- Unified dashboards (Prometheus/Grafana), latency/error alerts
- Tracing instrumentation (OpenTelemetry)
- Chaos tests: Kafka outage, Redis latency, SomaBrain failure
- Autonomic mode detection: monitor SomaBrain/LLM/Network health, publish state to UI, ensure queue replay on recovery
- Enterprise observability: SOC2 dashboards, extended retention, SIEM exports tied to the enterprise toggle
- Metrics: alert noise <5%, auto-recovery success, chaos reports archived

## Sprint 7 – Production Hardening *(Weeks 13-14)*
- Load tests to target RPS +20% headroom
- Security review (WAF rules, secret rotation, pen test triage)
- Documentation: runbooks, admin manual, compliance checklists
- Metrics: all SLOs met, incident drills passed

## Continuous Backlog
- FRGO transport learning integration
- Differential privacy pipeline
- Delegation analytics visualization
- Automated LLM regression harness
- Multi-region active-active rollout
- SomaBrain enrichment tasks (canvas summaries, tool output digests, audio analytics) so every interaction feeds long-term memory automatically

## Tracking & Updates
- Sprint board in project tool (Jira/Linear) labeled `SOMAAGENT01`
- Weekly architecture sync + decision log updates
- Documents to update each sprint: architecture baseline, operational runbooks, compliance artifacts

---
Use this roadmap as the authoritative tracker. Adjust milestones as scope evolves, but keep success metrics quantifiable.
