---
title: Legacy External APIs
audience: integrators, maintainers
last-reviewed: 2025-10-17
---

# Legacy External APIs

These endpoints are served by the legacy Python API layer (`python/api/*`). They are not exposed by the FastAPI gateway and remain for backward compatibility. Prefer the versioned gateway under `/v1` for new integrations.

Base URL varies by deployment; examples assume the same host as the UI.

Endpoints

- POST `/api_message`
  - Send a message with optional attachments and `lifetime_hours`; returns `context_id` and response content.

- GET|POST `/api_log_get`
  - Retrieve recent logs for a given `context_id`.

- POST `/api_terminate_chat`
  - Delete a chat context by `context_id`.

- POST `/api_reset_chat`
  - Reset a chat context history while keeping the `context_id` active.

- POST `/api_files_get`
  - Retrieve previously uploaded files by absolute path; returns base64 payloads.

- POST `/realtime_session`
  - Broker a realtime speech session with a provider (OpenAI). Returns a short‑lived client secret for WebRTC negotiation.

Authentication

- X-API-KEY header where required.
- Some deployments also accept bearer tokens.

Notes

- These APIs may be removed in a future major release. Migrate clients to `/v1` equivalents where available.
