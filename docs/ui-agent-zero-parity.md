# Web UI Parity with Agent Zero

This report captures file-level differences between the current web UI in this repository (`webui/`) and the Agent Zero reference UI, and maps each delta to a Gateway-aligned decision: keep (intentional deviation), change (port behavior), or defer (requires backend support). Code remains the source of truth; we avoid reintroducing legacy endpoints or CSRF flows.

## Scope and sources
- Current: `webui/` in this repo
- Reference: `tmp/agent-zero/webui` (and corroborating second reference path found previously)

## Parity summary
- Architecture: Current UI is Gateway-first. All traffic uses `/v1/*` UI-shaped endpoints where available; no CSRF token dance; no legacy workdir file endpoints.
- Notifications: Unified toast stack via `components/notifications/*`, replacing legacy #toast.
- Modals: Robust backdrop + stack management (`js/modals.js`) vs. simpler reference.
- Attachments: Gateway attachments paths only; no `/download_work_dir_file` or `image_get` fallbacks.
- Settings: Uses `/v1/ui/settings/sections` and `/v1/ui/settings/credentials`; AV test exists; tab filter + synthesized Tunnel section.
- Speech: Realtime and Kokoro gracefully disabled; browser TTS is fallback. STT disabled with gentle warning. No legacy `/synthesize` or `/transcribe`.
- Memory Dashboard: Canonical endpoints live under `/v1/memories/*`. A legacy `/memory_dashboard` compatibility shim may exist temporarily; prefer `/v1/memories/*` going forward.

## File-level gaps and decisions

1) `webui/js/api.js`
- Reference: CSRF token retrieval from `/csrf_token` and header `X-CSRF-Token`.
- Current: Base URL resolver using `__SA01_CONFIG__.api_base`, same-origin credentials, login redirect handling.
- Decision: KEEP current. CSRF is unnecessary for our Gateway flow; same-origin and header auth suffice.

2) `webui/js/settings.js`
- Reference: Legacy `/settings_get`, `/api/settings_get/save`, a vestigial `test_connection` action.
- Current: `/v1/ui/settings/sections` (GET/POST), credentials presence badges via `/v1/ui/settings/credentials`, AV test button hitting `/v1/av/test`, synthesized Tunnel section, read-only toggling for Uploads/AV.
- Decision: KEEP. No changes needed.

3) `webui/components/chat/attachments/attachmentsStore.js`
- Reference: Legacy workdir endpoints and name+size dedup only.
- Current: Gateway-only attachments paths, stronger dedup via seen keys, uniform preview icons.
- Decision: KEEP. No changes needed.

4) `webui/components/chat/speech/speech-store.js`
- Reference: Optional Kokoro + backend `/synthesize` and `/transcribe`; no `/v1` integration.
- Current: Hydrates from `/v1/ui/settings/sections`; realtime provider scaffolding exists but returns a friendly fallback; browser TTS is default; STT path is disabled with a clear user toast.
- Decision: KEEP for now. CHANGE later only if backend adds `/v1/realtime/session` and `/v1/stt/transcribe`.
- Follow-up (defer): Add realtime once a Gateway endpoint exists; add STT if we expose `/v1/speech/transcribe`.

5) `webui/js/modals.js`
- Reference: Static backdrop, simpler z-index handling.
- Current: ensureBackdrop(), safe initialization before body, stacked modals with interleaved backdrop.
- Decision: KEEP. No changes needed.

6) `webui/index.html`
- Reference: Different script order, legacy toast section.
- Current: Loads `initFw.js` early, unified toast stack component, service worker registration, scheduler scaffolding.
- Decision: KEEP. No changes needed.
- Note: Implemented pre-paint theme bootstrap to prevent first-load flicker. An inline script in `<head>` applies `.dark-mode`/`.light-mode` based on `localStorage.darkMode` before CSS loads; body mirrors the class on `DOMContentLoaded`. This aligns first render with the saved preference and removes the initial CSS glitch.

7) `webui/components/settings/memory/memory-dashboard-store.js`
- Reference: Use `/v1/memories` and related endpoints for search, update, delete, bulk_delete, and subdir listing.
- Current: Transition to `/v1/memories/*` endpoints with pagination and improved UX; legacy shim support may still be present for older clients.
- Decision: KEEP. Gateway compatibility route is present (`services/gateway/main.py`), so no legacy surface is reintroduced.

8) `webui/components/settings/tunnel/*`
- Reference: Tunnel-specific assets present; behavior relies on a tunnel proxy route.
- Current: Synthesized Tunnel section in Settings; store calls `/tunnel_proxy` which is implemented by Gateway.
- Decision: KEEP. No changes needed.

9) Notifications (`components/notifications/notification-store.js`)
- Reference: Simpler toasts.
- Current: Unified stack with priorities, grouping, and frontend-only helpers to avoid backend 404s.
- Decision: KEEP. No changes needed.

## Missing or intentionally disabled features
- Realtime speech: Disabled with graceful fallback. Requires backend `/v1` session endpoint and signaling.
- STT: Disabled with gentle warning. Requires `/v1` transcribe endpoint and model config. We’ll wire this only when Gateway exposes it.

## Tests and validation
- Gateway health: PASS (task: Gateway: Health).
- UI smoke (Playwright): Executed installer; see next steps for ensuring test run output is captured. No functional regressions observed during manual checks.

## Next steps
- Optional: When backend exposes realtime/STT endpoints, enable those branches in `speech-store.js` and add minimal UI toggle tests.
- Optional: Add an explicit Model Connectivity test in Settings to validate provider credentials (maps to `/v1/llm/credentials` or `/v1/llm/ping`).
- Docs alignment: Update any mentions of CSRF/legacy endpoints to reflect `/v1/ui/*` and canonical `/v1/memories/*` endpoints.

