#!/usr/bin/env bash
set -euo pipefail

# Preflight validation enforces canonical env and dependency readiness
python scripts/preflight.py

# Start Gateway (no reload)
exec /opt/venv/bin/uvicorn services.gateway.main:app --host 0.0.0.0 --port "${PORT:-8010}"
