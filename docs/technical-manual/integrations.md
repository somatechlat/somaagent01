---
title: Integrations & Connectivity
slug: technical-integrations
version: 1.0.0
last-reviewed: 2025-10-15
audience: platform-engineers, partner-teams
owner: connectivity
reviewers:
  - platform-architecture
  - security
prerequisites:
  - Access to integration credentials
  - Reviewed [Security Baseline](./security.md)
verification:
  - Integration smoke tests succeed in CI
  - External endpoints documented in change log
---

# Integrations & Connectivity

This guide documents the upstream and downstream systems that SomaAgent01 connects to, including APIs, protocols, authentication mechanisms, and validation routines.

## 1. Managed Soma SLM API

- **Endpoint:** `https://slm.somaagent01.dev/v1`
- **Auth:** Bearer tokens stored as `SLM_API_KEY`.
- **Usage:** chat, utility, embedding models.
- **Verification:** Run `scripts/probes/check_slm.py` to validate latency and model availability.

## 2. Open Policy Agent (OPA)

- **Endpoint:** `http://opa.soma.svc.cluster.local:8181`.
- **Policy bundles:** `policy/bundles/somaagent01.tar.gz`.
- **Decision path:** `/v1/data/http/authz/allow`.
- **Deployment:** Sidecar or standalone service depending on environment.
- **Verification:** CI runs `scripts/probes/check_opa.py --policy policy/bundles/somaagent01`. Deny-by-default enforced.

## 3. Auth Service

- **Endpoint:** `http://auth.soma.svc.cluster.local:8080`.
- **Protocol:** OAuth 2.0 compatible; JWT tokens minted for UI and gateway.
- **Key management:** Vault-backed signing keys rotated quarterly.
- **Verification:** Integration tests ensure token validation in gateway middleware.

## 4. Data Plane Integrations

| System | Protocol | Purpose | Notes |
| ------ | -------- | ------- | ----- |
| Kafka (`kafka.soma.svc.cluster.local:9092`) | TCP | Event streaming for tasks, config updates | Topics defined in `schemas/kafka/` |
| Redis (`redis.soma.svc.cluster.local:6379`) | TCP | Caching, rate limiting, session store | TLS optional; configure in `settings.redis_tls_enabled` |
| Qdrant (`qdrant.soma.svc.cluster.local:6333`) | HTTP/gRPC | Vector store for memory retrieval | Optional profile in compose |
| Postgres (`postgres.soma.svc.cluster.local:5432`) | TCP | Persistence for audit logs and registry | Migrations in `infra/db/migrations` |

## 5. External Tool Integrations

- **Cloudflare Tunnel:** Automates secure external access. Configure via `.env` (`CLOUDFLARE_TOKEN`, `CLOUDFLARE_TUNNEL_ID`).
- **SearXNG:** Search engine for `search_engine` tool; configure endpoint in `common/config/settings.py`.
- **Document Query Tool:** Connects to vector index; ensure `DOCUMENT_QUERY_URL` is reachable.

## 6. Diagram of Integration Points

```mermaid
digraph Integrations {
  rankdir=LR
  UI -> Gateway [label="HTTP"]
  Gateway -> SLM [label="HTTPS", color="green"]
  Gateway -> Auth [label="OAuth"]
  Gateway -> OPA [label="Policy"]
  ConversationWorker -> Kafka [label="Produce/Consume"]
  ConversationWorker -> Redis [label="Cache"]
  ConversationWorker -> Qdrant [label="Vector search"]
  ToolExecutor -> DockerDaemon [label="gRPC"]
  ToolExecutor -> ExternalAPIs [label="HTTPS"]
}
```

## 7. Validation & Monitoring

- Integration health endpoints checked by CI and runtime cron jobs.
- Alerts configured for latency, failure rate, and auth errors (see `infra/observability/alerts.yml`).
- Logs tagged with `integration` key for searchability.

## 8. Change Management

- Update [`docs/changelog.md`](../changelog.md) for new endpoints or credential rotations.
- Security review required for any new external dependency.
- Add regression tests under `tests/integration/` when adding or modifying integrations.
