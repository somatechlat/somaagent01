#!/usr/bin/env bash
set -euo pipefail

# Simple wrapper to run the Playwright UI smoke test without long commands.
# Usage: ./scripts/ui-smoke.sh [BASE_URL]
# Example: ./scripts/ui-smoke.sh http://127.0.0.1:21016/

BASE_URL="${1:-${WEB_UI_BASE_URL:-http://localhost:${GATEWAY_PORT:-21016}/ui}}"

if [ ! -x ".venv/bin/python" ]; then
  echo "Creating Python venv (.venv) ..."
  python3 -m venv .venv
fi

echo "Installing Playwright browsers if needed ..."
. .venv/bin/activate
python -m pip -q install -U pip >/dev/null
python -m pip -q install -U -r requirements.txt >/dev/null
python -m playwright install --with-deps chromium >/dev/null 2>&1 || true

echo "Running UI smoke against ${BASE_URL} ..."
WEB_UI_BASE_URL="${BASE_URL}" .venv/bin/python tests/playwright/test_ui_smoke.py
