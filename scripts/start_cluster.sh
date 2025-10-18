#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

# Set up Python path
export PYTHONPATH="${PYTHONPATH}:${PWD}"

echo "Initializing dynamic port assignments..."
python3 scripts/init_ports.py

# Load the generated port assignments
if [ -f .env.ports ]; then
    export $(cat .env.ports | xargs)
else
    echo "Error: Port assignments file not found!"
    exit 1
fi

echo "Starting SomaAgent services with dynamic ports..."
docker compose -f docker-compose.optimized.yaml --profile core up -d

echo "Waiting for services to be healthy..."
sleep 5

echo "Checking service health..."
docker compose -f docker-compose.optimized.yaml ps

echo "Port assignments:"
cat .env.ports