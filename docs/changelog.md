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
- Restored SSE streaming path for chat via `/v1/session/{id}/events`.
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
- Legacy documentation files not aligned with ISO structure
- Deprecated gRPC memory service documentation
