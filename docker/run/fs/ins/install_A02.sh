#!/bin/bash
set -e

# cachebuster script, this helps speed up docker builds

# remove repo (if not local branch)
if [ "$1" != "local" ]; then
    rm -rf /git/agent-zero

    # run the original install script again only for remote branches so cached layers stay warm
    bash /ins/install_A0.sh "$@"
else
    echo "Skipping reinstall for local sources; dependencies already provisioned"
fi

# remove python packages cache
. "/ins/setup_venv.sh" "$@"
pip cache purge
uv cache prune