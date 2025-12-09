# API Reference

This document provides a summary of the API endpoints for the Agent Zero application.

## Chat

### `POST /api/v1/chat`

This endpoint is used to send a message to an agent and queue a chat task for asynchronous processing.

**Request Body:**

| Parameter | Type | Description |
|---|---|---|
| `agent_url` | `str` | The URL of the remote agent to communicate with. |
| `message` | `str` | The message to send to the agent. |
| `attachments` | `Optional[List[str]]` | A list of attachment URLs. |
| `reset` | `bool` | Whether to reset the conversation history. |
| `session_id` | `Optional[str]` | The session ID for conversation tracking. |
| `metadata` | `Optional[Dict[str, Any]]` | Optional metadata to include with the request. |

**Response Body:**

| Parameter | Type | Description |
|---|---|---|
| `task_id` | `str` | The ID of the Celery task that was created to process the chat request. |
| `status` | `str` | The status of the task (e.g., `queued`). |
| `message` | `str` | A message indicating the status of the request. |
| `session_id` | `str` | The session ID for the conversation. |

### `GET /api/v1/chat/status/{task_id}`

This endpoint is used to get the status and result of a chat task.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `task_id` | `str` | The ID of the task to get the status of. |

**Response Body:**

| Parameter | Type | Description |
|---|---|---|
| `task_id` | `str` | The ID of the task. |
| `status` | `str` | The status of the task (e.g., `completed`, `failed`). |
| `result` | `Optional[str]` | The result of the task if it has completed. |
| `error` | `Optional[str]` | The error message if the task has failed. |
| `started_at` | `Optional[float]` | The timestamp when the task started. |
| `completed_at` | `Optional[float]` | The timestamp when the task completed. |
| `duration` | `Optional[float]` | The duration of the task in seconds. |

### `GET /api/v1/chat/history/{session_id}`

This endpoint is used to get the conversation history for a given session.

**Path Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `str` | The ID of the session to get the history for. |

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `limit` | `int` | The maximum number of messages to return. Defaults to `50`. |

**Response Body:**

| Parameter | Type | Description |
|---|---|---|
| `session_id` | `str` | The ID of the session. |
| `messages` | `List[Dict[str, Any]]` | A list of the messages in the conversation. |
| `total_messages` | `int` | The total number of messages in the conversation. |

## Health

### `GET /api/v1/health`

This endpoint is used to check the health of the FastAPI service and its dependencies.

**Response Body:**

| Parameter | Type | Description |
|---|---|---|
| `status` | `str` | The overall health status (e.g., `healthy`, `degraded`). |
| `timestamp` | `float` | The timestamp of the health check. |
| `services` | `Dict[str, Any]` | A dictionary containing the health status of each service. |
| `version` | `str` | The version of the API. |

### `GET /healths`

This endpoint is used to check the health of all core services and return a hierarchical status.

## Metrics

### `GET /api/v1/metrics`

This endpoint is used to expose Prometheus metrics.
