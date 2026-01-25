#!/bin/bash
# =============================================================================
# SOMA Monolith Build Script
# =============================================================================
# Builds the unified SOMA Agent container from all 3 repositories.
# =============================================================================

set -e

# Check Context & Navigate to Workspace Root
# Script is located in: somaAgent01/infra/aaas_deployment/build_aaas.sh
# We need to get to:   workspace/ (Parent of somaAgent01, somabrain, somafractalmemory)

# 1. Go to somaAgent01 root (Up 2 levels)
cd "$(dirname "$0")/../.."

# 2. Go to WORKSPACE root (Up 1 level)
cd ..

WORKSPACE_ROOT=$(pwd)
echo "📂 Workspace Root: $WORKSPACE_ROOT"

if [ ! -d "somabrain" ] || [ ! -d "somafractalmemory" ]; then
    echo "❌ Error: Sibling repositories (somabrain, somafractalmemory) not found."
    echo "   Please ensure you have all 3 repos in the same parent directory."
    exit 1
fi

# Build the AAAS image using Optimized Context (Tar Pipe)
# --------------------------------------------------------
# PROBLEM: Running `docker build -f ... .` from the parent sends the ENTIRE workspace context (3.5GB+)
#          including .venv, node_modules, and target directories of ALL repos.
# SOLUTION: We use `tar` to stream ONLY the necessary source code, filtering out junk on the fly.
# --------------------------------------------------------

echo -e "\n${YELLOW}Creating Optimized Build Context (Filtering .venv, node_modules, target...)${NC}"

# Define Excludes (Aggressive Optimization)
# Excluding: Git, Venv, Node Modules, Rust Target, PyCache, Logs, DS_Store
#            Docs, Tests, Examples, Github Constraints, VSCode, Markdown, Makefiles
EXCLUDES="--exclude=.git --exclude=.venv --exclude=node_modules --exclude=target --exclude=__pycache__ --exclude=*.log --exclude=.DS_Store \
          --exclude=docs --exclude=tests --exclude=examples --exclude=.github --exclude=.vscode \
          --exclude=*.md --exclude=LICENSE --exclude=Makefile --exclude=Tiltfile --exclude=*.toml"

# Note: We excluded *.toml but we need pyproject.toml for Brain.
# Strategy: We can't exclude *.toml globally if we need specific ones.
# Let's refine: Keep Cargo.toml and pyproject.toml, exclude others if any?
# Actually, tar excludes are strict. If I exclude *.toml, I lose pyproject.toml.
# Better to exclude specific folders and extensions that are clearly waste.
EXCLUDES="--exclude=.git --exclude=.venv --exclude=node_modules --exclude=target --exclude=__pycache__ --exclude=*.log --exclude=.DS_Store \
          --exclude=docs --exclude=tests --exclude=examples --exclude=.github --exclude=.vscode \
          --exclude=*.md --exclude=LICENSE --exclude=Makefile --exclude=Tiltfile"

# Stream context to Docker
# We are in WORKSPACE_ROOT
# We select the 3 repos explicitly to avoid sending other workspace junk
tar -czh $EXCLUDES somaAgent01 somabrain somafractalmemory | docker build \
    -f somaAgent01/infra/aaas/Dockerfile \
    -t somatech/soma-aaas:latest \
    -t somatech/soma-aaas:$(date +%Y%m%d) \
    -

echo -e "\n${GREEN}✅ Build Complete!${NC}"
echo -e "   Image: somatech/soma-aaas:latest"
echo -e "   Image: somatech/soma-aaas:$(date +%Y%m%d)"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Start the AAAS Stack:"
echo -e "     ${GREEN}cd somaAgent01/infra/aaas_deployment && docker compose up -d${NC}"
echo -e ""
echo -e "  2. Check health:"
echo -e "     ${GREEN}curl http://localhost:9000/health${NC}"
echo -e ""
echo -e "  3. View logs:"
echo -e "     ${GREEN}docker logs soma-agent${NC}"
