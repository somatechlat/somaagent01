#!/usr/bin/env bash
set -euo pipefail

# Configurable ports
UI_PORT="${UI_PORT:-21015}"
GW_PORT="${GW_PORT:-21016}"
GW_URL="http://127.0.0.1:${GW_PORT}"

echo "== E2E Local UI Runner =="

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Desktop and retry." >&2
  exit 1
fi

echo "[1/7] Build & start gateway + workers (dev) ..."
docker compose -p somaagent01_dev -f docker-compose.yaml up -d --build gateway conversation-worker memory-replicator

echo "[2/7] Wait for Gateway health ($GW_URL/healthz) ..."
for i in $(seq 1 60); do
  if curl -fsS "$GW_URL/healthz" >/dev/null; then echo "Gateway healthy"; break; fi
  sleep 1
  if [[ $i -eq 60 ]]; then echo "Gateway failed to become healthy" >&2; exit 1; fi
done

echo "[3/7] Apply LLM credentials and dialogue profile (idempotent) ..."
curl -fsS -X POST "$GW_URL/v1/llm/credentials" -H 'Content-Type: application/json' \
  -d "{\"provider\":\"groq\",\"secret\":\"${GROQ_API_KEY:-}\"}" >/dev/null || true
curl -fsS -X PUT "$GW_URL/v1/ui/settings" -H 'Content-Type: application/json' \
  -d '{"model_profile":{"model":"openai/gpt-oss-120b","base_url":"https://api.groq.com/openai/v1","temperature":0.2}}' >/dev/null || true

echo "[4/7] Create Python venv and install UI deps ..."
python3 -m venv .uv-venv >/dev/null 2>&1 || true
source .uv-venv/bin/activate
pip install -U pip wheel setuptools >/dev/null
pip install -r requirements.txt websockets aiohttp pathspec python-crontab numpy >/dev/null

echo "[5/7] Start UI on http://127.0.0.1:${UI_PORT} (Gateway: $GW_URL) ..."
export UI_USE_GATEWAY=true
export UI_GATEWAY_BASE="$GW_URL"
export UI_ENABLE_MCP=false
export UI_ENABLE_A2A=false
export UI_ENABLE_JOB_LOOP=false
python -u run_ui.py --host=127.0.0.1 --port="${UI_PORT}"

echo "UI stopped."

