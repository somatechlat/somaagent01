#!/bin/sh
set -e
# Run OpenFGA migrations before starting the server
echo "Running OpenFGA migration..."
openfga migrate \
  --datastore-engine postgres \
  --datastore-uri "${OPENFGA_DATASTORE_URI}" || exit 1

echo "Migration completed. Starting OpenFGA server..."
exec openfga run \
  --grpc-addr "${OPENFGA_GRPC_ADDR}" \
  --http-addr "${OPENFGA_HTTP_ADDR}" \
  --datastore-engine postgres \
  --datastore-uri "${OPENFGA_DATASTORE_URI}" \
  --datastore-max-open-conns "${OPENFGA_DATASTORE_MAX_OPEN_CONNS:-50}" \
  --datastore-max-idle-conns "${OPENFGA_DATASTORE_MAX_IDLE_CONNS:-10}"