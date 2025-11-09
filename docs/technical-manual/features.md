# Feature Capability Registry (Draft Schema)

Status: Draft (Sprint 0)  
Owner: Architecture / Platform Team  
Last Updated: 2025-11-09

## Purpose
Centralize all feature toggles and rollout controls into a typed, observable registry. Replace scattered `os.getenv` checks with a single source of truth supporting profiles (minimal, standard, enhanced, max) and health-aware degrade strategies.

## Objectives
- Best mode enabled by default (profile: `enhanced`).
- Health-aware auto-degrade (error/latency thresholds) instead of manual flag flapping.
- Auditable transitions (enabled → degraded → disabled) with reason codes.
- Metrics & diagnostics endpoint for real-time visibility.
- Backward compatibility: environment variables still honored during migration phase; deprecated after Sprint 1 exit gate.

## Descriptor Schema
Each capability is represented by a `FeatureDescriptor` object.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | `str` | yes | Unique machine-readable identifier (snake_case). |
| `description` | `str` | yes | Concise human description (<=120 chars). |
| `default_enabled` | `bool` | yes | Base on/off before profile & dependency evaluation. |
| `profiles` | `dict[str,bool]` | yes | Override enable state per profile (`minimal`, `standard`, `enhanced`, `max`). |
| `dependencies` | `list[str]` | no | Other feature keys that must be enabled and healthy. |
| `degrade_strategy` | `str` | yes | One of: `auto`, `manual`, `none`. `auto` allows health-based transition. |
| `cost_impact` | `str` | yes | `low` | `medium` | `high` for resource/cost planning. |
| `metrics_key` | `str` | yes | Key suffix for Prometheus labels (e.g. `embeddings_ingest`). |
| `tags` | `list[str]` | no | Classification: `observability`, `security`, `performance`, `beta`. |
| `enabled_env_var` | `str` | no | Legacy env var that can override during migration. |
| `stability` | `str` | yes | `stable`, `beta`, `experimental`. |
| `degrade_thresholds` | `dict[str,float]` | no | Health thresholds (e.g. `{error_rate:0.05, p95_latency_ms:800}`) for auto degrade. |
| `rollback_action` | `str` | no | Summary of safe fallback when disabled/degraded. |
| `audit_critical` | `bool` | yes | If true, all state changes require explicit audit log entry. |

### State Model
```
          +-----------+            health breach / dependency fail
    ON -->| DEGRADING |----------------------------------+
    ^     +-----------+                                   |
    |            | (grace period / evaluation)            v
    |            v                                   +---------+
manual disable   +-----------+   terminal or manual  | DISABLED|
re-enable -----> | DEGRADED  |---------------------->+---------+
                  +-----------+          |              ^
                       | recovery       |              |
                       +----------------+--------------+
                                   health recovery / manual enable
```
- `ON` → `DEGRADING`: system detects threshold breach; starts observation window.
- `DEGRADING` → `DEGRADED`: confirm sustained breach; apply restricted mode/fallback.
- `DEGRADED` → `ON`: health metrics back within thresholds for N consecutive windows.
- `DEGRADED`/`ON` → `DISABLED`: manual action or hard failure (e.g., fatal config). Only manual path returns to `ON`.

### Metrics
Prometheus metrics (all labeled by `feature`):
- `feature_enabled{feature}` gauge: 1 when ON, 0 otherwise.
- `feature_degraded{feature}` gauge: 1 when DEGRADED, 0 otherwise.
- `feature_state_transitions_total{feature,state}` counter.
- `feature_health_error_rate{feature}` gauge (optional for auto features).
- `feature_health_latency_p95_ms{feature}` gauge.

### Diagnostics Endpoint
`GET /v1/features` returns:
```json
{
  "profile": "enhanced",
  "features": [
    {
      "key": "embeddings_ingest",
      "state": "on",
      "degraded": false,
      "stability": "beta",
      "dependencies": [],
      "error_rate": 0.012,
      "p95_latency_ms": 420,
      "reason": null
    },
    {
      "key": "semantic_recall",
      "state": "disabled",
      "degraded": false,
      "stability": "experimental",
      "dependencies": ["embeddings_ingest"],
      "reason": "profile:max only"
    }
  ]
}
```

### Profiles
| Profile | Intent | Example Enabled | Example Disabled |
|---------|--------|-----------------|------------------|
| minimal | Critical core | `conversation_flow`, `memory_write` | `embeddings_ingest`, `semantic_recall` |
| standard | Production base | + `tool_executor`, `scheduler` | `semantic_recall` (beta) |
| enhanced | Full best mode | + `embeddings_ingest`, `sandbox_usage_metrics` | `semantic_recall` (experimental) |
| max | Advanced / experimental | All including `semantic_recall` | (none, unless forced) |

### Degrade Strategies
| Strategy | Behavior |
|----------|----------|
| auto | Transition when thresholds breached; apply fallback (e.g. use cached embeddings only). |
| manual | Changes only via authorized admin action. |
| none | No degrade path; either ON or DISABLED (e.g. security-critical feature). |

### Example Descriptors
```python
FeatureDescriptor(
    key="embeddings_ingest",
    description="Generate vector embeddings for messages and tool outputs",
    default_enabled=True,
    profiles={"minimal": False, "standard": True, "enhanced": True, "max": True},
    dependencies=[],
    degrade_strategy="auto",
    cost_impact="medium",
    metrics_key="embeddings_ingest",
    tags=["performance", "memory"],
    enabled_env_var="ENABLE_EMBED_ON_INGEST",
    stability="beta",
    degrade_thresholds={"error_rate": 0.05, "p95_latency_ms": 900},
    rollback_action="Skip embedding generation; proceed without vector metadata",
    audit_critical=True,
)

FeatureDescriptor(
    key="semantic_recall",
    description="Vector similarity recall for contextual memory injection",
    default_enabled=False,
    profiles={"minimal": False, "standard": False, "enhanced": False, "max": True},
    dependencies=["embeddings_ingest"],
    degrade_strategy="auto",
    cost_impact="high",
    metrics_key="semantic_recall",
    tags=["beta", "memory"],
    stability="experimental",
    degrade_thresholds={"error_rate": 0.07, "p95_latency_ms": 1200},
    rollback_action="Fall back to recency + session-scoped heuristics",
    audit_critical=True,
)
```

### Audit & Logging
On state transition emit structured log:
```
{"event":"feature_state_change","feature":"embeddings_ingest","from":"on","to":"degraded","reason":"error_rate>0.05","timestamp":"...","profile":"enhanced"}
```
Audit entries include masked env overrides (not actual secret values).

### Migration Plan
1. Sprint 0: Document schema (this file), add lint rule plan.
2. Sprint 1: Implement registry; dual-path env overrides; expose metrics & diagnostics.
3. Sprint 2: Remove direct env flag reads; enforce registry usage; finalize lint rule.
4. Sprint 3+: Add auto-degrade watchers; integrate alerting & dashboards.

### Lint / Enforcement Strategy
- Add static check forbidding `os.getenv("ENABLE_"` / `os.getenv("SA01_ENABLE_"` outside registry after Sprint 2.
- Provide a suppress comment pattern for transitional exceptions (expires after date).

### Open Questions
- Persistence of last known states? (Initial approach: in-memory; future: lightweight store for restart continuity.)
- Multi-tenant overrides per feature? (Phase after unified config M10.)
- Cross-feature coordinated degrade (e.g. memory pressure) – schedule evaluation.

### Next Steps
- Validate descriptor coverage for all current flags.
- Finalize list of initial features (embeddings_ingest, semantic_recall, scheduler_celery, tool_events, content_masking, token_metrics, error_classifier, reasoning_stream, sandbox_usage_metrics).
- Implement registry module (`services/common/features.py`).

---
END OF DRAFT
