-- infra/postgres/init/10-create-openfga-role.sql
-- Ensure the openfga role exists with the expected password before DB creation/migrations run.

DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'openfga') THEN
     CREATE ROLE openfga WITH LOGIN PASSWORD 'openfga';
   ELSE
     -- If role exists, alter the password to the expected value to ensure migrations can authenticate
     ALTER ROLE openfga WITH PASSWORD 'openfga';
   END IF;
END
$$;

-- Grant minimal privileges; database-specific grants are applied after DB creation.
GRANT CONNECT ON DATABASE postgres TO openfga;
