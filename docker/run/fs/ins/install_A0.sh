#!/bin/bash
set -e

# Exit immediately if a command exits with a non-zero status.
# set -e

# branch from parameter
if [ -z "$1" ]; then
    echo "Error: Branch parameter is empty. Please provide a valid branch name."
    exit 1
fi
BRANCH="$1"

if [ "$BRANCH" = "local" ]; then
    # For local branch, use the files
    echo "Using local dev files in /git/agent-zero"
    # List all files recursively in the target directory
    # echo "All files in /git/agent-zero (recursive):"
    # find "/git/agent-zero" -type f | sort
else
    # For other branches, clone from GitHub
    echo "Cloning repository from branch $BRANCH..."
    git clone -b "$BRANCH" "https://github.com/agent0ai/agent-zero" "/git/agent-zero" || {
        echo "CRITICAL ERROR: Failed to clone repository. Branch: $BRANCH"
        exit 1
    }
fi

. "/ins/setup_venv.sh" "$@"

# Filter out packages provided by the base OS (uv would otherwise try to compile them).
REQ_SRC="/git/agent-zero/requirements.txt"
REQ_DST="/tmp/requirements.filtered.txt"
export REQ_SRC REQ_DST
python <<'PY'
from pathlib import Path
import os

src = Path(os.environ["REQ_SRC"])
dst = Path(os.environ["REQ_DST"])
blocklist = {"asyncpg", "openai-whisper", "kokoro"}

torch_variant = os.environ.get("TORCH_VARIANT", "none").strip().lower()
if torch_variant == "none":
    blocklist.update({
        "torch",
        "torchvision",
        "torchaudio",
        "faster-whisper",
        "accelerate",
        "sentence-transformers",
    })

def canonical(name: str) -> str:
    base = name.split("[")[0]
    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<"):
        if sep in base:
            base = base.split(sep)[0]
            break
    return base.strip().lower()

lines = [line for line in src.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]
filtered: list[str] = []
skipped_kokoro = False
for line in lines:
    name = canonical(line)
    if name in blocklist:
        if name == "kokoro":
            skipped_kokoro = True
        continue
    filtered.append(line)

dst.write_text("\n".join(filtered) + "\n")
if skipped_kokoro:
    print("Skipping kokoro dependency (unsupported on Python 3.13)")
PY

# Install remaining A0 python packages (best-effort to avoid hard failures on optional deps)
set +e
mapfile -t REQUIREMENTS < "${REQ_DST}"
set -e

FAILED_PACKAGES=()
for requirement in "${REQUIREMENTS[@]}"; do
    req_trimmed="${requirement## }"
    if [ -n "${req_trimmed}" ]; then
        if ! pip install --no-cache-dir "${req_trimmed}"; then
            FAILED_PACKAGES+=("${req_trimmed}")
        fi
    fi
done

if [ ${#FAILED_PACKAGES[@]} -gt 0 ]; then
    printf 'WARNING: skipped packages due to install errors: %s\n' "${FAILED_PACKAGES[*]}"
fi

# install playwright
bash /ins/install_playwright.sh "$@"

# Preload A0
python /git/agent-zero/preload.py --dockerized=true
