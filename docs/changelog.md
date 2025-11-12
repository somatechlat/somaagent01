# Changelog

**Standards**: ISO/IEC 12207§8.2

All notable changes to SomaAgent01 documentation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-24

## [1.1.0] - 2025-11-02

### Added
- Technical Manual: "LLM Routing & Settings" documenting Gateway LLM normalization, provider detection, credentials, and model lock behavior.

### Changed
- Web UI now sources all configuration from Gateway Settings; credentials must be entered via Settings, not env vars.
- Files UI wired to `/v1/workdir` and Memories UI to `/v1/memories` for live parity.
- Restored SSE streaming path for chat via `/v1/sessions/{id}/events?stream=true`.
- Base URL normalization updated to remap OpenRouter paths ending in `/openai` to `/api`, preventing 405 errors.
- Quick Start and Troubleshooting updated to reflect Gateway host port 21016 and Settings‑driven configuration.

### Fixed
- Provider 405 with OpenRouter due to incorrect base path.
- Model profile persistence issues leading to wrong provider selection; Groq profile now saves and is used globally.

### Added
- ISO-compliant documentation structure
- Four core manuals (User, Technical, Development, Onboarding)
- Style guide and glossary
- Architecture documentation with C4 diagrams
- Standards compliance mapping (ISO/IEC 12207, 42010, 29148, 21500, 27001)

### Changed
- Restructured documentation to align with ISO standards
- Consolidated scattered READMEs into proper manual sections

### Removed
- Prior documentation files not aligned with ISO structure
- Deprecated gRPC memory service documentation

## [1.2.0] - 2025-11-03

### Added
- Technical Manual: SomaBrain Integration Guide covering API contracts, persona-aware metadata, admin metrics and migration endpoints, and policy decision receipts.
- Gateway admin endpoints:
	- `GET /v1/admin/memory/metrics` → proxied SomaBrain memory metrics
	- `POST /v1/admin/migrate/export` and `POST /v1/admin/migrate/import`
- Persona-aware memory metadata enrichment in Conversation Worker.
- Decision receipts for OPA/OpenFGA in Gateway authorization (best-effort audit log).

### Changed
- OpenFGA enforcement now skips in dev/unit contexts when not configured, while still emitting a decision receipt; production remains fail-closed when configured.

### Tests
- Unit tests for admin endpoints, expanding coverage without requiring e2e multimedia dependencies.

## [1.2.1] - 2025-11-06

### Changed
- Web UI theme bootstrap now applies before first paint to prevent initial flicker and incorrect styles on first interaction. Implemented an inline pre-paint script in `webui/index.html` that reads `localStorage.darkMode` and sets `.dark-mode`/`.light-mode` on `<html>` and mirrors to `<body>` on `DOMContentLoaded`.

### Fixed
- First-load CSS glitch where the wrong theme briefly appeared until the first message or DOM event updated the class list.
- Playwright selector alignment by adding `id="status-indicator"` (parity with test expectations).
- Metrics server startup conflict during tests now degrades gracefully (no retry storms) when port is already in use.

### Notes
- Continued enforcement of SSE-only streaming and canonical uploads + `document_ingest` tool flow; CSRF fully removed and prior endpoints purged.
