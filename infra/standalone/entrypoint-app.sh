#!/bin/sh
# =============================================================================
# Standalone app entrypoint — secret sourcing
# =============================================================================
# WHY THIS EXISTS
# ---------------
# services/gateway/settings.py builds its DATABASES block by parsing
# SA01_DB_DSN, which embeds the password. The password must not live in ENV on
# disk, in .env, or in git — so the DSN is not supplied by the deployer. It is
# composed here, in this container only, from:
#
#   * the mounted Docker secret  /run/secrets/postgres_password
#   * non-secret topology        SA01_DB_USER / HOST / PORT / NAME  (from .env)
#
# The result exists only in this process's environment for the lifetime of the
# process, and is handed to exactly one consumer: Django's DATABASES.
#
# This is a deployment-layer bridge, NOT the final shape. The tracked work item
# is to make services/gateway/settings.py assemble the connection from the
# topology plus secret/agent/credentials/postgres_password, and delete the
# SA01_DB_DSN read entirely. When that lands, delete this script and the
# entrypoint override in docker-compose.yml.
#
# Nothing here prints a secret. Errors name a file, never a value.
# =============================================================================

set -eu

SECRET_FILE="${DB_PASSWORD_FILE:-/run/secrets/postgres_password}"

if [ ! -s "$SECRET_FILE" ]; then
    echo "❌ missing or empty database password secret: $SECRET_FILE" >&2
    echo "   Expected a mounted Docker secret created from" >&2
    echo "   infra/standalone/secrets/postgres_password (see secrets/README.md)." >&2
    echo "   The value is not logged." >&2
    exit 1
fi

: "${SA01_DB_USER:?SA01_DB_USER must be set}"
: "${SA01_DB_HOST:?SA01_DB_HOST must be set}"
: "${SA01_DB_PORT:?SA01_DB_PORT must be set}"
: "${SA01_DB_NAME:?SA01_DB_NAME must be set}"

# Read the secret into a shell variable only for the length of this assignment.
# It is never echoed, and `set -x` is deliberately not enabled.
db_password="$(cat "$SECRET_FILE")"
export SA01_DB_DSN="postgresql://${SA01_DB_USER}:${db_password}@${SA01_DB_HOST}:${SA01_DB_PORT}/${SA01_DB_NAME}"
unset db_password

exec /app/start.sh "$@"
