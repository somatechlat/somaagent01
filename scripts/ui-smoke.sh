#!/usr/bin/env bash
set -euo pipefail

# Simple wrapper to run the Playwright UI smoke test without long commands.
# Usage: ./scripts/ui-smoke.sh [BASE_URL]
# Example: ./scripts/ui-smoke.sh http://127.0.0.1:21016/

# UI is now served at the root URL without a trailing '/ui'.
BASE_URL="${1:-${WEB_UI_BASE_URL:-http://localhost:${GATEWAY_PORT:-21016}}"

echo "Running UI smoke against ${BASE_URL} ..."
WEB_UI_BASE_URL="${BASE_URL}" python3 tests/ui_smoke_http.py
