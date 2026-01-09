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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  SOMA Monolith Agent Builder        ${NC}"
echo -e "${GREEN}======================================${NC}"

# -----------------------------------------------------------------------------
# Prerequisites check
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

check_repo() {
    if [ ! -d "$1" ]; then
        echo -e "${RED}ERROR: Repository not found: $1${NC}"
        exit 1
    fi
    echo -e "  ✅ Found: $1"
}

check_repo "$PARENT_DIR/somaAgent01"
check_repo "$PARENT_DIR/somabrain"
check_repo "$PARENT_DIR/somafractalmemory"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker not found${NC}"
    exit 1
fi
echo -e "  ✅ Docker available"

# -----------------------------------------------------------------------------
# Build the monolith image
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}Building SOMA Monolith image...${NC}"

cd "$PARENT_DIR"

docker build \
    -f somaAgent01/Dockerfile.monolith \
    -t somatech/soma-monolith:latest \
    -t somatech/soma-monolith:$(date +%Y%m%d) \
    .

echo -e "\n${GREEN}✅ Build complete!${NC}"
echo -e "   Image: somatech/soma-monolith:latest"

# -----------------------------------------------------------------------------
# Print next steps
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "  1. Start the monolith:"
echo -e "     ${GREEN}cd somaAgent01 && docker compose -f docker-compose.monolith.yml up -d${NC}"
echo -e ""
echo -e "  2. Check health:"
echo -e "     ${GREEN}curl http://localhost:9000/health${NC}"
echo -e ""
echo -e "  3. View logs:"
echo -e "     ${GREEN}docker logs soma-agent${NC}"
