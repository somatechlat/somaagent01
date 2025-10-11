# Tool Executor Callback API

After executing a tool invocation, the executor reports results back to the Gateway so conversations can continue.

## Kafka Topics

| Topic | Direction | Description |
| --- | --- | --- |
| `somastack.tools` | Gateway ➜ Executor | Tool invocation requests |
| `somastack.tool_results` | Executor ➜ Gateway | Execution results, errors |

Messages are JSON objects with a shared envelope:

```json
{
  "task_id": "uuid",
  "tenant_id": "default",
  "persona": "agent0",
  "tool_name": "shell",
  "payload": {
    "command": "ls -la"
  },
  "metadata": {
    "correlation_id": "conversation-uuid",
    "initiated_by": "gateway"
  }
}
```

## HTTP Callback (Optional)

Executors can POST results directly to Gateway (configured via settings):

`POST /tool_callback`

```json
{
  "task_id": "uuid",
  "status": "success",
  "output": {
    "stdout": "...",
    "stderr": "",
    "artifacts": []
  }
}
```

Gateway validates `task_id`, updates conversation state, and streams result to UI.

## Status Codes

| Status | Meaning |
| --- | --- |
| `success` | Tool finished normally |
| `failed` | Tool encountered an error; include `error` field |
| `retry` | Executor wants Gateway to requeue the task |

## Idempotency

- Executor must ensure multiple sends with same `task_id` are safe.
- Gateway deduplicates by `task_id` and ignores stale updates.

## Security

- Kafka: SASL/SSL configurable in production deployments.
- HTTP: Signed bearer tokens or mTLS recommended.

## Monitoring

- Metrics: `tool_results_total` by status, `tool_latency_seconds` histogram.
- Logs: structured entries with correlation ID for traceability.

## Failure Handling

- If Gateway is unavailable, executor retries with backoff.
- After max retries, message lands in dead-letter topic `somastack.tool_results.dlq`.
- Operators inspect DLQ, requeue via `scripts/kafka_partition_scaler.py` or custom tooling.

## Testing

- Unit: mock Kafka consumer producing tasks to executor.
- Integration: run executor against local Kafka (spin up via `make dev-up`), assert callbacks update conversation history.
