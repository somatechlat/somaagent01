#!/usr/bin/env bash
set -euo pipefail

GW_PORT="${GATEWAY_PORT:-21016}"
GW_BASE="http://localhost:${GW_PORT}"

if [[ -z "${GROQ_API_KEY:-}" ]]; then
  echo "[ERROR] GROQ_API_KEY environment variable not set. Export it first:"
  echo "  export GROQ_API_KEY=sk_..."
  exit 1
fi

echo "[INFO] Saving Groq model profile + credential via sections endpoint"
curl -sS -X POST "${GW_BASE}/v1/settings/sections" \
  -H 'Content-Type: application/json' \
  -d "{\n    \"sections\": [\n      { \"id\": \"llm\", \"fields\": [\n        { \"id\": \"chat_model_provider\", \"value\": \"groq\" },\n        { \"id\": \"chat_model_name\", \"value\": \"llama-3.1-8b-instant\" },\n        { \"id\": \"chat_model_api_base\", \"value\": \"https://api.groq.com/openai/v1\" },\n        { \"id\": \"api_key_groq\", \"value\": \"${GROQ_API_KEY}\" }\n      ] }\n    ]\n  }" | jq '.settings.sections[] | select(.id=="llm")'

echo "[INFO] Credential status (should show groq present + updated_at)"
curl -sS "${GW_BASE}/v1/settings/credentials" | jq .

echo "[INFO] Running connectivity test"
TEST_OUT=$(curl -sS -X POST "${GW_BASE}/v1/llm/test" -H 'Content-Type: application/json' -d '{"role":"dialogue"}')
echo "$TEST_OUT" | jq . || echo "$TEST_OUT"

if echo "$TEST_OUT" | grep -q '"reachable": true' && echo "$TEST_OUT" | grep -q '"credentials_present": true'; then
  echo "[INFO] Connectivity test passed"
else
  echo "[WARN] Connectivity test did not confirm reachability; inspect output above"
fi

echo "[INFO] Invoking chat (single-turn)"
INVOKE_OUT=$(curl -sS -X POST "${GW_BASE}/v1/llm/invoke" -H 'Content-Type: application/json' -H 'X-Internal-Token: dev-internal-token' -d '{"role":"dialogue","messages":[{"role":"user","content":"Respond with a single word: hello"}]}' )
echo "$INVOKE_OUT" | jq . || echo "$INVOKE_OUT"

if echo "$INVOKE_OUT" | grep -qi 'hello'; then
  echo "[INFO] Invocation appears successful"
else
  echo "[WARN] Invocation response did not contain expected content; check gateway logs"
fi

echo "[INFO] Done."