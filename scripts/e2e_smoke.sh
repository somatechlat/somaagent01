#!/usr/bin/env bash
set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:21016}"

echo "[1/4] Checking Gateway health at $GATEWAY_URL/healthz ..."
curl -fsS "$GATEWAY_URL/healthz" | jq . >/dev/null || {
  echo "Gateway health check failed. Ensure gateway is running and port is reachable: $GATEWAY_URL" >&2
  exit 1
}
echo "OK"

echo "[2/4] Posting a test message to $GATEWAY_URL/v1/session/message ..."
RESP=$(curl -fsS -X POST "$GATEWAY_URL/v1/session/message" \
  -H 'Content-Type: application/json' \
  -d '{"message":"Hello from e2e_smoke","metadata":{"tenant":"dev"}}')
echo "$RESP" | jq .
SID=$(echo "$RESP" | jq -r .session_id)
if [[ -z "$SID" || "$SID" == "null" ]]; then
  echo "Failed to obtain session_id from response." >&2
  exit 1
fi

echo "[3/4] Waiting a moment for worker to process ..."
sleep 3

echo "[4/4] Fetching session events ..."
curl -fsS "$GATEWAY_URL/v1/sessions/$SID/events?limit=200" | jq .
echo "Done. If you see an assistant message in events, end-to-end is healthy."

