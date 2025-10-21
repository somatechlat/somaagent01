#!/bin/bash

.
# Setup virtualenv if available
. "/ins/setup_venv.sh" "$@" || true

# Copy A0 data if the helper exists (optional)
if [ -f "/ins/copy_A0.sh" ]; then
    . "/ins/copy_A0.sh" "$@" || true
fi

# If a legacy /a0 mount exists (from older A0-based deployments), use it.
# Otherwise, fall back to the current project layout under /git/agent-zero.
if [ -d "/a0" ] && [ -f "/a0/prepare.py" ]; then
    echo "Detected legacy /a0 layout; running A0 from /a0"
    python /a0/prepare.py --dockerized=true || true
    echo "Starting A0 from /a0..."
    exec python /a0/run_ui.py --dockerized=true --port=80 --host="0.0.0.0"
else
    echo "No /a0 layout detected; falling back to /git/agent-zero"
    if [ -f "/git/agent-zero/prepare.py" ]; then
        python /git/agent-zero/prepare.py --dockerized=true || true
    fi
    echo "Starting agent-zero UI from /git/agent-zero..."
    exec python /opt/venv-a0/bin/python /git/agent-zero/run_ui.py --dockerized=true --port=80 --host="0.0.0.0"
fi
    # --code_exec_ssh_enabled=true \
    # --code_exec_ssh_addr="localhost" \
    # --code_exec_ssh_port=22 \
    # --code_exec_ssh_user="root" \
    # --code_exec_ssh_pass="toor"
