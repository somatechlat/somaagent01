-- Create the openfga database if it doesn't exist. This SQL file is
-- executed by the Docker entrypoint outside of a transaction, so
-- CREATE DATABASE is allowed here.

SELECT 'CREATE DATABASE openfga OWNER openfga'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'openfga')\gexec

-- Ensure privileges
GRANT ALL PRIVILEGES ON DATABASE openfga TO openfga;
