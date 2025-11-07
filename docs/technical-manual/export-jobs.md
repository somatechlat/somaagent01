# Export Jobs

This page describes asynchronous memory export jobs handled by the Gateway.

## What They Do

Export jobs produce an NDJSON file of memory replica rows that match your filters. They run in the background and you can poll for status and download when complete.

- Format: NDJSON (one JSON object per line)
- Scope: Rows from the memory replica (read-only view)
- Filters: `tenant`, `persona_id`, `role`, `session_id`, `universe`, `namespace`, text `q`, time range (`min_ts`, `max_ts`), and an optional `limit_total`

## Enabling Export Jobs

By default, local file writes are disabled and the export runner is off. Enable with environment flags:

- `DISABLE_FILE_SAVING=false` (or `GATEWAY_DISABLE_FILE_SAVING=false`)
- `EXPORT_JOBS_ENABLED=true`
- Optional:
  - `EXPORT_JOBS_DIR=/data/exports` (default: `/tmp/soma_export_jobs`)
  - `EXPORT_JOBS_MAX_ROWS=100000` (upper bound)
  - `EXPORT_JOBS_PAGE_SIZE=1000` (DB page size)
  - `EXPORT_JOBS_CONCURRENCY=1` (worker concurrency)
  - `EXPORT_JOBS_POLL_SECONDS=2` (queue poll interval)
  - `GATEWAY_EXPORT_REQUIRE_TENANT=true` to require a `tenant` in job params

The runner starts automatically in the Gateway when `EXPORT_JOBS_ENABLED=true` and file saving is enabled.

## Endpoints

All endpoints are policy-gated. Admin scope is required when auth is enabled. File saving must be enabled.

- POST `/v1/memory/export/jobs` — create a job
- GET `/v1/memory/export/jobs/{job_id}` — get status
- GET `/v1/memory/export/jobs/{job_id}/download` — download NDJSON file (when completed)

### Create Job

Request body (any subset):
```json
{
  "tenant": "acme",
  "persona_id": "default",
  "role": "assistant",
  "session_id": "abc123",
  "universe": "u1",
  "namespace": "wm",
  "q": "error OR timeout",
  "min_ts": 1730937600,
  "max_ts": 1731024000,
  "limit_total": 50000
}
```

Response:
```json
{ "job_id": 42, "status": "queued" }
```

Curl example:
```bash
curl -s -X POST http://localhost:21016/v1/memory/export/jobs \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <admin-jwt>' \
  -d '{"tenant":"acme","q":"timeout","limit_total":2000}'
```

### Check Status

Response contains a `download_url` when ready:
```json
{
  "id": 42,
  "status": "completed",
  "row_count": 1987,
  "byte_size": 4123456,
  "download_url": "/v1/memory/export/jobs/42/download"
}
```

Curl example:
```bash
curl -s http://localhost:21016/v1/memory/export/jobs/42 \
  -H 'Authorization: Bearer <admin-jwt>' | jq .
```

### Download File

Content type is `application/x-ndjson`.
```bash
curl -L http://localhost:21016/v1/memory/export/jobs/42/download \
  -H 'Authorization: Bearer <admin-jwt>' -o export_42.ndjson
```

## File Contents

Each line is a JSON object with the following fields:
```json
{
  "id": 123,
  "event_id": "evt_...",
  "session_id": "abc123",
  "persona_id": "default",
  "tenant": "acme",
  "role": "assistant",
  "coord": "...",
  "request_id": "...",
  "trace_id": "...",
  "wal_timestamp": 1731000000.123,
  "created_at": "2025-11-07T10:00:00.000Z",
  "payload": { /* original memory payload */ }
}
```

## Operational Notes

- Jobs are queued in Postgres and processed by a lightweight in-process worker.
- Runner concurrency is controlled via `EXPORT_JOBS_CONCURRENCY`.
- Exports are written atomically using a `*.part` temp file then `os.replace`.
- If a job fails, status moves to `failed` and the `error` string is set.
- Download may return 410 if the file was removed (e.g., after cleanup).

## Troubleshooting

- 403 "File export is disabled": ensure `DISABLE_FILE_SAVING=false`.
- 400 "tenant parameter required": set `GATEWAY_EXPORT_REQUIRE_TENANT=false` or include `tenant`.
- 409 "job not completed": wait for `status=completed`.
- Runner not starting: set `EXPORT_JOBS_ENABLED=true`; check Gateway logs for schema init.
