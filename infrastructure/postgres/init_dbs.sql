-- Automate creation of all SOMA Stack databases
-- VIBE Rule: Real Infrastructure & Resilient Startup

CREATE DATABASE somabrain;
CREATE DATABASE somafractalmemory;
CREATE DATABASE somaagent;

-- Grant privileges (optional but good practice if using specific users later)
GRANT ALL PRIVILEGES ON DATABASE somabrain TO postgres;
GRANT ALL PRIVILEGES ON DATABASE somafractalmemory TO postgres;
GRANT ALL PRIVILEGES ON DATABASE somaagent TO postgres;
