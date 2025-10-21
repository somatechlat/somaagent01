#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_PY="$ROOT_DIR/.venv/bin/python"
PYTHONPATH="$ROOT_DIR"
export PYTHONPATH
LOG_DIR="/tmp"

echo "Starting workers using python: $VENV_PY"

start_nohup() {
  local module=$1
  local name=$2
  local logfile="$LOG_DIR/${name}.log"
  echo "Starting $name (module: $module), logging to $logfile"
  nohup env PYTHONPATH="$PYTHONPATH" "$VENV_PY" -m "$module" > "$logfile" 2>&1 &
  echo "$name PID: $!"
}

# Conversation worker
start_nohup services.conversation_worker.main conversation_worker || true

# Tool executor
start_nohup services.tool_executor.main tool_executor || true

# Memory service (exposes an HTTP port)
start_nohup services.memory_service.main memory_service || true

echo "Workers started. Check logs under /tmp (conversation_worker.log, tool_executor.log, memory_service.log)"
