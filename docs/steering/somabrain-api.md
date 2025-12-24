# SomaBrain API Reference

This document describes the REAL SomaBrain API endpoints as verified from the OpenAPI spec at `http://localhost:9696/openapi.json`.

**CRITICAL**: Only use endpoints documented here. Do NOT invent API methods.

## Base URL

```
SOMA_BASE_URL=http://localhost:9696
```

## Core Memory Endpoints

### POST /remember
Store a memory item.

**Request Body**: Flexible - accepts either `{payload: {...}}` or direct payload fields.

**Response**: `RememberResponse`
```json
{
  "ok": true,
  "success": true,
  "namespace": "string",
  "trace_id": "string"
}
```

### POST /recall
Recall memories by query.

**Request Body**: `RecallRequest`
```json
{
  "query": "string",
  "top_k": 3,
  "universe": "string|null"
}
```

**Response**: `RecallResponse`
```json
{
  "wm": [{"score": 0.9, "payload": {...}}],
  "memory": [...],
  "namespace": "string",
  "trace_id": "string",
  "results": []
}
```

### POST /delete
Delete a memory by coordinate.

**Request Body**: `DeleteRequest`
```json
{
  "coordinate": [0.1, 0.2, 0.3]
}
```

## Neuromodulation Endpoints

### GET /neuromodulators
Get current neuromodulator state (global, not per-tenant).

**Response**: `NeuromodStateModel`
```json
{
  "dopamine": 0.4,
  "serotonin": 0.5,
  "noradrenaline": 0.0,
  "acetylcholine": 0.0
}
```

### POST /neuromodulators
Set neuromodulator state (global, not per-tenant).

**Request Body**: `NeuromodStateModel`
```json
{
  "dopamine": 0.6,
  "serotonin": 0.7,
  "noradrenaline": 0.1,
  "acetylcholine": 0.0
}
```

**Response**: Returns the updated `NeuromodStateModel`

## Adaptation Endpoints

### GET /context/adaptation/state
Get current adaptation weights and history.

**Query Parameters**:
- `tenant_id` (optional): Filter by tenant

**Response**: `AdaptationStateResponse`
```json
{
  "retrieval": {"alpha": 0.5, "beta": 0.5, "gamma": 0.5, "tau": 0.5},
  "utility": {"lambda_": 0.5, "mu": 0.5, "nu": 0.5},
  "history_len": 100,
  "learning_rate": 0.01,
  "gains": {"alpha": 0.1, "gamma": 0.1, "lambda_": 0.1, "mu": 0.1, "nu": 0.1},
  "constraints": {...}
}
```

### POST /context/adaptation/reset
Reset adaptation engine to defaults.

**Request Body**: `ResetAdaptationRequest`
```json
{
  "tenant_id": "string|null",
  "base_lr": 0.01,
  "reset_history": true
}
```

## Sleep/Consolidation Endpoints

### POST /sleep/run
Trigger a sleep cycle (memory consolidation).

**Request Body**: `SleepRunRequest`
```json
{
  "nrem": true,
  "rem": true
}
```

**Response**: `SleepRunResponse`
```json
{
  "ok": true,
  "run_id": "string|null"
}
```

### GET /sleep/status
Get current sleep status.

**Response**: `SleepStatusResponse`
```json
{
  "enabled": true,
  "interval_seconds": 3600,
  "last": {"nrem": 1234567890.0, "rem": 1234567890.0}
}
```

### POST /api/util/sleep
Transition tenant sleep state.

**Request Body**: `SleepRequest`
```json
{
  "target_state": "active|light|deep|freeze",
  "ttl_seconds": 300,
  "async_mode": false,
  "trace_id": "string|null"
}
```

### POST /api/brain/sleep_mode
Cognitive-level sleep state transition (same as /api/util/sleep).

## Context Endpoints

### POST /context/evaluate
Evaluate context for a query.

**Request Body**: `EvaluateRequest`
```json
{
  "session_id": "string",
  "query": "string",
  "top_k": 5,
  "tenant_id": "string|null"
}
```

### POST /context/feedback
Submit feedback for adaptation.

**Request Body**: `FeedbackRequest`
```json
{
  "session_id": "string",
  "query": "string",
  "prompt": "string",
  "response_text": "string",
  "utility": 0.8,
  "reward": 0.9,
  "tenant_id": "string|null"
}
```

## Persona Endpoints

### PUT /persona/{pid}
Create or update a persona.

**Headers**: `If-Match` (optional ETag for CAS)

**Request Body**: `Persona`
```json
{
  "id": "string",
  "display_name": "string|null",
  "properties": {},
  "fact": "persona"
}
```

### GET /persona/{pid}
Get a persona by ID.

### DELETE /persona/{pid}
Delete a persona.

## Planning Endpoints

### POST /plan/suggest
Suggest a plan from semantic graph.

**Request Body**: `PlanSuggestRequest`
```json
{
  "task_key": "string",
  "max_steps": 5,
  "rel_types": ["string"],
  "universe": "string|null"
}
```

**Response**: `PlanSuggestResponse`
```json
{
  "plan": ["step1", "step2", "step3"]
}
```

## Health Endpoints

### GET /health
System health check.

**Response**: `HealthResponse`
```json
{
  "ok": true,
  "components": {...}
}
```

---

## Client Implementation Status

The `python/integrations/soma_client.py` has been updated to correctly call the SomaBrain API:

| Client Method | Actual Endpoint | Status |
|---------------|-----------------|--------|
| `get_neuromodulators(tenant_id, persona_id)` | `GET /neuromodulators` | ✅ FIXED - params accepted for compatibility but not sent |
| `update_neuromodulators(tenant_id, persona_id, neuromodulators)` | `POST /neuromodulators` | ✅ FIXED - params accepted for compatibility but not sent |
| `get_adaptation_state(tenant_id, persona_id)` | `GET /context/adaptation/state?tenant_id=X` | ✅ FIXED - persona_id ignored |
| `sleep_cycle(tenant_id, persona_id, duration_minutes)` | `POST /sleep/run` | ✅ FIXED - uses nrem/rem bools |

All methods now correctly call the real SomaBrain endpoints.
