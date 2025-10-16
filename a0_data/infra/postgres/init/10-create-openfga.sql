-- Create dedicated OpenFGA role (idempotent).
-- Note: CREATE DATABASE cannot be executed inside a DO block / function
-- because it's not allowed within a transaction. Database creation is
-- handled in a separate shell script (11-create-openfga-db.sh) so it
-- runs outside a transaction and can succeed during container init.
DO
$$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = 'openfga'
    ) THEN
        CREATE ROLE openfga LOGIN PASSWORD 'openfga';
    ELSE
        EXECUTE 'ALTER ROLE openfga WITH LOGIN PASSWORD ''openfga''';
    END IF;
END
$$;
