# Observability Alert Rules (Prototype)

This document lists initial Prometheus alerting rules aligned with Phase 0–2 roadmap goals.
Rules live in `infra/observability/alerts/*.rules.yml` and are intended for inclusion by Prometheus via `rule_files`.

## Implemented Rule Groups

### feature-state
| Alert | Purpose | Expression (summary) | Action |
|-------|---------|----------------------|--------|
| FeatureDisabledUnexpected | Detect unexpected disabled features in best-mode profile | `sum by(feature) (feature_state_info{state="disabled"}) > 0` | Inspect `/v1/features` diagnostics; check recent config updates/audit logs |
| SemanticRecallErrors | Recall endpoint errors | `rate(semantic_recall_requests_total{result="error"}[5m]) > 0` | Verify embeddings provider and index integrity |
| EmbeddingProviderErrors | Embedding provider failures | `rate(embeddings_requests_total{result="error"}[5m]) > 0` | Check API key validity, network, provider status page |
| OutboxBacklogHigh | Message processing backlog | `gateway_outbox_backlog > 1000` | Investigate consumers, database latency, deadlocks |

## Future Rules (Planned)
- ReplicationLagCritical: WAL or replica lag threshold breach.
- FeatureDegraded: Introduce `degraded` state metrics and alert when sustained.
- TokenUsageAnomaly: Sudden surge in token usage vs baseline.
- RateLimitBlocksSpike: High proportion of blocked requests indicating abuse.

## Deployment
Add to Prometheus configuration:
```yaml
rule_files:
  - infra/observability/alerts/*.rules.yml
```
Reload Prometheus or use the HTTP reload endpoint after adding rules.

## Operations Runbook (Skeleton)
| Symptom | Quick Checks | Deep Dive |
|---------|--------------|-----------|
| EmbeddingProviderErrors | `/v1/features`, provider status page | Increase timeout, inspect network egress metrics |
| SemanticRecallErrors | Confirm feature enabled | Validate index memory usage & potential vector dimension mismatch |
| OutboxBacklogHigh | Check DB health, consumer logs | Profile slow queries, examine locking & retry loops |

---
Maintained by the observability owners. Update as new metrics and states are added.
