#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test for the essential compose stack.
# Usage: ./scripts/smoke_test_essential.sh

DEFAULT_GATEWAY_PORT=8010
# Try to detect the host port mapped for the gateway service in the current compose file.
# If docker/compose lookup fails, fall back to localhost:DEFAULT_GATEWAY_PORT.
HOST_PORT=""
if command -v docker >/dev/null 2>&1; then
  # docker compose port returns '0.0.0.0:12345' or '127.0.0.1:12345' format; extract port
  HOST_PORT=$(docker compose -f docker-compose.essential.yaml port gateway ${DEFAULT_GATEWAY_PORT} 2>/dev/null || true)
  if [ -n "$HOST_PORT" ]; then
    # strip host portion
    HOST_PORT=${HOST_PORT##*:}
  else
    HOST_PORT=${GATEWAY_PORT:-$DEFAULT_GATEWAY_PORT}
  fi
else
  HOST_PORT=${GATEWAY_PORT:-$DEFAULT_GATEWAY_PORT}
fi
GATEWAY_URL=${GATEWAY_URL:-http://localhost:${HOST_PORT}}
HEALTH_URL="$GATEWAY_URL/health"
MSG_URL="$GATEWAY_URL/v1/sessions/message"

echo "Waiting for gateway health... ($HEALTH_URL)"
for i in {1..60}; do
  if curl -sSf "$HEALTH_URL" >/dev/null 2>&1; then
    echo "Gateway healthy"
    break
  fi
  echo -n '.'
  sleep 1
done

echo "Sending test message to $MSG_URL"
RESP=$(curl -sS -X POST "$MSG_URL" -H 'Content-Type: application/json' -d '{"message":"hello from smoke test"}')
echo "Response: $RESP"

if echo "$RESP" | grep -q "session_id"; then
  echo "Smoke test passed"
  exit 0
else
  echo "Smoke test failed"
  exit 2
fi
