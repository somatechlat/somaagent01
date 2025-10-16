#!/bin/bash
set -e

# Feature-based installation script for Agent Zero
# This script installs dependencies based on feature flags

echo "=== Agent Zero Modular Installer ==="

# Source venv setup
. "/ins/setup_venv.sh" "$@"

# Define feature flags with defaults
FEATURE_AI="${FEATURE_AI:-basic}"           # none|basic|cpu|cuda
FEATURE_AUDIO="${FEATURE_AUDIO:-none}"      # none|basic|ml
FEATURE_BROWSER="${FEATURE_BROWSER:-false}" # true|false
FEATURE_DOCUMENTS="${FEATURE_DOCUMENTS:-true}" # true|false
FEATURE_DATABASE="${FEATURE_DATABASE:-true}" # true|false
FEATURE_MONITORING="${FEATURE_MONITORING:-false}" # true|false
FEATURE_DEV="${FEATURE_DEV:-true}"          # true|false
FEATURE_GRPC="${FEATURE_GRPC:-false}"       # true|false
FEATURE_INTEGRATIONS="${FEATURE_INTEGRATIONS:-true}" # true|false

ENABLE_TORCH="${ENABLE_TORCH:-false}"

if [ "$ENABLE_TORCH" != "true" ]; then
    TORCH_VARIANT="none"
    if [ "$FEATURE_AI" = "cpu" ] || [ "$FEATURE_AI" = "cuda" ]; then
        echo "Torch disabled by default; downgrading FEATURE_AI='$FEATURE_AI' to 'basic'."
        FEATURE_AI="basic"
    fi
fi

if [ -n "$TORCH_VARIANT" ] && [ "$TORCH_VARIANT" != "none" ]; then
    if [ "$ENABLE_TORCH" = "true" ]; then
        echo "TORCH_VARIANT='$TORCH_VARIANT' with ENABLE_TORCH=true."
        FEATURE_AI="$TORCH_VARIANT"
    else
        echo "Ignoring TORCH_VARIANT='$TORCH_VARIANT' because ENABLE_TORCH is not true."
        TORCH_VARIANT="none"
    fi
fi

echo "Feature Configuration:"
echo "  AI: $FEATURE_AI"
echo "  Audio: $FEATURE_AUDIO"
echo "  Browser: $FEATURE_BROWSER"
echo "  Documents: $FEATURE_DOCUMENTS"
echo "  Database: $FEATURE_DATABASE"
echo "  Monitoring: $FEATURE_MONITORING"
echo "  Development: $FEATURE_DEV"
echo "  gRPC: $FEATURE_GRPC"
echo "  Integrations: $FEATURE_INTEGRATIONS"

FAILED_PACKAGES=()

# Helper function to install requirements file
install_requirements() {
    local req_file="$1"
    local feature_name="$2"
    
    if [ -f "/git/agent-zero/$req_file" ]; then
        echo "Installing $feature_name dependencies from $req_file..."
        while IFS= read -r requirement; do
            # Skip empty lines and comments
            if [[ -z "$requirement" || "$requirement" =~ ^[[:space:]]*# ]]; then
                continue
            fi
            
            req_trimmed=$(echo "$requirement" | xargs)
            if [ -n "$req_trimmed" ]; then
                echo "  Installing: $req_trimmed"
                if ! pip install --no-cache-dir "$req_trimmed"; then
                    FAILED_PACKAGES+=("$req_trimmed")
                    echo "  WARNING: Failed to install $req_trimmed"
                fi
            fi
        done < "/git/agent-zero/$req_file"
    else
        echo "WARNING: Requirements file not found: $req_file"
    fi
}

# Install core dependencies (always required)
echo "=== Installing Core Dependencies ==="
install_requirements "requirements-core.txt" "Core"

# Install database dependencies
if [ "$FEATURE_DATABASE" = "true" ]; then
    echo "=== Installing Database Dependencies ==="
    install_requirements "requirements-database.txt" "Database"
fi

# Install AI dependencies
if [ "$FEATURE_AI" = "basic" ]; then
    echo "=== Installing AI Dependencies (basic profile) ==="
    install_requirements "requirements-ai-basic.txt" "AI Basic"
elif [ "$FEATURE_AI" = "cpu" ] || [ "$FEATURE_AI" = "cuda" ]; then
    if [ "$ENABLE_TORCH" = "true" ]; then
        echo "Installing torch for AI variant: $FEATURE_AI"
        if [ "$FEATURE_AI" = "cpu" ]; then
            pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch || FAILED_PACKAGES+=("torch-cpu")
        else
            pip install --no-cache-dir torch || FAILED_PACKAGES+=("torch-cuda")
        fi
        install_requirements "requirements-ai-cpu.txt" "AI CPU/CUDA"
    else
        echo "Skipping torch installation: ENABLE_TORCH is not true."
    fi
else
    echo "=== Skipping AI dependencies (FEATURE_AI='$FEATURE_AI') ==="
fi

# Install audio dependencies
if [ "$FEATURE_AUDIO" != "none" ]; then
    echo "=== Installing Audio Dependencies ==="
    install_requirements "requirements-audio-basic.txt" "Audio Basic"
    
    if [ "$FEATURE_AUDIO" = "ml" ]; then
        if [ "$FEATURE_AI" = "cpu" ] || [ "$FEATURE_AI" = "cuda" ]; then
            install_requirements "requirements-audio-ml.txt" "Audio ML"
        else
            echo "WARNING: Audio ML requires AI CPU or CUDA features enabled"
        fi
    fi
fi

# Install document processing dependencies
if [ "$FEATURE_DOCUMENTS" = "true" ]; then
    echo "=== Installing Document Processing Dependencies ==="
    install_requirements "requirements-documents.txt" "Documents"
fi

# Install browser automation dependencies
if [ "$FEATURE_BROWSER" = "true" ]; then
    echo "=== Installing Browser Automation Dependencies ==="
    install_requirements "requirements-browser.txt" "Browser"
fi

# Install development dependencies
if [ "$FEATURE_DEV" = "true" ]; then
    echo "=== Installing Development Dependencies ==="
    install_requirements "requirements-dev.txt" "Development"
fi

# Install monitoring dependencies
if [ "$FEATURE_MONITORING" = "true" ]; then
    echo "=== Installing Monitoring Dependencies ==="
    install_requirements "requirements-monitoring.txt" "Monitoring"
fi

# Install gRPC dependencies
if [ "$FEATURE_GRPC" = "true" ]; then
    echo "=== Installing gRPC Dependencies ==="
    install_requirements "requirements-grpc.txt" "gRPC"
fi

# Install integration dependencies
if [ "$FEATURE_INTEGRATIONS" = "true" ]; then
    echo "=== Installing Integration Dependencies ==="
    install_requirements "requirements-integrations.txt" "Integrations"
fi

# Report any failed packages
if [ ${#FAILED_PACKAGES[@]} -gt 0 ]; then
    echo "=== Installation Summary ==="
    printf 'WARNING: Failed to install the following packages: %s\n' "${FAILED_PACKAGES[*]}"
    echo "The application may still function but some features might be unavailable."
else
    echo "=== Installation Complete ==="
    echo "All dependencies installed successfully!"
fi

# Install playwright browsers if browser feature is enabled
if [ "$FEATURE_BROWSER" = "true" ]; then
    echo "=== Installing Playwright Browsers ==="
    bash /ins/install_playwright.sh "$@"
fi
