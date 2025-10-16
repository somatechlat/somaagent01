#!/bin/bash
set -e

# ==============================================================================
# Agent Zero Canonical Installation Script
#
# This single script handles all application installation logic for Docker builds,
# combining the functionality of install_A0.sh, install_A02.sh, and
# install_modular.sh.
#
# Usage:
#   bash /ins/install.sh <branch>
#
# Environment Variables:
#   - FEATURE_AI:         AI/ML features (none|basic|cpu|cuda). Default: basic.
#   - FEATURE_AUDIO:      Audio features (none|basic|ml). Default: none.
#   - FEATURE_BROWSER:    Browser automation (true|false). Default: true.
#   - FEATURE_DOCUMENTS:  Document processing (true|false). Default: true.
#   - FEATURE_DATABASE:   Database support (true|false). Default: true.
#   - FEATURE_MONITORING: Monitoring tools (true|false). Default: false.
#   - FEATURE_DEV:        Developer tools (true|false). Default: true.
#   - FEATURE_GRPC:       gRPC support (true|false). Default: false.
#   - FEATURE_INTEGRATIONS: External integrations (true|false). Default: true.
#   - ENABLE_TORCH:       Explicitly enable/disable torch install (true|false). Default: false.
#   - TORCH_VARIANT:      Overrides FEATURE_AI for torch (cpu|cuda|none).
# ==============================================================================

echo "=== Agent Zero Canonical Installer ==="

# --- 1. Setup and Environment Validation ---
BRANCH="${1}"
if [ -z "$BRANCH" ]; then
    echo "ERROR: Branch parameter is required."
    exit 1
fi

# Source venv setup to ensure pip and python are from the correct environment
. "/ins/setup_venv.sh" "$@"

# --- 2. Source Code Setup ---
if [ "$BRANCH" = "local" ]; then
    echo "Using local dev files from context in /git/agent-zero"
    if [ ! -d "/git/agent-zero" ] || [ -z "$(ls -A /git/agent-zero)" ]; then
        echo "ERROR: BRANCH=local but /git/agent-zero is empty or does not exist."
        exit 1
    fi
else
    echo "Cloning repository from branch '$BRANCH'..."
    # Clean up existing repo before cloning (logic from install_A02.sh)
    rm -rf /git/agent-zero
    git clone --depth 1 -b "$BRANCH" "https://github.com/agent0ai/agent-zero" "/git/agent-zero" || {
        echo "CRITICAL ERROR: Failed to clone repository for branch '$BRANCH'."
        exit 1
    }
fi

# --- 3. Dependency Configuration ---
# Define feature flags with defaults
FEATURE_AI="${FEATURE_AI:-basic}"
FEATURE_AUDIO="${FEATURE_AUDIO:-none}"
FEATURE_BROWSER="${FEATURE_BROWSER:-true}"
FEATURE_DOCUMENTS="${FEATURE_DOCUMENTS:-true}"
FEATURE_DATABASE="${FEATURE_DATABASE:-true}"
FEATURE_MONITORING="${FEATURE_MONITORING:-false}"
FEATURE_DEV="${FEATURE_DEV:-true}"
FEATURE_GRPC="${FEATURE_GRPC:-false}"
FEATURE_INTEGRATIONS="${FEATURE_INTEGRATIONS:-true}"
ENABLE_TORCH="${ENABLE_TORCH:-false}"

# Torch installation logic consolidation
if [ "$ENABLE_TORCH" != "true" ]; then
    TORCH_VARIANT="none"
    if [[ "$FEATURE_AI" == "cpu" || "$FEATURE_AI" == "cuda" ]]; then
        echo "INFO: ENABLE_TORCH is false, downgrading FEATURE_AI from '$FEATURE_AI' to 'basic'."
        FEATURE_AI="basic"
    fi
fi

if [ -n "$TORCH_VARIANT" ] && [ "$TORCH_VARIANT" != "none" ]; then
    if [ "$ENABLE_TORCH" = "true" ]; then
        echo "INFO: TORCH_VARIANT='$TORCH_VARIANT' is set, overriding FEATURE_AI for torch installation."
        FEATURE_AI="$TORCH_VARIANT"
    else
        echo "INFO: Ignoring TORCH_VARIANT='$TORCH_VARIANT' because ENABLE_TORCH is not true."
        TORCH_VARIANT="none"
    fi
fi

echo "Feature Configuration:"
echo "  AI: $FEATURE_AI, Audio: $FEATURE_AUDIO, Browser: $FEATURE_BROWSER, Documents: $FEATURE_DOCUMENTS"
echo "  Database: $FEATURE_DATABASE, Monitoring: $FEATURE_MONITORING, Dev: $FEATURE_DEV"
echo "  gRPC: $FEATURE_GRPC, Integrations: $FEATURE_INTEGRATIONS, Torch Enabled: $ENABLE_TORCH"

# --- 4. Modular Dependency Installation ---
FAILED_PACKAGES=()

install_requirements() {
    local req_file="$1"
    local feature_name="$2"
    
    if [ -f "/git/agent-zero/$req_file" ]; then
        echo "Installing $feature_name dependencies from $req_file..."
        # Use uv for faster installation, falling back to pip if it fails.
        if ! uv pip install --no-cache-dir -r "/git/agent-zero/$req_file"; then
            echo "WARNING: 'uv pip install' failed for $req_file. Retrying with pip."
            while IFS= read -r requirement; do
                if [[ -z "$requirement" || "$requirement" =~ ^[[:space:]]*# ]]; then
                    continue
                fi
                req_trimmed=$(echo "$requirement" | xargs)
                if [ -n "$req_trimmed" ]; then
                    echo "  Installing with pip: $req_trimmed"
                    if ! pip install --no-cache-dir "$req_trimmed"; then
                        FAILED_PACKAGES+=("$req_trimmed")
                        echo "  ERROR: Failed to install $req_trimmed"
                    fi
                fi
            done < "/git/agent-zero/$req_file"
        fi
    else
        echo "WARNING: Requirements file not found: $req_file"
    fi
}

# Install dependencies based on features
install_requirements "requirements-core.txt" "Core"
[ "$FEATURE_DATABASE" = "true" ] && install_requirements "requirements-database.txt" "Database"
[ "$FEATURE_DOCUMENTS" = "true" ] && install_requirements "requirements-documents.txt" "Documents"
[ "$FEATURE_BROWSER" = "true" ] && install_requirements "requirements-browser.txt" "Browser"
[ "$FEATURE_DEV" = "true" ] && install_requirements "requirements-dev.txt" "Development"
[ "$FEATURE_MONITORING" = "true" ] && install_requirements "requirements-monitoring.txt" "Monitoring"
[ "$FEATURE_GRPC" = "true" ] && install_requirements "requirements-grpc.txt" "gRPC"
[ "$FEATURE_INTEGRATIONS" = "true" ] && install_requirements "requirements-integrations.txt" "Integrations"

# AI & Audio dependencies (torch-sensitive)
if [ "$FEATURE_AI" = "basic" ]; then
    install_requirements "requirements-ai-basic.txt" "AI Basic"
elif [[ "$FEATURE_AI" == "cpu" || "$FEATURE_AI" == "cuda" ]]; then
    echo "Installing torch for AI variant: $FEATURE_AI"
    if [ "$FEATURE_AI" = "cpu" ]; then
        pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch || FAILED_PACKAGES+=("torch-cpu")
    else
        pip install --no-cache-dir torch || FAILED_PACKAGES+=("torch-cuda")
    fi
    install_requirements "requirements-ai-cpu.txt" "AI CPU/CUDA"
else
    echo "Skipping AI dependencies (FEATURE_AI='$FEATURE_AI')"
fi

if [ "$FEATURE_AUDIO" != "none" ]; then
    install_requirements "requirements-audio-basic.txt" "Audio Basic"
    if [ "$FEATURE_AUDIO" = "ml" ]; then
        if [[ "$FEATURE_AI" == "cpu" || "$FEATURE_AI" == "cuda" ]]; then
            install_requirements "requirements-audio-ml.txt" "Audio ML"
        else
            echo "WARNING: Audio ML requires AI CPU or CUDA features to be enabled, but FEATURE_AI is '$FEATURE_AI'. Skipping."
        fi
    fi
fi

# --- 5. Post-installation Steps ---
if [ "$FEATURE_BROWSER" = "true" ]; then
    echo "Installing Playwright browsers..."
    bash /ins/install_playwright.sh "$@"
fi

echo "Running application preload..."
python /git/agent-zero/preload.py --dockerized=true

# --- 6. Finalization and Cleanup ---
echo "Cleaning up package caches..."
pip cache purge
uv cache prune

if [ ${#FAILED_PACKAGES[@]} -gt 0 ]; then
    echo "---"
    echo "WARNING: Installation completed with errors. The following packages failed to install:"
    printf ' - %s\n' "${FAILED_PACKAGES[@]}"
    echo "The application may not function correctly."
    echo "---"
    # Optionally, exit with an error code
    # exit 1
else
    echo "=== Installation Complete ==="
    echo "All dependencies installed successfully!"
fi
