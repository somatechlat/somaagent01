#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}⚠️  INITIATING RESILIENT INFRASTRUCTURE RESET ⚠️${NC}"
echo "This will destroy all local data in volumes and restart from zero."
sleep 3

# 1. Tear down everything
echo -e "${BLUE}Creation Phase 1: Destruction${NC}"
docker compose down -v
docker compose rm -f

# 2. Start Database Layer
echo -e "${BLUE}Creation Phase 2: Data Layer${NC}"
docker compose up -d postgres
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose exec postgres pg_isready -U postgres; do
  echo "Sleeping 2s..."
  sleep 2
done

# 3. SpiceDB Migration (The Critical Step)
echo -e "${BLUE}Creation Phase 3: Schema Migration${NC}"
echo "Running SpiceDB migration..."
docker compose run --rm --entrypoint spicedb spicedb migrate head

# 4. Launch Full Stack
echo -e "${BLUE}Creation Phase 4: Full Launch${NC}"
docker compose up -d

echo -e "${GREEN}✅ RESET COMPLETE. Infrastructure is fresh and hydrated.${NC}"
echo "Verify status with: docker compose ps"
