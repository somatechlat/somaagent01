# Feature: Real-Time Propagation

## Overview
Real-time event propagation enables instant updates across the system using Server-Sent Events (SSE).

## How It Works
- Single SSE stream per session at `/v1/sessions/{session_id}/events?stream=true`
- Canonical event types: `assistant.delta`, `assistant.final`, `tool.start`, `tool.result`
- Heartbeat events every 20 seconds to detect connection issues
- Automatic reconnection with exponential backoff

## Event Types

### assistant.delta
Streaming token updates during LLM response generation.

### assistant.final
Final complete response with metadata.

### tool.start
Tool execution started notification.

### tool.result
Tool execution result with output data.

### system.keepalive
Heartbeat event to maintain connection health.

## Client Implementation
See the Web UI implementation in `webui/js/stream.js` for reference client code.

## Configuration
- `SSE_HEARTBEAT_SECONDS`: Heartbeat interval (default: 20)
- `SA01_SSE_ENABLED`: Enable/disable SSE streaming (default: true)

## Monitoring
SSE connection metrics:
- `gateway_sse_connections`: Active SSE connections
- `sse_messages_sent_total`: Total messages sent
- `sse_message_duration_seconds`: Message delivery latency
