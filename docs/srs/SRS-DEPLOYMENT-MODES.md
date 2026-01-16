# SRS: Deployment Modes and AWS Fargate Baseline

**Document ID:** SA01-SRS-DEPLOYMENT-MODES-2025-12
**Purpose:** Define deployment targets, resource baselines, and infra expectations for somaAgent01, somabrain, and somafractalmemory.
**Status:** CANONICAL REFERENCE

---

## 1. Scope

This SRS applies to the following repositories:

- **somaAgent01** (gateway + web UI + workers)
- **somabrain** (cognitive/memory runtime)
- **somafractalmemory** (memory store + search)

The goal is to support multiple deployment targets with a single configuration flag while keeping production‑aligned behavior for testing.

---

## 2. Deployment Targets (Modes)

The platform must support the following deployment targets via **`SA01_DEPLOYMENT_TARGET`**:

- **LOCAL**: Docker Compose on a single host.
- **FARGATE**: ECS Fargate (primary target for production‑aligned testing).
- **EKS**: Kubernetes on AWS.
- **ECS_EC2**: ECS on EC2 capacity.
- **EC2**: Direct VM deployment.
- **APP_RUNNER**: AWS App Runner (HTTP‑only services; no WebSocket for Channels).
- **UNIFIED_SAAS**: Single-Process Integration (Agent+Brain+SFM). Used for high-performance SaaS.

`SA01_DEPLOYMENT_MODE` continues to describe environment posture (DEV/STAGING/PROD/LOCAL/TEST).
`SOMA_SAAS_MODE` controls the internal integration strategy (HTTP vs DIRECT).

---

## 3. Resource Baselines

### 3.1 Local (Docker) Baseline

- Total host memory budget: **15 GB** (production‑aligned testing on constrained hardware).
- All stateful services run locally (Postgres, Redis, Kafka, etc.).

### 3.2 Unified SaaS (Direct) Baseline
- **Architecture**: `SOMA_SAAS_MODE=direct`
- **Memory**: Direct Python Interface (No HTTP overhead for memory ops).
- **Latency**: < 0.1ms for memory store/recall.

### 3.2 AWS Baseline (Fargate / ECS / EKS / EC2)

Minimum per‑service resource requirements:

- **Memory:** 16 GB
- **Disk:** 30 GB

These are minimums for the **gateway**, **somabrain**, and **somafractalmemory** services. Higher tiers may require more memory and storage.

---

## 4. Required Managed Services (AWS)

The following services must be provided by AWS managed infrastructure or equivalent self‑managed clusters:

- **PostgreSQL** (RDS or equivalent)
- **Redis** (ElastiCache or equivalent)
- **Kafka** (MSK or equivalent)
- **Object Storage** (S3 or equivalent)
- **Secrets** (Secrets Manager or SSM)

If authentication is enabled (`SA01_AUTH_REQUIRED=true`), a **Keycloak/JWT provider** must be available.

---

## 5. Networking & Traffic

- **Public entrypoint** for the gateway must support **HTTP + WebSocket**.
- WebSocket traffic must terminate on a load balancer that preserves upgrade headers.
- Internal services must live on private subnets with no public ingress.

---

## 6. Configuration Requirements

Required canonical environment variables (minimum set):

- `SA01_DEPLOYMENT_MODE`
- `SA01_DEPLOYMENT_TARGET`
- `SA01_AUTH_REQUIRED`
- `SA01_AUTH_JWT_SECRET`
- `SA01_AUTH_INTERNAL_TOKEN`
- `SA01_CRYPTO_FERNET_KEY`
- `SA01_POLICY_URL`
- `SA01_POLICY_DECISION_PATH`
- `SA01_DB_DSN`
- `SA01_REDIS_URL`
- `SA01_KAFKA_BOOTSTRAP_SERVERS`

All secrets must be injected at runtime (never committed to the repo).

---

## 7. Observability

Each service must export:

- **Health**: `/health`, `/healthz`, `/readyz` (as available per service)
- **Metrics**: `/metrics` (Prometheus format)

Centralized logging must be enabled per deployment target.

---

## 8. Constraints & Non‑Goals

- No direct reads of local credential files by application code.
- No reliance on mocked services in production‑aligned deployments.
- No single‑container monolith deployment for production; each service deploys separately.

---

## 9. Compliance Notes

This SRS is based on repository‑local requirements and user‑provided constraints. AWS‑specific limits and exact infrastructure settings must be verified against official AWS documentation before provisioning.
