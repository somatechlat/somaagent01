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

# Filter out heavy GPU/torch-related packages when torch is disabled
REQ_SRC="/git/agent-zero/requirements.txt"
REQ_DST="/tmp/requirements.filtered.txt"
export REQ_SRC REQ_DST
python <<'PY'
from pathlib import Path
import os

src = Path(os.environ["REQ_SRC"])  # /git/agent-zero/requirements.txt
dst = Path(os.environ["REQ_DST"])  # /tmp/requirements.filtered.txt

enable_torch = os.environ.get("ENABLE_TORCH", "false").strip().lower() == "true"
torch_variant = os.environ.get("TORCH_VARIANT", "none").strip().lower()

blocklist = {"openai-whisper", "kokoro"}
if not enable_torch or torch_variant == "none":
    blocklist.update({
        "torch",
        "torchvision",
        "torchaudio",
        "faster-whisper",
        "accelerate",
        "sentence-transformers",
    })

def canonical(line: str) -> str:
    base = line.split("[")[0]
    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<"):
        if sep in base:
            base = base.split(sep)[0]
            break
    return base.strip().lower()

filtered = []
for raw in src.read_text().splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    name = canonical(line)
    if name in blocklist:
        continue
    filtered.append(line)

dst.write_text("\n".join(filtered) + "\n")
PY

# moved to base image
# # Ensure the virtual environment and pip setup
# pip install --upgrade pip ipython requests
# # Install some packages in specific variants
# pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining A0 python packages (filtered)
uv pip install -r /tmp/requirements.filtered.txt

# install playwright
bash /ins/install_playwright.sh "$@"

# Preload A0
python /git/agent-zero/preload.py --dockerized=true
