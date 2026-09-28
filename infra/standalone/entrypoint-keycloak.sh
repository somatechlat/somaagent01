#!/bin/sh
# =============================================================================
# Standalone Keycloak entrypoint — secret sourcing
# =============================================================================
# WHY THIS EXISTS
# ---------------
# Keycloak documents KC_DB_PASSWORD and KEYCLOAK_ADMIN_PASSWORD but ships no
# _FILE variant for either (verified against keycloak.org/server/configuration,
# "Server configuration"). A Java KeyStore is the upstream's file-based option
# and is disproportionate for a local stack.
#
# So the two values are mounted as Docker secrets and exported into this
# container's process environment by this script. They are never in
# docker-compose.yml, never in .env and never in git.
#
# This is a named LOCAL LIMITATION of the third-party image, not a workaround
# we invented to hide a secret. See README.md §"Local limitations".
#
# Nothing here prints a secret. Errors name a file, never a value.
# =============================================================================

set -eu

read_secret() {
    # read_secret <var-name> <file>
    if [ ! -s "$2" ]; then
        echo "❌ missing or empty secret file: $2" >&2
        echo "   See infra/standalone/secrets/README.md. The value is not logged." >&2
        exit 1
    fi
    # Exported directly from the file read; never echoed.
    export "$1=$(cat "$2")"
}

read_secret KC_DB_PASSWORD        /run/secrets/postgres_password
read_secret KEYCLOAK_ADMIN_PASSWORD /run/secrets/keycloak_admin_password

# Upstream image's own start-dev invocation.
exec /opt/keycloak/bin/kc.sh start-dev
