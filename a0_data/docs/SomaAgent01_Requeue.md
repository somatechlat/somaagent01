⚠️ WE DO NOT MOCK we DO NOT IMITATE, WE DO NOT USE BYPASSES OR GIVE FAKE OR UNREAL VALUES TO PAST TESTS, we use MATH perfect math TO surpass any problem and we only abide truth and real serveres real data.

# SomaAgent 01 Requeue Workflow

Blocked tool executions (policy deny) are stored in Redis and exposed via the Requeue Service (`services/requeue_service`). Operators can list entries, requeue them with an override, or discard them.

## Redis Structure
- Each blocked event stored at `policy:requeue:<event_id>`.
- A set `policy:requeue:keys` keeps track of all pending identifiers.
- Requeue entries include the original tool payload plus timestamp metadata.

## Requeue Service Endpoints
- `GET /v1/requeue` → list all pending entries.
- `POST /v1/requeue/{id}/resolve` → remove entry; if `allow=true`, resubmits to `tool.requests` with `metadata.requeue_override=true` so the tool executor skips policy checks.
- `DELETE /v1/requeue/{id}` → remove entry without re-executing.

Implementation in `services/requeue_service/main.py` using FastAPI + common modules.
