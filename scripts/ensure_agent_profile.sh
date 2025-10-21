#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_DIR="$ROOT_DIR/agents"
DEFAULT_AGENT_DIR="$AGENTS_DIR/agent0"

mkdir -p "$AGENTS_DIR"
if [ ! -d "$DEFAULT_AGENT_DIR" ]; then
  echo "Creating default agent profile at $DEFAULT_AGENT_DIR"
  mkdir -p "$DEFAULT_AGENT_DIR"
  cat > "$DEFAULT_AGENT_DIR/profile.json" <<'EOF'
{
  "name": "agent0",
  "display_name": "Default Agent 0",
  "description": "Auto-created default agent for local dev",
  "model": "groq"
}
EOF
else
  echo "Default agent profile already exists"
fi

# Ensure tmp/settings.json points to agent0 as default if present
SETTINGS_FILE="$ROOT_DIR/tmp/settings.json"
if [ -f "$SETTINGS_FILE" ]; then
  if ! grep -q 'agent0' "$SETTINGS_FILE" 2>/dev/null; then
    echo "Patching $SETTINGS_FILE to set default agent to agent0"
    jq '.agent_profile = "agent0"' "$SETTINGS_FILE" > "$SETTINGS_FILE.tmp" && mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE" || true
  fi
fi

echo "Agent profile check complete."
