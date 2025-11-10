# Selective Authorization Model (Post OPA Middleware Removal)

We removed the legacy global `EnforcePolicy` middleware that caused health failures by calling a non-existent `/v1/policy/evaluate`. Authorization now occurs **selectively** on sensitive endpoints using a lightweight `PolicyClient` and helper `authorize()`.

## Goals
1. Fail-closed for security critical actions (memory writes, tool execution).  
2. No startup coupling—health endpoints remain green even if policy backend is down.  
3. Low latency decision path with small response surface (boolean allow/deny).  
4. Observable: decisions and latency metrics exported via Prometheus (`auth_decisions_total`, `auth_duration_seconds`).

## Components
| Component | File | Responsibility |
|-----------|------|----------------|
| `PolicyClient` | `services/common/policy_client.py` | HTTP evaluation against OPA data path; short TTL cache; fail-closed. |
| `authorize()` | `services/common/authorization.py` | Wraps evaluation, records metrics, raises `403 policy_denied` on failure. |
| `require_policy()` | `services/common/authorization.py` | Decorator for concise inline enforcement (future usage). |
| Metrics | `services/common/authorization.py` | Decision counters + latency histogram. |

## Environment Variables
| Name | Default | Purpose |
|------|---------|---------|
| `POLICY_BASE_URL` | `http://opa:8181` | Base URL of OPA/policy service. |
| `POLICY_DATA_PATH` | `/v1/data/soma/allow` | Data path returning truthy allow decision. |
| `POLICY_CACHE_TTL` | `2` | Seconds to cache identical decisions. |

> Note: `POLICY_FAIL_OPEN` is intentionally ignored—system now fails closed for safety.

## Metrics
| Metric | Labels | Description |
|--------|--------|-------------|
| `auth_decisions_total` | `action`, `result` (allow|deny|error) | Count of selective authorization outcomes. |
| `auth_duration_seconds` | `action` | Latency histogram for decisions. |

## Current Enforcement Points
| Endpoint | Action | Resource | Context keys |
|----------|--------|----------|--------------|
| `POST /v1/learning/reward` | `learning.reward` | `learning` | `session_id`, `signal` |
| `POST /v1/tool/request` | `tool.execute` | `tool` | `tool_name`, `session_id` |
| `POST /v1/memory/batch` | `memory.write` | `memory` | `batch_size` |
| `GET /v1/admin/memory` | `ops.memory.list` | `OperationsAdministration` | `tenant`, `persona_id`, `role`, `session_id` |
| `GET /v1/admin/memory/{event_id}` | `ops.memory.get` | `OperationsAdministration` | `event_id` |
| `GET /v1/memory/export` | `ops.memory.export.stream` | `OperationsAdministration` | filters (tenant/persona_id/role/session_id) |
| `POST /v1/memory/export/jobs` | `ops.memory.export.job.create` | `OperationsAdministration` | payload fields |
| `GET /v1/memory/export/jobs/{job_id}` | `ops.memory.export.job.status` | `OperationsAdministration` | `job_id` |
| `GET /v1/memory/export/jobs/{job_id}/download` | `ops.memory.export.job.download` | `OperationsAdministration` | `job_id` |
| `GET /v1/admin/memory/metrics` | `ops.memory.metrics` | `OperationsAdministration` | `tenant`, `namespace` |
| `POST /v1/admin/migrate/export` | `ops.migrate.export` | `OperationsAdministration` | payload fields |
| `POST /v1/admin/migrate/import` | `ops.migrate.import` | `OperationsAdministration` | `replace` |
| `GET /v1/admin/dlq/{topic}` | `ops.dlq.list` | `OperationsAdministration` | `topic` |
| `DELETE /v1/admin/dlq/{topic}` | `ops.dlq.purge` | `OperationsAdministration` | `topic` |
| `POST /v1/admin/dlq/{topic}/{id}/reprocess` | `ops.dlq.reprocess` | `OperationsAdministration` | `topic`, `id` |
| `GET /v1/admin/audit/export` | `ops.audit.export` | `OperationsAdministration` | filters (request_id/session_id/tenant/action) |
| `GET /v1/admin/audit/decisions` | `ops.audit.decisions.list` | `OperationsAdministration` | filters (tenant/session_id/request_id) |
| `GET /constitution/version` | `ops.constitution.version` | `OperationsAdministration` | – |
| `POST /constitution/validate` | `ops.constitution.validate` | `OperationsAdministration` | – |
| `POST /constitution/load` | `ops.constitution.load` | `OperationsAdministration` | – |

Note: We collectively refer to the privileged operator/admin surface as "OperationsAdministration". These routes now perform selective policy checks in addition to existing scope checks.

## Failure Modes
| Scenario | Result | HTTP Code | Notes |
|----------|--------|-----------|-------|
| Policy allow | Request continues | 200/normal | Decision cached (TTL). |
| Policy deny | Blocked | 403 | Audit handled by upstream layers (planned). |
| Policy error/timeout | Blocked (fail-closed) | 403 | Recorded as `result=error` metric then denial. |

## Rationale for Selective vs Global Middleware
Global middleware created a hard dependency on policy availability for **every** request including health probes, causing cascading failures and preventing stack bring-up. Selective enforcement isolates policy risk to sensitive domains only, improving reliability while preserving security posture.

## Future Enhancements
1. **Decorator Adoption:** Replace direct calls with `@require_policy(action, resource)` for cleaner routes.  
2. **Context Enrichment:** Include `tenant`, `persona_id`, and redacted request body fields for finer-grained policies.  
3. **Audit Logging:** Emit structured audit records on allow/deny including trace and request IDs.  
4. **OpenFGA Integration:** Combine relationship checks (ownership, role) prior to policy evaluation.  
5. **Decision Bundling:** Batch multiple tool calls decisions per request to reduce latency under high concurrency.  

## Testing
Unit tests: `tests/unit/test_selective_policy.py` cover allow, deny, error (fail-closed) paths by monkeypatching `PolicyClient.evaluate`.  
Integration tests (planned): exercise tool request and memory batch endpoints with mocked OPA service responses.

## Quick Reference (Usage)
```python
from services.common.authorization import authorize

@app.post("/v1/tool/request")
async def request_tool_execution(payload: ToolRequestPayload, request: Request):
    await authorize(request, action="tool.execute", resource="tool", context={"tool_name": payload.tool_name})
    # proceed
```

## Rollout Status
Selective auth deployed; global middleware removed. Health endpoints stable (200). Metrics available on `/metrics`.

---
Maintainers: Security / Platform team. Update this document as new policy scopes are enforced.
