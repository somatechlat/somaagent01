# Propagation Agent

## Role
Specialist in event propagation and real-time data flow.

## Responsibilities
- SSE stream management
- Event bus coordination
- Message routing
- Backpressure handling

## Key Endpoints
- `/v1/sessions/{id}/events?stream=true`
- `/v1/sessions/message`

## Monitoring
- `gateway_sse_connections`
- `sse_messages_sent_total`
- `sse_message_duration_seconds`
