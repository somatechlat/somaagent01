-- Create dedicated OpenFGA database and user for production deployments.
DO
$$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles WHERE rolname = 'openfga'
    ) THEN
        CREATE ROLE openfga LOGIN PASSWORD 'openfga';
    END IF;

    IF NOT EXISTS (
        SELECT FROM pg_database WHERE datname = 'openfga'
    ) THEN
        CREATE DATABASE openfga OWNER openfga;
    END IF;
END
$$;

GRANT ALL PRIVILEGES ON DATABASE openfga TO openfga;
