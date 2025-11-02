# 2025-11-02 Update — Centralized UI preferences and parity tests

This addendum documents the consolidation of UI header toggle preferences in the Gateway and the new golden-vs-local UI parity tests.

## What changed
- Introduced a small, focused Gateway API for lightweight UI preferences:
  - GET /v1/ui/preferences
  - PUT /v1/ui/preferences
- Preferences are stored in the existing Postgres-backed `ui_settings` document under `preferences`.
- The Web UI (Alpine.js SPA) now:
  - Loads preferences on boot and applies them (Show Thoughts, Show JSON, Show Utility Messages)
  - Persists user toggles immediately via PUT /v1/ui/preferences
  - Uses safe defaults if the preferences document is absent
- Added Playwright suite for UX parity: `tests/playwright/test_ui_flows_parity.py` which validates:
  - No duplicate AI replies on a single prompt
  - New chat creation, reset clears, and delete updates selection/list
  - Upload POST observable in network
  - Header toggle persistence across reloads
  - Tool echo visibility in-stream
  - Runs against golden (7001) when reachable; always runs locally (21016)

## Why this matters
- Establishes the Gateway as the single configuration plane for UI preferences—no UI-only state.
- Provides a repeatable golden-vs-local test harness to guard behavior, ensuring feature parity converges over time.

## Next steps
- Extend parity tests to include styling and label assertions for chat bubbles and the thinking indicator.
- Add a CI job to run the parity suite headless for local; optionally run against golden when the environment exposes it.
- Expand tests to uploads progress, tool panel lifecycle, and memory dashboard read-only views.
