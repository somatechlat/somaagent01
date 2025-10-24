#!/usr/bin/env bash
set -euo pipefail

# Generate a local development root CA using openssl.
# Outputs CA key and cert under scripts/dev-ca/ca/.
# Usage: ./scripts/dev-ca/generate-dev-ca.sh [CN]

CN=${1:-"Soma Dev Local CA"}
OUT_DIR="$(cd "$(dirname "$0")" && pwd)/ca"
mkdir -p "$OUT_DIR"
KEY="$OUT_DIR/dev-ca.key.pem"
CERT="$OUT_DIR/dev-ca.crt.pem"

if [[ -f "$KEY" || -f "$CERT" ]]; then
  echo "CA files already exist in $OUT_DIR; refusing to overwrite."
  echo "Delete the directory or move the files if you want to regenerate."
  exit 1
fi

openssl req -x509 -new -nodes -sha256 -days 3650 \
  -newkey rsa:4096 \
  -subj "/C=US/ST=Local/L=Local/O=Soma/OU=Dev/CN=$CN" \
  -keyout "$KEY" \
  -out "$CERT"

# Print resulting files
ls -l "$OUT_DIR"

echo "\nDev CA generated:"
echo "  Key:  $KEY"
echo "  Cert: $CERT"
