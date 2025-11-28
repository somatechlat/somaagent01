#!/usr/bin/env bash

# This helper script runs the project's pytest suite in the background.
# It is useful during development when you want to keep the test suite
# executing while you continue to implement features (e.g., observability,
# Helm refactor, load tests).  The script redirects both stdout and stderr to
# a log file so you can inspect results later.

# Ensure the virtual environment is activated. If the script is executed from
# the repository root, the .venv directory is expected to exist.
if [ -f ".venv/bin/activate" ]; then
    source ".venv/bin/activate"
else
    echo "Virtual environment not found. Please create it first (python -m venv .venv)."
    exit 1
fi

LOG_FILE="pytest_background.log"

# Run pytest in the background, redirecting output.
nohup python -m pytest -q > "$LOG_FILE" 2>&1 &

PID=$!
echo "pytest started in background (PID=$PID). Logging to $LOG_FILE"
