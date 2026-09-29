#!/bin/bash
# =============================================================================
# MULTI-DATABASE + TEST-ROLE INITIALIZATION
# =============================================================================
# Mounted to /docker-entrypoint-initdb.d/ in the PostgreSQL container.
# Runs exactly once, on an empty data directory.
#
# Creates the per-service databases and the least-privileged application/test
# role. The test role is a ROLE, not a superuser: config/settings.py connects
# as it (TEST_DB_USER) using the Vault secret test_db_password, which is a
# different credential from the cluster superuser's postgres_password. Least
# privilege, two distinct secrets — not one password reused everywhere.
#
# VIBE Rule 164: the password is read from a mounted secret file. It is never
# passed as an argument (argv is world-readable via ps) and never interpolated
# from an environment variable.
# =============================================================================

set -e
set -u

function create_database() {
    local database=$1
    echo "Creating database: $database"
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
        CREATE DATABASE $database;
        GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

# Create databases for each service
if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
    echo "Creating multiple databases: $POSTGRES_MULTIPLE_DATABASES"
    for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
        create_database $db
    done
    echo "Multiple databases created successfully"
fi

# ---------------------------------------------------------------------------
# Least-privileged test/application role. Password from a mounted secret file.
# ---------------------------------------------------------------------------
TEST_DB_USER="${TEST_DB_USER:-somaagent}"
TEST_DB_PASSWORD_FILE="${TEST_DB_PASSWORD_FILE:-/run/secrets/test_db_password}"

if [ ! -f "$TEST_DB_PASSWORD_FILE" ]; then
    echo "FATAL: $TEST_DB_PASSWORD_FILE is missing."
    echo "The test role password is a credential and arrives as a mounted"
    echo "Docker secret (VIBE Rule 164). It is never generated and never read"
    echo "from ENV. Refusing to create a role with a password nobody can use."
    exit 1
fi

# Read without echoing. tr strips the trailing newline the bootstrap file has;
# postgres treats the newline as part of the password and auth then fails.
TEST_DB_PASSWORD="$(tr -d '\n' < "$TEST_DB_PASSWORD_FILE")"
if [ -z "$TEST_DB_PASSWORD" ]; then
    echo "FATAL: $TEST_DB_PASSWORD_FILE is empty. Refusing to create a role with an empty password."
    exit 1
fi

echo "Creating least-privileged role: $TEST_DB_USER"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "somaagent" \
    -c "CREATE ROLE \"${TEST_DB_USER}\" LOGIN PASSWORD '${TEST_DB_PASSWORD}';"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "somaagent" \
    -c "GRANT ALL PRIVILEGES ON DATABASE somaagent TO \"${TEST_DB_USER}\";"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "somaagent" \
    -c "GRANT ALL ON SCHEMA public TO \"${TEST_DB_USER}\";"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "somaagent" \
    -c "ALTER DATABASE somaagent OWNER TO \"${TEST_DB_USER}\";"

echo "Test role created."
