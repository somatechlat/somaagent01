#!/bin/sh
set -e

# This script runs during docker-entrypoint-initdb.d processing and is executed
# outside of a transaction, so CREATE DATABASE is allowed here.

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    SELECT 1 FROM pg_database WHERE datname = 'openfga'\gexec
EOSQL

# The above is a no-op placeholder; rely on conditional create below.
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'openfga') THEN
            PERFORM dblink_exec('dbname=postgres', 'CREATE DATABASE openfga OWNER openfga');
        END IF;
    END
    $$;
EOSQL
