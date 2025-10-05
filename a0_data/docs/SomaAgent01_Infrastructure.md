⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Infrastructure Profiles

SomaAgent 01 operates on three canonical infrastructure profiles. Each profile relies exclusively on open-source tooling and allows us to move from laptop experiments to enterprise production without changing code.

## 1. LOCAL (Workstation)
- **Orchestration**: Docker Compose (`infra/docker-compose.somaagent01.yaml`).
- **Core Services**: Kafka (Bitnami KRaft), Redis, Postgres, Qdrant, ClickHouse, Whisper (CPU), Vault dev mode, OPA (permissive), OpenFGA, Delegation gateway/worker. The SLM tier is consumed via the managed Soma SLM API (`SLM_BASE_URL`) so no heavyweight model container is required locally.
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
  - Soma SLM connector (points to the managed SLM API; no in-cluster LLM deployment).
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
  - Managed Soma SLM API endpoints with autoscaling; no tenant-owned LLM GPUs required.
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
