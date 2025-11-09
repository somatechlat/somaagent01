# Developer Mode Parity Plan

## Goals
- Local environment behavior mirrors production features (flags, rate limits, topic names) with safe defaults.
- Simple onboarding: one `make dev` brings up all required dependencies.
- Deterministic seeds for profiles, tool catalog entries, tenants, feature flags.

## Compose Profiles
- `docker-compose.yaml` base: add `profiles:` for optional services (clamav, somabrain mock, tracing collector, grafana).
- `docker-compose.dev.yaml` overlay: mounts source, enables watch reload, exposes metrics ports.

## Make Targets
- `make dev`: build images (or use host .venv), start compose with dev profile.
- `make seed`: run seed script for model profiles, tool catalog, API keys.
- `make test-fast`: run unit tests excluding integration requiring external services.

## Feature Flags
Expose environment or config registry overlays with defaults:
- `GATEWAY_WRITE_THROUGH` false by default.
- `SA01_ENABLE_TOOL_EVENTS` false.
- `speech_realtime_enabled` false.

## Tooling
- Add `scripts/seed_dev_data.py` populating: profiles, a test API key, sample notification.
- Provide `.env.example` listing required variables with comments.

## Debugging & Observability
- Enable verbose logging + trace sampling (100%) in dev.
- Expose Prometheus and Jaeger/Tempo ports.
- Provide `scripts/trace_dump.py` to query recent spans via OTLP exporter fallback.

## Next Steps
1. Add compose dev profile scaffolds.
2. Add seed script and Make target.
3. Add .env.example file.
4. Document workflow in README.
