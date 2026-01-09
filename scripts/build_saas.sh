#!/bin/bash
# =============================================================================
# SOMA Monolith Build Script
# =============================================================================
# Builds the unified SOMA Agent container from all 3 repositories.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
PARENT_DIR="$(dirname "$AGENT_DIR")"

# SOMA SaaS Build Script
# usage: ./build_saas.sh

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color (using NC for consistency with original, though 'd' was in the provided snippet)

echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  SOMA SaaS Agent Builder        ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"

# Check Context (Must be run from root or have access to sibling repos)
# We assume we are in somaAgent01 root
if [ ! -d "infra/saas_deployment" ]; then
    echo "❌ Error: Could not find infra/saas_deployment."
    echo "   Please run this from the somaAgent01 root directory."
    exit 1
fi

# Set Build Context to Parent (..) to allow access to Brain/Memory
# This script assumes the standard folder structure:
# workspace/
#   ├── somaAgent01/
#   ├── somabrain/
#   └── somafractalmemory/

cd ..

if [ ! -d "somabrain" ] || [ ! -d "somafractalmemory" ]; then
    echo "❌ Error: Sibling repositories (somabrain, somafractalmemory) not found."
    echo "   Please ensure you have all 3 repos in the same parent directory."
    exit 1
fi

# Build the SaaS image
echo -e "\n${YELLOW}Building SOMA SaaS image...${NC}"
docker build \
    -f somaAgent01/infra/saas_deployment/Dockerfile \
    -t somatech/soma-saas:latest \
    -t somatech/soma-saas:$(date +%Y%m%d) \
    .

echo -e "\n${GREEN}✅ Build Complete!${NC}"
echo -e "   Image: somatech/soma-saas:latest"
echo -e "   Image: somatech/soma-saas:$(date +%Y%m%d)"

echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Start the SaaS Stack:"
echo -e "     ${GREEN}cd somaAgent01/infra/saas_deployment && docker compose up -d${NC}"
echo -e ""
echo -e "  2. Check health:"
echo -e "     ${GREEN}curl http://localhost:9000/health${NC}"
echo -e ""
echo -e "  3. View logs:"
echo -e "     ${GREEN}docker logs soma-agent${NC}"
