#!/bin/sh
# Thin wrapper: real bootstrap is bootstrap_exec.py (root stays in process RAM).
set -eu
target="$1"
shift
exec python3 /work/bootstrap_exec.py --target "$target" -- "$@"
