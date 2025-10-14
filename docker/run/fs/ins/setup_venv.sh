#!/bin/bash
set -e

# this has to be ready from base image
# if [ ! -d /opt/venv ]; then
#     # Create and activate Python virtual environment
#     python3.12 -m venv /opt/venv
#     source /opt/venv/bin/activate
# else
    # source /opt/venv/bin/activate
# fi
if [ -d /venv ]; then
    # Prefer the Dockerfile-created venv that exposes system site packages (asyncpg, grpcio, etc.).
    source /venv/bin/activate
elif [ -d /opt/venv-a0 ]; then
    source /opt/venv-a0/bin/activate
else
    echo "Error: expected virtual environment not found" >&2
    exit 1
fi