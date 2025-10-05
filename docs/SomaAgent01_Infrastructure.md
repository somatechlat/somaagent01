⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Infrastructure Profiles

SomaAgent 01 operates on three canonical infrastructure profiles. Each profile relies exclusively on open-source tooling and allows us to move from laptop experiments to enterprise production without changing code.

> **Update (2025-10-05):** SLM and micro-LLM tiers remain feature-flagged off in all environments. The infrastructure below still advertises the integration points so we can enable them later, but runtime traffic currently flows only through the primary LLM stack.

## 1. LOCAL (Workstation)
- **Orchestration**: Docker Compose (`infra/docker-compose.somaagent01.yaml`).
- **Core Services**: Kafka (Bitnami KRaft), Redis, Postgres, Qdrant, ClickHouse, Whisper (CPU), Vault dev mode, OPA (permissive), OpenFGA, Delegation gateway/worker. The SLM tier is consumed via the managed Soma SLM API (`SLM_BASE_URL`) so no heavyweight model container is required locally.
  - **SLM status**: Connector remains stubbed; by default the worker routes conversations to the baseline LLM profile to keep workstation dependencies light.
- **Observability**: Prometheus (bundled in compose).
- **Networking**: All services bound to localhost; no ingress controller required.
- **Usage**: Solo development, quick smoke tests, replaying sessions.

## 2. DEVELOPMENT (Shared Kubernetes Cluster)
- **Cluster**: Kubernetes (≥1.28) with GPU node pool. Namespaces managed per environment (`dev`, `qa`).
- **GitOps**: Argo CD syncs Helm/Kustomize charts from `infra/k8s/` (to be populated). Terraform manages cluster resources and IAM.
- **Core Services**:
  - Kafka/KRaft via Strimzi operator (single AZ, persistent volumes).
  - Redis cluster (Redis Operator) with TLS/ACLs.
  - Postgres HA (Patroni or CrunchyData) with Timescale extension.
  - Qdrant & ClickHouse stateful sets (persistent volumes + backups).
  - Soma SLM connector placeholder (points to managed API when enabled). Default deployments keep the flag off and rely exclusively on the promoted LLM profiles.
  - Whisper ASR (GPU deployments with autoscaling).
  - Vault (HA) with Kubernetes auth; secrets injected via Vault Agent sidecars.
  - OPA + OpenFGA (policy enforcement namespaces).
  - Prometheus Operator with SomaSuite dashboards.
- **Networking**: Kong/Envoy ingress with mTLS, cert-manager for TLS.
- **Usage**: Team development, integration testing, nightly benchmarks.

## 3. ENTERPRISE / PRODUCTION (Multi-Region Kubernetes)
- **Cluster Topology**: Multi-region Kubernetes (e.g., GKE/AKS/EKS) with dedicated Kafka, Redis, Postgres, Qdrant, ClickHouse clusters per region. Cross-region replication enabled (Kafka MirrorMaker 2, Postgres logical replication, ClickHouse Distributed tables).
- **GitOps & CI/CD**: Argo CD + Argo Rollouts for canary deployments. Dagger-based pipelines sign images with Cosign and push Terraform/Helm updates.
- **Core Services**:
  - Kafka/KRaft clusters (3–5 brokers/region, tiered storage, TLS/SASL).
  - Redis Enterprise or Redis Operator cluster with shard replication and Redis Streams for backpressure.
  - Postgres HA (Citus or Patroni) with synchronous replicas, PITR backups.
  - Qdrant federated clusters (encryption at rest, tenant isolation).
  - ClickHouse Cloud/Cluster with replicated shards for analytics.
  - Managed Soma SLM API endpoints remain provisioned but disabled; production routing keeps traffic on the current LLM estate until mobile/edge constraints are resolved.
  - Whisper GPU pools with autoscaling and queue length metrics.
  - Vault Enterprise (HSM backed) for secrets + PKI; integrations with Service Mesh (Istio/Linkerd).
  - OPA Gatekeeper for admission control; OpenFGA for relationship authorization.
  - Prometheus + Thanos (object storage for long-term metrics).
- **Networking**: Global load balancing (CloudFront/Cloud Armor/Cloud DNS). Kong/Envoy edge with WAF, mTLS, JWT validation. Zero-trust network policies via Cilium/Calico.
- **Usage**: Tenant-facing production with SLAs, compliance evidence, automated failover and disaster recovery.

## GitOps Repository Layout (proposed)
```
infra/
  └── k8s/
        ├── base/               # Common Helm chart values
        ├── overlays/
        │    ├── local/         # Kind or k3d overlays (optional)
        │    ├── dev/
        │    ├── training/
        │    └── prod/
        └── apps/               # HelmRelease/Argo CD Application manifests
```

## Observability Expectations
- Prometheus scrape configs aligned per profile; Thanos enabled in enterprise.
- Alerting rules vary by mode (development warnings vs production paging).
- Tracing pipelines remain pluggable (gateway → worker → tool executor → SomaBrain).
- Logs structured with tenant/persona/mode for searchability.

## Security
- Vault is the single source of secrets beyond LOCAL mode.
- OPA/OpenFGA enforce policy in all environments; strict fail-closed in production.
- Kyverno/Falco monitor container behaviour; CIS benchmarks applied to clusters.

Document updates in `docs/SomaKamachiq_Redesign.md` and `docs/SomaAgent01_Modes.md` reference this file.

## 2. Escalation LLM Tier (Shared Service)

### 2.1 Role inside the language ladder
- **Current posture**: `ESCALATION_ENABLED=false` across all profiles, so the router never invokes the SLM tier in runtime traffic. The configuration and observability hooks stay in place to shorten lead time when we revisit the rollout.
- The escalation tier only activates when the pre-SLM classifier marks a task as high complexity, high risk, or high business value, or when the primary SLM returns an explicit `defer`/`insufficient_confidence` signal.
- Requests enter through the same router telemetry envelope used elsewhere in SomaSuite, preserving `tenant`, `persona`, `mode`, and `budget_trace_id` so downstream policies remain enforceable.
- The conversation worker enriches the prompt with the micro-model outputs (summaries, retrieved facts, budget hints) and forwards the bundle to the selected escalation LLM endpoint.
- Responses are scored and optionally post-processed (tool plan validation, hallucination guard). Any outputs failing policy checks are automatically re-queued or downgraded back to tool-based resolution.

### 2.2 Deployment and capacity strategy
- **Short term (now):** consume open-source model inference from trusted providers (e.g., Hugging Face Inference Endpoints, Replicate, Fireworks) while enforcing egress via our delegated gateway. We pin model revisions and attach per-tenant service accounts so policies and rate limits remain centralized.
- **Near term (≤2 quarters):** operate self-hosted inference pools in the shared Kubernetes GPU node group using vLLM or TGI. Pools reside in the `soma-escalation-llm` namespace and scale via KEDA on Kafka queue depth. No fine-tuning is required initially, but hooks are left for LoRA adapters managed by Vault.
- **Future (project-based):** when Soma launches proprietary models, they deploy as additional inference services behind the same router contract, allowing gradual cutover without changing client code.
- All endpoints emit standard OpenTelemetry traces so the platform can compare throughput, latency, and GPU utilisation in real time.
- Runtime switches: `ESCALATION_ENABLED` gates the tier globally, while `ESCALATION_FALLBACK_ENABLED` activates the length-based safety net for unusually long statements.

### 2.3 Telemetry, governance, and cost accounting
- Every escalation call publishes a `llm.escalation.invocation` event to Kafka (`suite.telemetry.llm.escalation.raw`). The payload records tokens in/out, wall clock latency, GPU milliseconds, cache hits, temperature, safety filters applied, and the routing decision tree.
- The Telemetry Store batches these events into ClickHouse tables partitioned by `tenant` and `model_id`. SomaAgentHub consumes the same stream to update per-tenant scorecards, budget burn-down, and win/loss analytics.
- An hourly aggregator derives cost estimates using the provider's published rate card (or internal GPU cost model) and persists them to the budget ledger so OPA can hard-stop when a policy threshold is hit.
- Field-level schema, redaction rules, and retention windows remain aligned with `docs/SomaAgent01_Telemetry.md`, ensuring SomaAgentHub interprets escalation events consistently with the rest of the suite.
- Safety and compliance data (prompt hashes, refusal reasons, policy versions) are attached as OPA input documents, allowing retrospective audits and reproducible adjudication.
- Prometheus exposes SLI dashboards (P50/P95 latency, success %, cost per 1K tokens) while traces flow into Tempo/Jaeger for deep debugging.

### 2.4 OSS escalation LLM catalog
| Model (OSS) | License & Size | Strengths | Suggested Use Cases | Operational Notes |
| --- | --- | --- | --- | --- |
| Mixtral 8x7B Instruct | Apache 2.0, MoE 8×7B | Fast MoE routing, strong general reasoning, bilingual (EN/FR) | Default fallback for complex multi-step synthesis, structured answer drafting | Runs efficiently on 2×A100 40GB via vLLM; enable KV cache + speculative decoding for latency <2s on 4K tokens |
| Qwen2-72B Instruct | Apache 2.0, 72B dense | High-quality multilingual reasoning, code understanding | Multilingual escalations, legal/policy drafting where nuance matters | Requires 4×A100 80GB or 8×A6000; plan nightly evaluation to monitor drift |
| Yi-34B Chat | Apache 2.0, 34B dense | Balanced performance vs cost, excels at long-form synthesis | Financial summaries, persona coaching with long context windows | Operable on 2×A100 80GB; integrate with context window >32K using rope scaling |
| DeepSeek-Coder-V2 Instruct | MIT, 16×7B MoE | Code generation, tool plan repair, DSL authoring | Escalations that involve code patches, automation scripts, infrastructure IaC | Ensure router only routes developer personas; enforce repo access policy via OPA |
| Phi-3-Medium Instruct | MIT, 14B dense | Low-cost, good for concise reasoning, safety-tuned | Budget-constrained tenants needing faster turnaround, sanity-check passes | Serves on single L40S; ideal for canarying new escalation logic |

- Model selection is data-driven: the router compares last-24h success rate, cost per 1K tokens, and latency against persona-specific SLAs before committing.
- Periodic batch evaluations (nightly on development, weekly in production) run benchmarks and publish scorecards to SomaAgentHub so operators can promote/demote models quickly.
- All models share the same prompt scaffolding and safety adapters, making swaps transparent to upstream services.

> 📌 **Key takeaway:** the escalation tier behaves like another shared service in the Soma suite—policy-aware, telemetry-rich, and interchangeable—ensuring we can adopt the best open models today while paving the way for Soma-built LLMs tomorrow.
