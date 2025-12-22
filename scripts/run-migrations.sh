#!/usr/bin/env bash
# run-migrations.sh - Run Alembic database migrations
#
# This script runs Alembic migrations with proper error handling.
# It is designed to be called from Docker entrypoint or manually.
#
# Environment Variables:
#   SA01_DB_DSN - PostgreSQL connection string (required)
#
# Exit Codes:
#   0 - Success
#   1 - Missing SA01_DB_DSN
#   2 - Migration failed

set -euo pipefail

# Color output for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check for required environment variable
if [[ -z "${SA01_DB_DSN:-}" ]]; then
    log_error "SA01_DB_DSN environment variable is not set"
    log_error "Example: SA01_DB_DSN=postgresql://user:pass@host:port/dbname"
    exit 1
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

log_info "Running Alembic migrations..."
log_info "Project root: ${PROJECT_ROOT}"

# Change to project root for alembic to find alembic.ini
pushd "${PROJECT_ROOT}" > /dev/null

# Run migrations
if alembic upgrade head; then
    log_info "Migrations completed successfully"
    popd > /dev/null
    exit 0
else
    log_error "Migration failed!"
    popd > /dev/null
    exit 2
fi
