#!/usr/bin/env bash
set -euo pipefail

POLICY=${1:-policy/tool_policy.rego}

# Echo tool should be allowed
opa eval --fail-defined --data "$POLICY" --input - 'data.soma.policy.allow' <<'JSON'
{
  "action": "tool.execute",
  "resource": "echo",
  "context": {"args": {}}
}
JSON

echo "[PASS] echo tool allowed"

# Timestamp tool with DENY format should be blocked
RESULT=$(opa eval --data "$POLICY" --input - 'data.soma.policy.allow' <<'JSON'
{
  "action": "tool.execute",
  "resource": "timestamp",
  "context": {"args": {"format": "DENY"}}
}
JSON
)

if echo "$RESULT" | grep -q 'true'; then
  echo "[FAIL] timestamp tool denial regression"
  exit 1
fi

echo "[PASS] timestamp tool denied with format DENY"
